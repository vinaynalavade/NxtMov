import re
import secrets
import threading
import time
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.tenant import get_current_user, TenantContext
from app.core.rate_limiter import check_login_rate_limit, reset_login_rate_limit, check_register_rate_limit
from app.services.sms_service import get_sms_provider, normalize_phone_number, otp_rate_limiter
from app.services.email_service import get_email_provider, generate_verification_url
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership, OrgType, OrgRole
from app.models.candidate import Candidate, CandidateStatus
from app.models.student_profile import StudentProfile
from app.schemas.user import (
    UserCreate, UserResponse, Token,
    EmailVerifyRequest, EmailVerifyConfirm,
    PhoneOTPRequest, PhoneOTPConfirm,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.schemas.organization import OrganizationResponse, WorkspaceSwitchRequest

router = APIRouter()
_demo_lock = threading.Lock()

def ensure_demo_user_exists(db: Session):
    """
    Idempotently and reliably provisions the demo user, workspace organization,
    organization membership, candidate record, and student profile.
    Guarantees deterministic login under demo mode across restarts and deployments.
    """
    if not settings.NXTMOV_DEMO_MODE:
        return

    with _demo_lock:
        try:
            demo_email = settings.DEMO_USER_EMAIL.strip().lower()
            user = db.query(User).filter(User.email == demo_email).first()
            hashed_pwd = get_password_hash(settings.DEMO_USER_PASSWORD)

            if not user:
                user = User(
                    email=demo_email,
                    hashed_password=hashed_pwd,
                    full_name="Demo User",
                    phone="+91 99999 00000",
                    is_active=True,
                    is_email_verified=True,
                    is_phone_verified=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                # Ensure password hash is valid, active, and verified
                needs_commit = False
                if not verify_password(settings.DEMO_USER_PASSWORD, user.hashed_password) or not user.is_active:
                    user.hashed_password = hashed_pwd
                    user.is_active = True
                    needs_commit = True
                if not user.is_email_verified or not user.is_phone_verified:
                    user.is_email_verified = True
                    user.is_phone_verified = True
                    needs_commit = True
                if needs_commit:
                    db.commit()
                    db.refresh(user)

            # Check or create demo organizations and memberships for all canonical roles
            demo_roles = [
                ("demo-workspace", "Demo Workspace", OrgType.CONSULTANCY, OrgRole.ADMIN),
                ("demo-student-hub", "Student Career Hub", OrgType.INDIVIDUAL, OrgRole.STUDENT),
                ("demo-mentor-workspace", "Student Mentorship Desk", OrgType.CONSULTANCY, OrgRole.MENTOR),
                ("demo-recruiter-workspace", "Talent Sourcing & Recruitment", OrgType.CONSULTANCY, OrgRole.RECRUITER),
            ]

            for slug, name, otype, o_role in demo_roles:
                d_org = db.query(Organization).filter(Organization.slug == slug).first()
                if not d_org:
                    d_org = Organization(
                        name=name,
                        slug=slug,
                        type=otype,
                        owner_id=user.id
                    )
                    db.add(d_org)
                    db.commit()
                    db.refresh(d_org)

                d_mem = db.query(OrganizationMembership).filter(
                    OrganizationMembership.user_id == user.id,
                    OrganizationMembership.organization_id == d_org.id
                ).first()
                if not d_mem:
                    d_mem = OrganizationMembership(
                        user_id=user.id,
                        organization_id=d_org.id,
                        role=o_role
                    )
                    db.add(d_mem)
                    db.commit()
                elif d_mem.role != o_role:
                    d_mem.role = o_role
                    db.commit()

                # Check or create linked candidate
                d_cand = db.query(Candidate).filter(
                    Candidate.organization_id == d_org.id,
                    Candidate.email == user.email
                ).first()
                if not d_cand:
                    d_cand = Candidate(
                        organization_id=d_org.id,
                        user_id=user.id,
                        full_name=user.full_name,
                        email=user.email,
                        phone=user.phone,
                        status=CandidateStatus.NEW
                    )
                    db.add(d_cand)
                    db.commit()
                    db.refresh(d_cand)

                # Check or create student profile
                d_prof = db.query(StudentProfile).filter(
                    StudentProfile.organization_id == d_org.id,
                    StudentProfile.user_id == user.id
                ).first()
                if not d_prof:
                    d_prof = StudentProfile(
                        organization_id=d_org.id,
                        user_id=user.id,
                        candidate_id=d_cand.id,
                        headline="Full Stack Software Engineer",
                        completeness_score=85
                    )
                    db.add(d_prof)
                    db.commit()
        except Exception as e:
            db.rollback()

from app.schemas.user import (
    UserCreate, UserResponse, Token, ActiveOrgInfo, UserRoleInfo,
    EmailVerifyRequest, EmailVerifyConfirm,
    PhoneOTPRequest, PhoneOTPConfirm,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.schemas.organization import OrganizationResponse, WorkspaceSwitchRequest

def make_user_response(
    user: User,
    db: Session,
    active_org_id: Optional[int] = None,
    active_role: Optional[str] = None
) -> UserResponse:
    from app.core.permissions import get_role_permissions

    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user.id)
        .all()
    )

    roles_list = []
    active_org_info = None
    resolved_permissions = []
    active_role_str = "STUDENT"

    for m in memberships:
        r_str = m.role.value if hasattr(m.role, "value") else str(m.role)
        if r_str.upper() == "CANDIDATE":
            r_str = "STUDENT"
        org_name = m.organization.name if m.organization else "Workspace"
        roles_list.append(UserRoleInfo(
            organization_id=m.organization_id,
            role=r_str,
            organization_name=org_name
        ))

        # Check if this membership matches the requested active_org_id or active_role
        is_org_match = active_org_id is not None and int(m.organization_id) == int(active_org_id)
        is_role_match = active_role is not None and r_str.upper() == active_role.upper()

        if is_org_match or (active_org_info is None and is_role_match):
            active_role_str = r_str
            active_org_info = ActiveOrgInfo(
                id=m.organization_id,
                name=org_name,
                role=r_str
            )
            resolved_permissions = get_role_permissions(r_str, is_superuser=user.is_superuser)

    # If active_role is requested (e.g. ADMIN) and user is superuser, resolve ADMIN context
    if active_role and active_role.upper() == "ADMIN" and user.is_superuser and not active_org_info:
        active_role_str = "ADMIN"
        first_org = memberships[0] if memberships else None
        active_org_info = ActiveOrgInfo(
            id=first_org.organization_id if first_org else 0,
            name=first_org.organization.name if (first_org and first_org.organization) else "Admin Workspace",
            role="ADMIN"
        )
        resolved_permissions = get_role_permissions("ADMIN", is_superuser=True)

    # Fallback to first membership ONLY IF active_org_info is still None and no active_role was requested
    if not active_org_info and memberships and not active_role:
        first_m = memberships[0]
        first_r = first_m.role.value if hasattr(first_m.role, "value") else str(first_m.role)
        if first_r.upper() == "CANDIDATE":
            first_r = "STUDENT"
        active_role_str = first_r
        active_org_info = ActiveOrgInfo(
            id=first_m.organization_id,
            name=first_m.organization.name if first_m.organization else "Workspace",
            role=first_r
        )
        resolved_permissions = get_role_permissions(first_r, is_superuser=user.is_superuser)

    if not active_org_info:
        resolved_permissions = get_role_permissions(active_role or "STUDENT", is_superuser=user.is_superuser)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        is_phone_verified=user.is_phone_verified,
        is_superuser=user.is_superuser,
        avatar_url=user.avatar_url,
        headline=user.headline,
        location=user.location,
        active_organization=active_org_info,
        roles=roles_list,
        permissions=resolved_permissions
    )

