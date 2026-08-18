"""
Development & Demo Account Seeding for NxtMov.

Provides idempotent, development-only seeding for standard evaluation accounts:
- Student: student.tester@example.com (Password123!)
- Mentor:  prof.mentor@example.edu (MentorPass123!)
- Admin:   demo@nxtmov.local (NxtMov@123)
"""

import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, AccountType, AccountStatus
from app.models.organization import Organization, OrganizationMembership, OrgType, OrgRole
from app.models.candidate import Candidate, CandidateStatus
from app.models.student_profile import StudentProfile

logger = logging.getLogger(__name__)

DEMO_ACCOUNTS = [
    {
        "email": "student.tester@example.com",
        "password": "Password123!",
        "full_name": "Student Tester",
        "phone": "+91 98765 43210",
        "account_type": AccountType.STUDENT,
        "is_superuser": False,
        "org_name": "Student Career Hub",
        "org_slug": "student-career-hub",
        "org_type": OrgType.INDIVIDUAL,
        "org_role": OrgRole.STUDENT,
        "headline": "Computer Science Student & Aspiring Software Engineer"
    },
    {
        "email": "prof.mentor@example.edu",
        "password": "MentorPass123!",
        "full_name": "Prof. Marcus Vance",
        "phone": "+91 98765 43211",
        "account_type": AccountType.MENTOR,
        "is_superuser": False,
        "org_name": "Student Mentorship Desk",
        "org_slug": "student-mentorship-desk",
        "org_type": OrgType.CONSULTANCY,
        "org_role": OrgRole.MENTOR,
        "headline": "Senior Career Counselor & Technical Mentor"
    },
    {
        "email": "demo@nxtmov.local",
        "password": "NxtMov@123",
        "full_name": "Demo Administrator",
        "phone": "+91 99999 00000",
        "account_type": AccountType.ADMIN,
        "is_superuser": True,
        "org_name": "Demo Workspace",
        "org_slug": "demo-workspace",
        "org_type": OrgType.CONSULTANCY,
        "org_role": OrgRole.ADMIN,
        "headline": "Platform System Administrator"
    }
]

def seed_demo_accounts(db: Session) -> None:
    """
    Seeds standard development/demo evaluation accounts.
    Executes only if settings.NXTMOV_DEMO_MODE is True.
    Idempotent: Creates accounts if missing, never alters existing users.
    """
    if not settings.NXTMOV_DEMO_MODE:
        return

    for account_data in DEMO_ACCOUNTS:
        email = account_data["email"].strip().lower()
        user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash(account_data["password"]),
                full_name=account_data["full_name"],
                phone=account_data["phone"],
                account_type=account_data["account_type"],
                status=AccountStatus.ACTIVE,
                is_active=True,
                is_superuser=account_data["is_superuser"],
                is_email_verified=True,
                is_phone_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created demo user: {email} ({account_data['account_type'].value})")

        # Ensure default workspace exists
        org_slug = f"{account_data['org_slug']}-{user.id}"
        org = db.query(Organization).filter(
            (Organization.slug == org_slug) | (Organization.owner_id == user.id)
        ).first()

        if not org:
            org = Organization(
                name=account_data["org_name"],
                slug=org_slug,
                type=account_data["org_type"],
                owner_id=user.id
            )
            db.add(org)
            db.commit()
            db.refresh(org)

        # Ensure membership exists
        mem = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == org.id
        ).first()

        if not mem:
            mem = OrganizationMembership(
                user_id=user.id,
                organization_id=org.id,
                role=account_data["org_role"]
            )
            db.add(mem)
            db.commit()

        # If student, ensure Candidate and StudentProfile exist
        if account_data["account_type"] == AccountType.STUDENT:
            cand = db.query(Candidate).filter(
                Candidate.organization_id == org.id,
                Candidate.email == user.email
            ).first()
            if not cand:
                cand = Candidate(
                    organization_id=org.id,
                    user_id=user.id,
                    full_name=user.full_name,
                    email=user.email,
                    phone=user.phone,
                    status=CandidateStatus.NEW
                )
                db.add(cand)
                db.commit()
                db.refresh(cand)

            prof = db.query(StudentProfile).filter(
                StudentProfile.candidate_id == cand.id
            ).first()
            if not prof:
                prof = StudentProfile(
                    organization_id=org.id,
                    user_id=user.id,
                    candidate_id=cand.id,
                    headline=account_data.get("headline", "Student"),
                    completeness_score=85
                )
                db.add(prof)
                db.commit()
