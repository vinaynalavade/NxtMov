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
from app.models.user import User, AccountType, AccountStatus
from app.models.mentor_application import MentorApplication, MentorApplicationStatus
from app.models.organization import Organization, OrganizationMembership, OrgType, OrgRole
from app.models.candidate import Candidate, CandidateStatus
from app.models.student_profile import StudentProfile
from app.schemas.user import (
    UserCreate, StudentRegisterRequest, MentorApplicationCreate, MentorApplicationResponse,
    AdminBootstrapRequest, AdminInviteRequest, UserLogin, UserResponse, Token,
    ActiveOrgInfo, UserRoleInfo,
    EmailVerifyRequest, EmailVerifyConfirm,
    PhoneOTPRequest, PhoneOTPConfirm,
    ForgotPasswordRequest, ResetPasswordRequest
)
from app.schemas.organization import OrganizationResponse, WorkspaceSwitchRequest

router = APIRouter()
_demo_lock = threading.Lock()

def ensure_demo_user_exists(db: Session):
    """
    Idempotently and reliably provisions the demo user with ADMIN account_type,
    along with student and mentor workspaces for test/eval convenience.
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
                    full_name="Demo Administrator",
                    phone="+91 99999 00000",
                    account_type=AccountType.ADMIN,
                    status=AccountStatus.ACTIVE,
                    is_active=True,
                    is_superuser=True,
                    is_email_verified=True,
                    is_phone_verified=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                needs_commit = False
                if not verify_password(settings.DEMO_USER_PASSWORD, user.hashed_password) or not user.is_active:
                    user.hashed_password = hashed_pwd
                    user.is_active = True
                    needs_commit = True
                if user.account_type != AccountType.ADMIN or user.status != AccountStatus.ACTIVE or not user.is_superuser:
                    user.account_type = AccountType.ADMIN
                    user.status = AccountStatus.ACTIVE
                    user.is_superuser = True
                    needs_commit = True
                if not user.is_email_verified or not user.is_phone_verified:
                    user.is_email_verified = True
                    user.is_phone_verified = True
                    needs_commit = True
                if needs_commit:
                    db.commit()
                    db.refresh(user)

            # Check or create demo organizations and memberships
            demo_roles = [
                ("demo-workspace", "Demo Workspace", OrgType.CONSULTANCY, OrgRole.ADMIN),
                ("demo-student-hub", "Student Career Hub", OrgType.INDIVIDUAL, OrgRole.STUDENT),
                ("demo-mentor-workspace", "Student Mentorship Desk", OrgType.CONSULTANCY, OrgRole.MENTOR),
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

                # Linked candidate & student profile
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
        except Exception:
            db.rollback()

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
    account_type_str = user.account_type.value if hasattr(user.account_type, "value") else str(user.account_type).upper()
    status_str = user.status.value if hasattr(user.status, "value") else str(user.status).upper()

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

        if active_org_id is not None and int(m.organization_id) == int(active_org_id):
            active_org_info = ActiveOrgInfo(
                id=m.organization_id,
                name=org_name,
                role=r_str
            )

    if not active_org_info and memberships:
        first_m = memberships[0]
        first_r = first_m.role.value if hasattr(first_m.role, "value") else str(first_m.role)
        if first_r.upper() == "CANDIDATE":
            first_r = "STUDENT"
        active_org_info = ActiveOrgInfo(
            id=first_m.organization_id,
            name=first_m.organization.name if first_m.organization else "Workspace",
            role=first_r
        )

    # Authoritative permissions derived directly from account_type and superuser status
    resolved_permissions = get_role_permissions(user.account_type, is_superuser=user.is_superuser)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        account_type=account_type_str,
        status=status_str,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        is_phone_verified=user.is_phone_verified,
        is_superuser=user.is_superuser,
        avatar_url=getattr(user, "avatar_url", None),
        headline=getattr(user, "headline", None),
        location=getattr(user, "location", None),
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

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, summary="Student Self-Registration")
def register(request: Request, user_in: UserCreate, db: Session = Depends(get_db)):
    # 1. Rate limiting
    check_register_rate_limit(request)

    # 2. Validation
    name_clean = user_in.full_name.strip() if user_in.full_name else ""
    if not name_clean:
        name_clean = user_in.email.split("@")[0].replace(".", " ").capitalize()

    if len(name_clean) < 2 or any(ch.isdigit() for ch in name_clean) or "@" in name_clean or "http://" in name_clean or "https://" in name_clean:
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
            detail="Password must be at least 6 characters long."
        )

    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    # 3. Create Student User (Authoritative STUDENT account_type, ACTIVE lifecycle)
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=email_clean,
        hashed_password=hashed_password,
        full_name=name_clean,
        phone=user_in.phone.strip() if user_in.phone else None,
        account_type=AccountType.STUDENT,
        status=AccountStatus.ACTIVE,
        is_active=True,
        is_email_verified=False,
        is_phone_verified=False
    )
    db.add(user)
    db.flush()

    # 4. Create Default Student Workspace
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
        role=OrgRole.STUDENT
    )
    db.add(membership)

    cand = Candidate(
        organization_id=personal_org.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        status=CandidateStatus.NEW,
        source="Student Self-Registration"
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

    access_token = create_access_token(
        subject=user.id,
        org_id=personal_org.id,
        role="STUDENT",
        account_type="STUDENT",
        status="ACTIVE"
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=personal_org.id,
        user=make_user_response(user, db, active_org_id=personal_org.id, active_role="STUDENT")
    )

@router.post("/apply-mentor", summary="Submit Mentor Application")
def apply_mentor(
    request: Request,
    mentor_in: MentorApplicationCreate,
    db: Session = Depends(get_db)
):
    check_register_rate_limit(request)

    name_clean = mentor_in.full_name.strip()
    if not name_clean or len(name_clean) < 2 or any(ch.isdigit() for ch in name_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid full name."
        )

    email_clean = mentor_in.official_email.strip().lower()
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_clean):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid official institutional email address."
        )

    if len(mentor_in.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    if not mentor_in.institute_name.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Institute name is required.")
    if not mentor_in.employee_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee / Faculty ID is required.")

    # Check existing user
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        if existing_user.account_type == AccountType.MENTOR and existing_user.status == AccountStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A mentor application for this official email is already pending review."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Check pending mentor application
    existing_app = db.query(MentorApplication).filter(
        MentorApplication.official_email == email_clean,
        MentorApplication.status == MentorApplicationStatus.PENDING
    ).first()
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A mentor application for this official email is already pending review."
        )

    # Create User with PENDING status (Cannot access Mentor dashboard until Approved)
    hashed_password = get_password_hash(mentor_in.password)
    user = User(
        email=email_clean,
        hashed_password=hashed_password,
        full_name=name_clean,
        phone=mentor_in.phone.strip() if mentor_in.phone else None,
        account_type=AccountType.MENTOR,
        status=AccountStatus.PENDING,
        is_active=False,
        is_email_verified=False,
        is_phone_verified=False
    )
    db.add(user)
    db.flush()

    # Create MentorApplication record
    app_record = MentorApplication(
        user_id=user.id,
        full_name=name_clean,
        official_email=email_clean,
        institute_name=mentor_in.institute_name.strip(),
        employee_id=mentor_in.employee_id.strip(),
        department=mentor_in.department.strip() if mentor_in.department else None,
        designation=mentor_in.designation.strip() if mentor_in.designation else None,
        status=MentorApplicationStatus.PENDING
    )
    db.add(app_record)
    db.commit()

    return {
        "success": True,
        "message": "Your Mentor application has been submitted successfully. It is currently under review by an Administrator.",
        "application_id": app_record.id,
        "status": "PENDING"
    }

@router.post("/admin/bootstrap", response_model=Token, summary="Bootstrap Initial Administrator Account")
def admin_bootstrap(
    data: AdminBootstrapRequest,
    db: Session = Depends(get_db)
):
    key_input = data.bootstrap_key.strip()
    configured_secret = settings.ADMIN_BOOTSTRAP_SECRET.strip()

    if not secrets.compare_digest(key_input, configured_secret):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid administrator bootstrap key."
        )

    email_clean = data.email.strip().lower()
    name_clean = data.full_name.strip()
    if not name_clean:
        name_clean = "Administrator"

    if len(data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    user = db.query(User).filter(User.email == email_clean).first()
    hashed_password = get_password_hash(data.password)

    if user:
        # Upgrade existing user to ADMIN
        user.hashed_password = hashed_password
        user.full_name = name_clean
        user.account_type = AccountType.ADMIN
        user.status = AccountStatus.ACTIVE
        user.is_active = True
        user.is_superuser = True
        user.is_email_verified = True
        db.commit()
        db.refresh(user)
    else:
        user = User(
            email=email_clean,
            hashed_password=hashed_password,
            full_name=name_clean,
            account_type=AccountType.ADMIN,
            status=AccountStatus.ACTIVE,
            is_active=True,
            is_superuser=True,
            is_email_verified=True,
            is_phone_verified=True
        )
        db.add(user)
        db.flush()

    # Ensure admin workspace exists
    admin_org = db.query(Organization).filter(
        Organization.owner_id == user.id,
        Organization.slug.like(f"admin-workspace-{user.id}%")
    ).first()
    if not admin_org:
        admin_org = Organization(
            name=f"{user.full_name}'s Admin Workspace",
            slug=f"admin-workspace-{user.id}",
            type=OrgType.CONSULTANCY,
            owner_id=user.id
        )
        db.add(admin_org)
        db.flush()

    mem = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user.id,
        OrganizationMembership.organization_id == admin_org.id
    ).first()
    if not mem:
        mem = OrganizationMembership(
            user_id=user.id,
            organization_id=admin_org.id,
            role=OrgRole.ADMIN
        )
        db.add(mem)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        subject=user.id,
        org_id=admin_org.id,
        role="ADMIN",
        account_type="ADMIN",
        status="ACTIVE"
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=admin_org.id,
        user=make_user_response(user, db, active_org_id=admin_org.id, active_role="ADMIN")
    )

@router.post("/login", response_model=Token, summary="User Login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    requested_role: Optional[str] = Query(None),
    requested_account_type: Optional[str] = Query(None),
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

    # 1. Resolve requested account type / context
    req_type = requested_account_type or requested_role
    if not req_type:
        req_type = request.headers.get("X-Requested-Role") or request.headers.get("X-Requested-Account-Type")
    if not req_type:
        try:
            form = await request.form()
            req_type = form.get("requested_account_type") or form.get("requested_role")
        except Exception:
            pass

    actual_account_type_str = user.account_type.value if hasattr(user.account_type, "value") else str(user.account_type).upper()
    user_status_str = user.status.value if hasattr(user.status, "value") else str(user.status).upper()

    # 2. Critical Backend Authentication Rule: Strict Account Type Matching
    if req_type:
        clean_req = str(req_type).strip().upper()
        if clean_req in ("CANDIDATE", "STUDENT"):
            clean_req = "STUDENT"
        elif clean_req in ("ADMINISTRATOR", "ADMIN"):
            clean_req = "ADMIN"
        elif clean_req == "MENTOR":
            clean_req = "MENTOR"

        ROLE_DISPLAY_NAMES = {
            "ADMIN": "Administrator",
            "MENTOR": "Mentor",
            "STUDENT": "Student",
            "RECRUITER": "Recruiter"
        }

        # Allow superuser to access Admin context
        is_admin_allowed = user.is_superuser and clean_req == "ADMIN"

        if actual_account_type_str != clean_req and not is_admin_allowed:
            actual_display = ROLE_DISPLAY_NAMES.get(actual_account_type_str, actual_account_type_str.title())
            clean_display = ROLE_DISPLAY_NAMES.get(clean_req, clean_req.title())
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This account is registered as a {actual_display}. Please select {actual_display}."
            )

    # 3. Lifecycle Status Checks
    if user_status_str == "PENDING":
        app = db.query(MentorApplication).filter(
            (MentorApplication.user_id == user.id) | (MentorApplication.official_email == user.email)
        ).order_by(MentorApplication.id.desc()).first()
        if app and app.status == MentorApplicationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your Mentor application is currently pending administrator review. You will be notified once approved."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is currently pending administrator approval."
        )

    if user_status_str == "REJECTED":
        app = db.query(MentorApplication).filter(
            (MentorApplication.user_id == user.id) | (MentorApplication.official_email == user.email)
        ).order_by(MentorApplication.id.desc()).first()
        reason = f" Reason: {app.rejection_reason}" if (app and app.rejection_reason) else ""
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your Mentor application was not approved.{reason}"
        )

    if user_status_str == "SUSPENDED" or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has been deactivated or suspended."
        )

    # 4. Successful Authentication
    reset_login_rate_limit(request, username_clean)

    memberships = (
        db.query(OrganizationMembership)
        .filter(OrganizationMembership.user_id == user.id)
        .all()
    )

    active_org_id = memberships[0].organization_id if memberships else 0

    if not memberships:
        org_slug = f"workspace-{user.id}"
        org = Organization(
            name=f"{user.full_name}'s Workspace",
            slug=org_slug,
            type=OrgType.INDIVIDUAL if actual_account_type_str == "STUDENT" else OrgType.CONSULTANCY,
            owner_id=user.id
        )
        db.add(org)
        db.flush()
        m = OrganizationMembership(
            user_id=user.id,
            organization_id=org.id,
            role=OrgRole.STUDENT if actual_account_type_str == "STUDENT" else (OrgRole.MENTOR if actual_account_type_str == "MENTOR" else OrgRole.ADMIN)
        )
        db.add(m)
        db.commit()
        active_org_id = org.id

    access_token = create_access_token(
        subject=user.id,
        org_id=active_org_id,
        role=actual_account_type_str,
        account_type=actual_account_type_str,
        status=user_status_str
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=active_org_id,
        user=make_user_response(
            user,
            db,
            active_org_id=active_org_id,
            active_role=actual_account_type_str
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
            token_role = payload.get("role") or payload.get("account_type")

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