@router.get("/config", summary="Get Public Authentication Configuration")
def get_auth_config(db: Session = Depends(get_db)):
    if settings.NXTMOV_DEMO_MODE:
        ensure_demo_user_exists(db)

    return {
        "demo_mode": settings.NXTMOV_DEMO_MODE,
        "demo_email": settings.DEMO_USER_EMAIL if settings.NXTMOV_DEMO_MODE else None,
        "demo_password": settings.DEMO_USER_PASSWORD if settings.NXTMOV_DEMO_MODE else None,
        "supported_methods": ["password"],
        "rate_limiting_enabled": True
    }

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, summary="User Self-Registration")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. Rate limiting
    check_register_rate_limit(request)

    # 2. Validation
    name_clean = user_in.full_name.strip()
    if not name_clean or len(name_clean) < 2 or any(ch.isdigit() for ch in name_clean) or "@" in name_clean or "http://" in name_clean or "https://" in name_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid full name."
        )

    email_clean = user_in.email.strip().lower()
    if email_clean != "demo@nxtmov.local" and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid email address."
        )

    if len(user_in.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet the required security requirements."
        )

    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # 3. Create User
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=email_clean,
        hashed_password=hashed_password,
        full_name=name_clean,
        phone=user_in.phone.strip() if user_in.phone else None,
        is_email_verified=False,
        is_phone_verified=False
    )
    db.add(user)
    db.flush()

    # 4. Create Default Individual Workspace
    org_slug = f"workspace-{user.id}-{re.sub(r'[^a-z0-9]', '', email_clean.split('@')[0])[:12]}"
    personal_org = Organization(
        name=f"{user.full_name}'s Workspace",
        slug=org_slug,
        type=OrgType.INDIVIDUAL,
        owner_id=user.id
    )
    db.add(personal_org)
    db.flush()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=personal_org.id,
        role=OrgRole.ADMIN
    )
    db.add(membership)

    cand = Candidate(
        organization_id=personal_org.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        status=CandidateStatus.NEW
    )
    db.add(cand)
    db.flush()

    profile = StudentProfile(
        organization_id=personal_org.id,
        user_id=user.id,
        candidate_id=cand.id,
        completeness_score=30
    )
    db.add(profile)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=user.id, org_id=personal_org.id, role=OrgRole.ADMIN.value)

    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=personal_org.id,
        user=make_user_response(user, db, active_org_id=personal_org.id, active_role="ADMIN")
    )

