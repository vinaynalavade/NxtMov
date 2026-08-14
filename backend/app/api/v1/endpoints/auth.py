import re
from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.tenant import get_current_user, TenantContext
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership, OrgType, OrgRole
from app.models.candidate import Candidate, CandidateStatus
from app.schemas.user import UserCreate, UserResponse, Token
from app.schemas.organization import OrganizationResponse, WorkspaceSwitchRequest

router = APIRouter()

# REMOVE BEFORE PRODUCTION DEPLOYMENT
def ensure_demo_user_exists(db: Session):
    if not settings.NXTMOV_DEMO_MODE:
        return
    existing = db.query(User).filter(User.email == settings.DEMO_USER_EMAIL).first()
    if not existing:
        hashed_pwd = get_password_hash(settings.DEMO_USER_PASSWORD)
        user = User(
            email=settings.DEMO_USER_EMAIL,
            hashed_password=hashed_pwd,
            full_name="Demo User",
            phone="+91 99999 00000"
        )
        db.add(user)
        db.flush()

        org_slug = f"user-{user.id}-demo-workspace"
        personal_org = Organization(
            name="Demo Workspace",
            slug=org_slug,
            type=OrgType.INDIVIDUAL,
            owner_id=user.id
        )
        db.add(personal_org)
        db.flush()

        membership = OrganizationMembership(
            organization_id=personal_org.id,
            user_id=user.id,
            role=OrgRole.ADMIN
        )
        db.add(membership)

        personal_candidate = Candidate(
            organization_id=personal_org.id,
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            status=CandidateStatus.NEW
        )
        db.add(personal_candidate)
        db.commit()

@router.get("/config", summary="Get Auth & Demo Mode Configuration")
def get_auth_config(db: Session = Depends(get_db)):
    if settings.NXTMOV_DEMO_MODE:
        ensure_demo_user_exists(db)
        return {
            "demo_mode": True,
            "demo_email": settings.DEMO_USER_EMAIL,
            "demo_password": settings.DEMO_USER_PASSWORD,
            "notice": "DEMO / DEVELOPMENT MODE ACTIVE. REMOVE BEFORE PRODUCTION DEPLOYMENT."
        }
    return {"demo_mode": False}

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '-', text)

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, summary="Register User & Provision Personal Workspace")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check existing user
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # 1. Create User
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        phone=user_in.phone
    )
    db.add(user)
    db.flush()

    # 2. Provision Personal Organization Workspace
    org_slug = f"user-{user.id}-{slugify(user_in.full_name)}"
    personal_org = Organization(
        name=f"{user.full_name}'s Workspace",
        slug=org_slug,
        type=OrgType.INDIVIDUAL,
        owner_id=user.id
    )
    db.add(personal_org)
    db.flush()

    # 3. Create Membership as ADMIN
    membership = OrganizationMembership(
        organization_id=personal_org.id,
        user_id=user.id,
        role=OrgRole.ADMIN
    )
    db.add(membership)

    # 4. Auto-create personal Candidate profile for Individual Mode applications
    personal_candidate = Candidate(
        organization_id=personal_org.id,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        status=CandidateStatus.NEW
    )
    db.add(personal_candidate)

    db.commit()
    db.refresh(user)

    # 5. Issue JWT token
    access_token = create_access_token(subject=user.id, org_id=personal_org.id, role=OrgRole.ADMIN.value)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=personal_org.id,
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=Token, summary="User Login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account."
        )

    # Find primary membership
    membership = db.query(OrganizationMembership).filter(OrganizationMembership.user_id == user.id).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to any workspace organization."
        )

    access_token = create_access_token(subject=user.id, org_id=membership.organization_id, role=membership.role.value)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        active_org_id=membership.organization_id,
        user=UserResponse.model_validate(user)
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
        "user": UserResponse.model_validate(user),
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
        user=UserResponse.model_validate(user)
    )
