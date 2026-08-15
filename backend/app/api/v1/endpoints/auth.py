import re
import secrets
import threading
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.tenant import get_current_user, TenantContext
from app.core.rate_limiter import check_login_rate_limit, reset_login_rate_limit, check_register_rate_limit
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

            # Check or create demo organization
            demo_org = db.query(Organization).filter(Organization.owner_id == user.id).first()
            if not demo_org:
                demo_org = db.query(Organization).filter(Organization.slug == "demo-workspace").first()
            if not demo_org:
                demo_org = Organization(
                    name="Demo Workspace",
                    slug="demo-workspace",
                    type=OrgType.INDIVIDUAL,
                    owner_id=user.id
                )
                db.add(demo_org)
                db.commit()
                db.refresh(demo_org)

            # Check or create organization membership
            membership = db.query(OrganizationMembership).filter(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.organization_id == demo_org.id
            ).first()
            if not membership:
                membership = OrganizationMembership(
                    user_id=user.id,
                    organization_id=demo_org.id,
                    role=OrgRole.ADMIN
                )
                db.add(membership)
                db.commit()

            # Check or create linked candidate
            cand = db.query(Candidate).filter(
                Candidate.organization_id == demo_org.id,
                Candidate.email == user.email
            ).first()
            if not cand:
                cand = Candidate(
                    organization_id=demo_org.id,
                    user_id=user.id,
                    full_name=user.full_name,
                    email=user.email,
                    phone=user.phone,
                    status=CandidateStatus.NEW
                )
                db.add(cand)
                db.commit()
                db.refresh(cand)

            # Check or create student profile
            profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == user.id
            ).first()
            if not profile:
                profile = StudentProfile(
                    organization_id=demo_org.id,
                    user_id=user.id,
                    candidate_id=cand.id,
                    headline="Full Stack Software Engineer",
                    completeness_score=85
                )
                db.add(profile)
                db.commit()
        except Exception as e:
            db.rollback()

def make_user_response(user: User, db: Session) -> UserResponse:
    u = UserResponse.model_validate(user)
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if profile and profile.avatar_url:
        u.avatar_url = profile.avatar_url
    return u

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

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, summary="Register New User Account")
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
        user=make_user_response(user, db)
    )

@router.post("/login", response_model=Token, summary="User Login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username_clean = form_data.username.strip().lower()

    check_login_rate_limit(request, username_clean)

    if settings.NXTMOV_DEMO_MODE and username_clean == settings.DEMO_USER_EMAIL.lower():
        ensure_demo_user_exists(db)

    user = db.query(User).filter(User.email == username_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email address.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account."
        )

    membership = db.query(OrganizationMembership).filter(OrganizationMembership.user_id == user.id).first()
    if not membership:
        org = Organization(
            name=f"{user.full_name}'s Workspace",
            slug=f"workspace-{user.id}",
            type=OrgType.INDIVIDUAL,
            owner_id=user.id
        )
        db.add(org)
        db.flush()
        membership = OrganizationMembership(
            user_id=user.id,
            organization_id=org.id,
            role=OrgRole.ADMIN
        )
        db.add(membership)
        db.commit()

    reset_login_rate_limit(request, username_clean)

    access_token = create_access_token(subject=user.id, org_id=membership.organization_id, role=membership.role.value)

    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=membership.organization_id,
        user=make_user_response(user, db)
    )

@router.get("/me", summary="Get Current User Profile & Workspaces")
def get_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user.id)
        .all()
    )
    org_list = []
    for m in memberships:
        if not m.organization:
            continue
        org_resp = OrganizationResponse.model_validate(m.organization)
        role_str = m.role.value if hasattr(m.role, "value") else str(m.role)
        org_dict = org_resp.model_dump()
        org_dict["role"] = role_str
        org_list.append(org_dict)

    return {
        "user": make_user_response(user, db),
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
        user=make_user_response(user, db)
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

    token = secrets.token_urlsafe(32)
    user.email_verification_token = token
    db.commit()

    # Determine frontend application URL
    origin = request.headers.get("origin") or request.headers.get("referer")
    if origin and ("localhost" in origin or "127.0.0.1" in origin):
        frontend_base = origin.rstrip("/")
    else:
        frontend_base = settings.FRONTEND_URL.rstrip("/")
    
    verification_link = f"{frontend_base}/#/verify-email?token={token}"

    if settings.NXTMOV_DEMO_MODE and user.email == settings.DEMO_USER_EMAIL:
        user.is_email_verified = True
        db.commit()
        return {"message": "Verification link sent. Check your email.", "is_verified": True, "verification_link": verification_link}

    return {"message": "Verification link sent. Check your email.", "is_verified": False, "verification_link": verification_link}

@router.get("/verify-email", summary="Confirm Email Verification via Direct Link")
def confirm_email_verification_get(
    token: str = Query(..., description="Email verification token"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email_verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has already been used."
        )

    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()

    return {"message": "Email verified successfully.", "is_verified": True}

@router.post("/verify-email/confirm", summary="Confirm Email Verification Token")
def confirm_email_verification(
    data: EmailVerifyConfirm,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email_verification_token == data.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has already been used."
        )

    user.is_email_verified = True
    user.email_verification_token = None
    db.commit()

    return {"message": "Email verified successfully.", "is_verified": True}

@router.post("/verify-phone/request-otp", summary="Request Phone OTP Verification")
def request_phone_otp(
    data: PhoneOTPRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_digits = re.sub(r"\D", "", data.phone)
    if len(clean_digits) < 7 or len(clean_digits) > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid mobile number (7 to 15 digits)."
        )

    otp = str(secrets.randbelow(900000) + 100000)
    user.phone = data.phone.strip()
    user.phone_otp = otp
    db.commit()

    if settings.NXTMOV_DEMO_MODE:
        user.is_phone_verified = True
        db.commit()
        return {"message": "Phone number verified successfully.", "is_verified": True}

    return {"message": "OTP sent successfully to your mobile number.", "is_verified": False}

@router.post("/verify-phone/confirm-otp", summary="Confirm Phone OTP")
def confirm_phone_otp(
    data: PhoneOTPConfirm,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if settings.NXTMOV_DEMO_MODE or (user.phone_otp and user.phone_otp == data.otp.strip()):
        user.is_phone_verified = True
        user.phone_otp = None
        db.commit()
        return {"message": "Mobile number verified successfully!", "is_verified": True}

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid OTP. Please enter the correct 6-digit code or request a new one."
    )

@router.post("/forgot-password", summary="Request Password Reset Link")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if user:
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        db.commit()

    # OWASP generic response to prevent account enumeration
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

    user = db.query(User).filter(User.password_reset_token == data.token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or has expired."
        )

    user.hashed_password = get_password_hash(data.new_password)
    user.password_reset_token = None
    db.commit()

    return {"message": "Password updated successfully. You can now log in with your new password."}