@router.post("/login", response_model=Token, summary="User Login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    requested_role: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    username_clean = form_data.username.strip().lower()

    check_login_rate_limit(request, username_clean)

    if settings.NXTMOV_DEMO_MODE and username_clean == settings.DEMO_USER_EMAIL.lower():
        ensure_demo_user_exists(db)

    user = db.query(User).filter(User.email == username_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account."
        )

    # Read requested_role from query parameter, header, or form body
    if not requested_role:
        requested_role = request.headers.get("X-Requested-Role")
    if not requested_role:
        try:
            form = await request.form()
            requested_role = form.get("requested_role")
        except Exception:
            pass

    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user.id)
        .all()
    )

    if not memberships:
        org = Organization(
            name=f"{user.full_name}'s Workspace",
            slug=f"workspace-{user.id}",
            type=OrgType.INDIVIDUAL,
            owner_id=user.id
        )
        db.add(org)
        db.flush()
        default_role = OrgRole.STUDENT if requested_role and requested_role.strip().upper() == "STUDENT" else OrgRole.ADMIN
        m = OrganizationMembership(
            user_id=user.id,
            organization_id=org.id,
            role=default_role
        )
        db.add(m)
        db.commit()
        memberships = [m]

    target_membership = None

    if requested_role:
        req_clean = requested_role.strip().upper()
        if req_clean == "CANDIDATE":
            req_clean = "STUDENT"

        ROLE_DISPLAY_NAMES = {
            "ADMIN": "Administrator",
            "MENTOR": "Mentor",
            "RECRUITER": "Recruiter",
            "STUDENT": "Student",
            "COUNSELOR": "Counselor"
        }
        role_title = ROLE_DISPLAY_NAMES.get(req_clean, req_clean.title())

        # Match against user's actual memberships
        for m in memberships:
            m_role_str = m.role.value if hasattr(m.role, "value") else str(m.role).upper()
            if m_role_str == "CANDIDATE":
                m_role_str = "STUDENT"
            if m_role_str == req_clean:
                target_membership = m
                break

        # Superuser privilege allows ADMIN role access
        if not target_membership and req_clean == "ADMIN" and user.is_superuser and memberships:
            target_membership = memberships[0]

        if not target_membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This account does not have {role_title} access."
            )
    else:
        target_membership = memberships[0]

    reset_login_rate_limit(request, username_clean)

    role_val = target_membership.role.value if hasattr(target_membership.role, "value") else str(target_membership.role)
    if role_val.upper() == "CANDIDATE":
        role_val = "STUDENT"

    access_token = create_access_token(
        subject=user.id,
        org_id=target_membership.organization_id,
        role=role_val
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=target_membership.organization_id,
        user=make_user_response(
            user,
            db,
            active_org_id=target_membership.organization_id,
            active_role=role_val
        )
    )

