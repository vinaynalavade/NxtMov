from datetime import datetime, timezone
import secrets
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_account_type
from app.models.user import User, AccountType, AccountStatus
from app.models.mentor_application import MentorApplication, MentorApplicationStatus
from app.models.organization import Organization, OrganizationMembership, OrgType, OrgRole
from app.models.student_profile import StudentProfile
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.application import Application
from app.models.notification import Notification
from app.schemas.user import (
    MentorApplicationResponse, MentorApprovalAction, AdminInviteRequest,
    UserStatusUpdate, UserResponse
)

router = APIRouter()

@router.get("/mentor-applications", response_model=List[MentorApplicationResponse], summary="List Mentor Applications")
def list_mentor_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    query = db.query(MentorApplication)
    if status_filter:
        clean_status = status_filter.strip().upper()
        if clean_status in ("PENDING", "APPROVED", "REJECTED"):
            query = query.filter(MentorApplication.status == clean_status)

    apps = query.order_by(MentorApplication.submitted_at.desc()).all()
    return apps

@router.get("/mentor-applications/{app_id}", response_model=MentorApplicationResponse, summary="Get Mentor Application Details")
def get_mentor_application(
    app_id: int,
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    app = db.query(MentorApplication).filter(MentorApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor application not found.")
    return app

@router.post("/mentor-applications/{app_id}/approve", response_model=MentorApplicationResponse, summary="Approve Mentor Application")
def approve_mentor_application(
    app_id: int,
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    app = db.query(MentorApplication).filter(MentorApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor application not found.")

    try:
        app.status = MentorApplicationStatus.APPROVED
        app.reviewed_at = datetime.now(timezone.utc)
        app.reviewed_by = current_admin.id
        app.rejection_reason = None

        # Activate linked user
        user = app.user
        if not user:
            user = db.query(User).filter(User.email == app.official_email).first()
            if user:
                app.user_id = user.id

        if user:
            user.account_type = AccountType.MENTOR
            user.status = AccountStatus.ACTIVE
            user.is_active = True
            user.is_email_verified = True

            # Check or provision mentor workspace
            m_org = db.query(Organization).filter(
                Organization.owner_id == user.id,
                Organization.type == OrgType.CONSULTANCY
            ).first()

            if not m_org:
                clean_slug = f"mentor-hub-{user.id}-{secrets.token_hex(3)}"
                m_org = Organization(
                    name=f"{user.full_name}'s Mentorship Hub",
                    slug=clean_slug,
                    type=OrgType.CONSULTANCY,
                    owner_id=user.id
                )
                db.add(m_org)
                db.flush()

            mem = db.query(OrganizationMembership).filter(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.organization_id == m_org.id
            ).first()
            if not mem:
                mem = OrganizationMembership(
                    user_id=user.id,
                    organization_id=m_org.id,
                    role=OrgRole.MENTOR
                )
                db.add(mem)
            elif mem.role != OrgRole.MENTOR:
                mem.role = OrgRole.MENTOR

            # Create confirmation notification linked to mentor's organization
            notif = Notification(
                organization_id=m_org.id,
                user_id=user.id,
                title="Mentor Application Approved!",
                message="Your institutional mentor application has been approved. You now have full access to the Mentor Workspace.",
                notification_type="INFO",
                link_url="#/mentor"
            )
            db.add(notif)

        db.commit()
        db.refresh(app)
        return app
    except Exception as e:
        db.rollback()
        raise e

@router.post("/mentor-applications/{app_id}/reject", response_model=MentorApplicationResponse, summary="Reject Mentor Application")
def reject_mentor_application(
    app_id: int,
    action: Optional[MentorApprovalAction] = None,
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    app = db.query(MentorApplication).filter(MentorApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mentor application not found.")

    rejection_msg = (action.rejection_reason.strip() if action and action.rejection_reason else "Institutional verification criteria not met.")

    app.status = MentorApplicationStatus.REJECTED
    app.reviewed_at = datetime.now(timezone.utc)
    app.reviewed_by = current_admin.id
    app.rejection_reason = rejection_msg

    # Mark linked user as REJECTED
    user = app.user
    if not user:
        user = db.query(User).filter(User.email == app.official_email).first()

    if user:
        user.status = AccountStatus.REJECTED
        user.is_active = False

    db.commit()
    db.refresh(app)
    return app

@router.get("/students", summary="List All Students for Admin")
def list_students_admin(
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    students = db.query(User).filter(User.account_type == AccountType.STUDENT).order_by(User.id.desc()).all()
    results = []
    for s in students:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == s.id).first()
        
        # Accurately count resumes and applications linked via Candidate model
        resumes_count = (
            db.query(Resume)
            .join(Candidate, Resume.candidate_id == Candidate.id)
            .filter((Candidate.user_id == s.id) | (Candidate.email == s.email))
            .count()
        )
        apps_count = (
            db.query(Application)
            .join(Candidate, Application.candidate_id == Candidate.id)
            .filter((Candidate.user_id == s.id) | (Candidate.email == s.email))
            .count()
        )

        results.append({
            "id": s.id,
            "full_name": s.full_name,
            "email": s.email,
            "phone": s.phone,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "is_active": s.is_active,
            "is_email_verified": s.is_email_verified,
            "completeness_score": profile.completeness_score if profile else 0,
            "headline": profile.headline if profile else "Student Talent",
            "city": profile.city if profile else "",
            "resumes_count": resumes_count,
            "applications_count": apps_count,
            "created_at": s.created_at
        })
    return results

@router.get("/mentors", summary="List All Active Mentors for Admin")
def list_mentors_admin(
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    mentors = db.query(User).filter(User.account_type == AccountType.MENTOR).order_by(User.id.desc()).all()
    results = []
    for m in mentors:
        app = db.query(MentorApplication).filter(MentorApplication.user_id == m.id).first() or db.query(MentorApplication).filter(MentorApplication.official_email == m.email).first()
        results.append({
            "id": m.id,
            "full_name": m.full_name,
            "email": m.email,
            "phone": m.phone,
            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
            "is_active": m.is_active,
            "institute_name": app.institute_name if app else "Academic Institute",
            "employee_id": app.employee_id if app else "—",
            "department": app.department if app else "Academic Faculty",
            "designation": app.designation if app else "Mentor",
            "created_at": m.created_at
        })
    return results

@router.get("/users", summary="List All Platform Users for Admin")
def list_users_admin(
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.id.desc()).all()
    results = []
    for u in users:
        results.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "account_type": u.account_type.value if hasattr(u.account_type, "value") else str(u.account_type),
            "status": u.status.value if hasattr(u.status, "value") else str(u.status),
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "is_email_verified": u.is_email_verified,
            "created_at": u.created_at
        })
    return results

@router.put("/users/{user_id}/status", summary="Update User Status")
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if target_user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot modify your own administrator account status.")

    clean_status = data.status.strip().upper()
    if clean_status in ("ACTIVE", "PENDING", "SUSPENDED", "REJECTED"):
        target_user.status = AccountStatus(clean_status)
    if data.is_active is not None:
        target_user.is_active = data.is_active

    db.commit()
    db.refresh(target_user)
    return {"message": f"User status updated to {target_user.status.value}."}

@router.post("/invite", summary="Invite an Administrator or Mentor")
def invite_user_admin(
    data: AdminInviteRequest,
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    email_clean = data.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A user with this email already exists.")

    invited_type = data.account_type.strip().upper()
    if invited_type not in ("ADMIN", "MENTOR", "STUDENT"):
        invited_type = "ADMIN"

    # Create user with temporary password / invite link
    temp_pass = secrets.token_urlsafe(12)
    from app.core.security import get_password_hash
    hashed = get_password_hash(temp_pass)

    new_user = User(
        email=email_clean,
        hashed_password=hashed,
        full_name=data.full_name.strip() if data.full_name else email_clean.split("@")[0].capitalize(),
        account_type=AccountType(invited_type),
        status=AccountStatus.ACTIVE,
        is_active=True,
        is_superuser=(invited_type == "ADMIN"),
        is_email_verified=True
    )
    db.add(new_user)
    db.flush()

    # Create workspace
    org_slug = f"workspace-{new_user.id}-{secrets.token_hex(3)}"
    org = Organization(
        name=f"{new_user.full_name}'s Workspace",
        slug=org_slug,
        type=OrgType.CONSULTANCY if invited_type != "STUDENT" else OrgType.INDIVIDUAL,
        owner_id=new_user.id
    )
    db.add(org)
    db.flush()

    mem = OrganizationMembership(
        user_id=new_user.id,
        organization_id=org.id,
        role=OrgRole(invited_type)
    )
    db.add(mem)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "message": f"Successfully invited {new_user.full_name} as {invited_type}.",
        "user_id": new_user.id,
        "temp_password": temp_pass
    }

@router.get("/stats", summary="Get Administrator Overview Metrics")
def get_admin_stats(
    current_admin: User = Depends(require_account_type(AccountType.ADMIN)),
    db: Session = Depends(get_db)
):
    total_students = db.query(User).filter(User.account_type == AccountType.STUDENT).count()
    total_mentors = db.query(User).filter(User.account_type == AccountType.MENTOR, User.status == AccountStatus.ACTIVE).count()
    pending_mentor_apps = db.query(MentorApplication).filter(MentorApplication.status == MentorApplicationStatus.PENDING).count()
    total_users = db.query(User).count()
    total_organizations = db.query(Organization).count()

    return {
        "total_students": total_students,
        "total_mentors": total_mentors,
        "pending_mentor_applications": pending_mentor_apps,
        "total_users": total_users,
        "total_organizations": total_organizations
    }