@router.get("/me", summary="Get Current User Profile & Workspaces")
def get_me(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user.id)
        .all()
    )
    org_list = []
    active_org_id = None
    token_role = None

    # Try getting active org and role from token header if present
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        from app.core.security import decode_access_token
        payload = decode_access_token(auth_header[7:].strip())
        if payload:
            raw_org = payload.get("org_id")
            if raw_org is not None:
                try:
                    active_org_id = int(raw_org)
                except (ValueError, TypeError):
                    active_org_id = None
            token_role = payload.get("role")

    for m in memberships:
        if not m.organization:
            continue
        org_resp = OrganizationResponse.model_validate(m.organization)
        role_str = m.role.value if hasattr(m.role, "value") else str(m.role)
        if role_str.upper() == "CANDIDATE":
            role_str = "STUDENT"
        org_dict = org_resp.model_dump()
        org_dict["role"] = role_str
        org_list.append(org_dict)

    if not active_org_id and token_role:
        for m in memberships:
            m_r = m.role.value if hasattr(m.role, "value") else str(m.role).upper()
            if m_r == "CANDIDATE":
                m_r = "STUDENT"
            if m_r == token_role.upper():
                active_org_id = m.organization_id
                break

    if not active_org_id and memberships:
        active_org_id = memberships[0].organization_id

    return {
        "user": make_user_response(user, db, active_org_id=active_org_id, active_role=token_role),
        "organizations": org_list
    }

@router.post("/switch", response_model=Token, summary="Switch Active Workspace Context")
def switch_workspace(
    req: Optional[WorkspaceSwitchRequest] = None,
    organization_id: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_org_id = organization_id or (req.organization_id if req else None)
    if not target_org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="organization_id must be provided.")

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == target_org_id
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace organization."
        )

    access_token = create_access_token(subject=user.id, org_id=membership.organization_id, role=membership.role.value)

    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=membership.organization_id,
        user=make_user_response(user, db, active_org_id=membership.organization_id)
    )

# ==============================================================================
# EMAIL & MOBILE VERIFICATION ENDPOINTS
# ==============================================================================

@router.post("/verify-email/request", summary="Request Email Verification Token")
def request_email_verification(
    request: Request,
    req: Optional[EmailVerifyRequest] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.is_email_verified:
        return {"message": "Email address is already verified.", "is_verified": True}

    target_email = (req.email.strip().lower() if req and req.email else user.email).strip().lower()
    token = secrets.token_urlsafe(32)
    user.email_verification_token = f"{token}:{int(time.time())}"
    db.commit()

    origin = request.headers.get("origin") or request.headers.get("referer")
    verification_link = generate_verification_url(token, origin)

    email_provider = get_email_provider()
    result = email_provider.send_verification_email(
        to_email=target_email,
        user_name=user.full_name or "User",
        verification_link=verification_link
    )

    if not result.success:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.message
        )

    return {
        "message": result.message,
        "is_verified": False,
        "verification_link": verification_link if settings.NXTMOV_DEMO_MODE else None
    }

def _process_email_verification(token_str: str, db: Session):
    token_clean = token_str.strip()
    if not token_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has already been used."
        )

    user = None
    all_pending = db.query(User).filter(User.email_verification_token.isnot(None)).all()
    for u in all_pending:
        stored = u.email_verification_token or ""
        if stored == token_clean or stored.startswith(f"{token_clean}:"):
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has already been used."
        )

    # Check 24-hour expiration window (86400 seconds)
    stored_token = user.email_verification_token or ""
    if ":" in stored_token:
        try:
            _, ts_str = stored_token.rsplit(":", 1)
            ts = float(ts_str)
            if time.time() - ts > 86400:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This verification link has expired. Please request a new one."
                )
        except (ValueError, TypeError):
            pass

    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()

    return {"message": "Email verified successfully.", "is_verified": True}

@router.get("/verify-email", summary="Confirm Email Verification via Direct Link")
def confirm_email_verification_get(
    token: str = Query(..., description="Email verification token"),
    db: Session = Depends(get_db)
):
    return _process_email_verification(token, db)

@router.post("/verify-email/confirm", summary="Confirm Email Verification Token")
def confirm_email_verification(
    data: EmailVerifyConfirm,
    db: Session = Depends(get_db)
):
    return _process_email_verification(data.token, db)

@router.post("/verify-phone/request-otp", summary="Request Phone OTP Verification")
def request_phone_otp(
    data: PhoneOTPRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        clean_phone = normalize_phone_number(data.phone, settings.DEFAULT_PHONE_COUNTRY_CODE)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Rate limiting: minimum cooldown and maximum requests per window
    rate_key = f"otp:{user.id}:{clean_phone}"
    is_allowed, rate_msg = otp_rate_limiter.check_rate_limit(rate_key)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=rate_msg
        )

    otp = str(secrets.randbelow(900000) + 100000)
    user.phone = clean_phone
    user.phone_otp = f"{otp}:{int(time.time())}"
    db.commit()

    sms_provider = get_sms_provider()
    result = sms_provider.send_otp(clean_phone, otp)

    if not result.success:
        raise HTTPException(
            status_code=result.status_code,
            detail=result.message
        )

    return {
        "message": result.message,
        "is_verified": False,
        "dev_otp": otp if settings.NXTMOV_DEMO_MODE else None
    }

@router.post("/verify-phone/confirm-otp", summary="Confirm Phone OTP")
def confirm_phone_otp(
    data: PhoneOTPConfirm,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    otp_input = data.otp.strip()
    if not otp_input or not otp_input.isdigit() or len(otp_input) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP. Please enter the correct 6-digit code."
        )

    if not user.phone_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification code found. Please request a new OTP."
        )

    stored_str = user.phone_otp
    stored_code = stored_str
    if ":" in stored_str:
        stored_code, ts_str = stored_str.split(":", 1)
        try:
            ts = float(ts_str)
            # 10 minute expiration window (600 seconds)
            if time.time() - ts > 600:
                user.phone_otp = None
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This verification code has expired. Please request a new OTP."
                )
        except (ValueError, TypeError):
            pass

    # Compare code
    if stored_code != otp_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please enter the correct 6-digit code or request a new one."
        )

    # Success: verify and clear phone_otp (single-use)
    user.is_phone_verified = True
    user.phone_otp = None

    # Sync candidate phone if candidate exists
    cand = db.query(Candidate).filter(Candidate.user_id == user.id).first()
    if cand and user.phone:
        cand.phone = user.phone

    db.commit()
    return {"message": "Mobile number verified successfully!", "is_verified": True}

@router.post("/forgot-password", summary="Request Password Reset Link")
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if user:
        token = secrets.token_urlsafe(32)
        user.password_reset_token = f"{token}:{int(time.time())}"
        db.commit()

        origin = request.headers.get("origin") or request.headers.get("referer")
        base = (origin if origin and ("localhost" in origin or "127.0.0.1" in origin) else settings.FRONTEND_URL).rstrip("/")
        reset_link = f"{base}/#/reset-password?token={token}"

        email_provider = get_email_provider()
        email_provider.send_password_reset_email(user.email, user.full_name or "User", reset_link)

    # Generic response to prevent account enumeration
    return {"message": "If an account with this email exists, a password reset link has been sent."}

@router.post("/reset-password", summary="Reset Password with Token")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet the required security requirements."
        )

    token_clean = data.token.strip()
    user = None
    all_users = db.query(User).filter(User.password_reset_token.isnot(None)).all()
    for u in all_users:
        stored = u.password_reset_token or ""
        if stored == token_clean or stored.startswith(f"{token_clean}:"):
            user = u
            break

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired."
        )

    # Check 2-hour expiration (7200 seconds)
    stored_token = user.password_reset_token or ""
    if ":" in stored_token:
        try:
            _, ts_str = stored_token.rsplit(":", 1)
            ts = float(ts_str)
            if time.time() - ts > 7200:
                user.password_reset_token = None
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This password reset link has expired. Please request a new one."
                )
        except (ValueError, TypeError):
            pass

    user.hashed_password = get_password_hash(data.new_password)
    user.password_reset_token = None
    db.commit()

    return {"message": "Password updated successfully. You can now log in with your new password."}
