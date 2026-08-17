import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import Base, engine, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership, OrgRole, OrgType
from app.models.company import Company
from app.models.candidate import Candidate, CandidateStatus
from app.models.requirement import JobRequirement, RequirementStatus, EmploymentType

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    yield session
    session.close()

def create_test_user_and_org(db: Session, email_prefix: str, role: OrgRole = OrgRole.ADMIN, org_name: str = "Test Org"):
    uid = uuid.uuid4().hex[:6]
    email = f"{email_prefix}_{uid}@nxtmov.local"
    user = User(
        email=email,
        full_name=f"User {email_prefix.title()}",
        hashed_password=get_password_hash("TestPass123!"),
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.flush()

    org = Organization(
        name=f"{org_name} {uid}",
        slug=f"org-{email_prefix}-{uid}",
        type=OrgType.CONSULTANCY,
        owner_id=user.id
    )
    db.add(org)
    db.flush()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org.id,
        role=role
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    db.refresh(org)
    return user, org, membership

def get_auth_headers(user: User, org: Organization, role: OrgRole):
    token = create_access_token(
        subject=user.id,
        org_id=org.id,
        role=role.value if hasattr(role, "value") else str(role)
    )
    return {"Authorization": f"Bearer {token}"}

class TestCanonicalRBAC:
    def test_admin_has_full_permissions(self, db_session):
        admin_user, org, _ = create_test_user_and_org(db_session, "admin", OrgRole.ADMIN, "Admin Test Org")
        headers = get_auth_headers(admin_user, org, OrgRole.ADMIN)

        # 1. Admin can list team members
        res = client.get("/api/v1/organizations/team", headers=headers)
        assert res.status_code == 200
        team = res.json()
        assert len(team) >= 1
        assert team[0]["email"] == admin_user.email
        assert team[0]["role"] == "ADMIN"

        # 2. Admin can create company and requirements
        comp = Company(
            organization_id=org.id,
            name=f"TechCorp {uuid.uuid4().hex[:4]}",
            industry="Software",
            location="Bengaluru"
        )
        db_session.add(comp)
        db_session.commit()
        db_session.refresh(comp)

        req_res = client.post(
            "/api/v1/requirements",
            headers=headers,
            json={
                "company_id": comp.id,
                "title": "Lead Software Engineer",
                "description": "Building next-gen systems",
                "skills_req": "Python, TypeScript",
                "employment_type": "FULL_TIME"
            }
        )
        assert req_res.status_code == 201

    def test_student_role_restrictions(self, db_session):
        student_user, org, _ = create_test_user_and_org(db_session, "student", OrgRole.STUDENT, "Student Test Org")
        headers = get_auth_headers(student_user, org, OrgRole.STUDENT)

        # 1. Student CANNOT view candidate database roster
        res = client.get("/api/v1/candidates", headers=headers)
        assert res.status_code == 403

        # 2. Student CANNOT view mentor student list
        mentor_res = client.get("/api/v1/mentor/students", headers=headers)
        assert mentor_res.status_code == 403

        # 3. Student CANNOT invite team members
        inv_res = client.post(
            "/api/v1/organizations/invitations",
            headers=headers,
            json={"email": f"newbie_{uuid.uuid4().hex[:4]}@test.local", "role": "STUDENT"}
        )
        assert inv_res.status_code == 403

        # 4. Student CAN view jobs
        jobs_res = client.get("/api/v1/requirements", headers=headers)
        assert jobs_res.status_code == 200

    def test_recruiter_permissions(self, db_session):
        recruiter_user, org, _ = create_test_user_and_org(db_session, "recruiter", OrgRole.RECRUITER, "Recruiter Test Org")
        headers = get_auth_headers(recruiter_user, org, OrgRole.RECRUITER)

        # 1. Recruiter CAN view and create candidates
        cand_email = f"applicant_{uuid.uuid4().hex[:6]}@example.com"
        create_res = client.post(
            "/api/v1/candidates",
            headers=headers,
            json={
                "full_name": "Applicant One",
                "email": cand_email,
                "phone": "+91 9876543210",
                "primary_skills": "Python, SQL"
            }
        )
        assert create_res.status_code == 201

        list_res = client.get("/api/v1/candidates", headers=headers)
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 2. Recruiter CANNOT change team roles
        role_res = client.put(
            f"/api/v1/organizations/members/{recruiter_user.id}/role",
            headers=headers,
            json={"role": "ADMIN"}
        )
        assert role_res.status_code == 403

    def test_mentor_assigned_students_scoping(self, db_session):
        mentor_user, org, _ = create_test_user_and_org(db_session, "mentor", OrgRole.MENTOR, "Mentor Test Org")
        headers = get_auth_headers(mentor_user, org, OrgRole.MENTOR)

        # Create 2 candidates: one assigned to mentor, one unassigned
        cand_assigned_email = f"assigned_{uuid.uuid4().hex[:6]}@test.local"
        cand_unassigned_email = f"unassigned_{uuid.uuid4().hex[:6]}@test.local"
        cand_assigned = Candidate(
            organization_id=org.id,
            full_name="Assigned Student",
            email=cand_assigned_email,
            assigned_counselor_id=mentor_user.id
        )
        cand_unassigned = Candidate(
            organization_id=org.id,
            full_name="Unassigned Student",
            email=cand_unassigned_email
        )
        db_session.add(cand_assigned)
        db_session.add(cand_unassigned)
        db_session.commit()

        # Mentor accesses /mentor/students
        res = client.get("/api/v1/mentor/students", headers=headers)
        assert res.status_code == 200
        data = res.json()
        student_emails = [s["email"] for s in data["students"]]
        assert cand_assigned_email in student_emails
        assert cand_unassigned_email not in student_emails

    def test_last_admin_protection(self, db_session):
        admin_user, org, membership = create_test_user_and_org(db_session, "sole_admin", OrgRole.ADMIN, "Sole Admin Org")
        headers = get_auth_headers(admin_user, org, OrgRole.ADMIN)

        # Attempt to demote the sole admin to STUDENT
        res = client.put(
            f"/api/v1/organizations/members/{admin_user.id}/role",
            headers=headers,
            json={"role": "STUDENT"}
        )
        assert res.status_code == 400
        assert "last Administrator" in res.json()["detail"]

        # Attempt to remove the sole admin
        del_res = client.delete(
            f"/api/v1/organizations/members/{admin_user.id}",
            headers=headers
        )
        assert del_res.status_code == 400
        assert "last Administrator" in del_res.json()["detail"]

        # Add a second admin
        second_email = f"second_admin_{uuid.uuid4().hex[:4]}@nxtmov.local"
        second_admin = User(
            email=second_email,
            full_name="Second Admin",
            hashed_password=get_password_hash("TestPass123!"),
            is_active=True
        )
        db_session.add(second_admin)
        db_session.flush()
        m2 = OrganizationMembership(
            user_id=second_admin.id,
            organization_id=org.id,
            role=OrgRole.ADMIN
        )
        db_session.add(m2)
        db_session.commit()

        # Now demoting the first admin succeeds
        ok_res = client.put(
            f"/api/v1/organizations/members/{admin_user.id}/role",
            headers=headers,
            json={"role": "MENTOR"}
        )
        assert ok_res.status_code == 200
        assert ok_res.json()["role"] == "MENTOR"

    def test_multi_workspace_switch_and_permissions(self, db_session):
        # User belongs to Org 1 as ADMIN and Org 2 as STUDENT
        multi_email = f"multi_{uuid.uuid4().hex[:6]}@nxtmov.local"
        multi_user = User(
            email=multi_email,
            full_name="Multi User",
            hashed_password=get_password_hash("TestPass123!"),
            is_active=True
        )
        db_session.add(multi_user)
        db_session.flush()

        uid1 = uuid.uuid4().hex[:4]
        uid2 = uuid.uuid4().hex[:4]
        org1 = Organization(name="Company Org", slug=f"comp-org-{uid1}", type=OrgType.CONSULTANCY, owner_id=multi_user.id)
        org2 = Organization(name="Individual Org", slug=f"acad-org-{uid2}", type=OrgType.INDIVIDUAL, owner_id=multi_user.id)
        db_session.add(org1)
        db_session.add(org2)
        db_session.flush()

        db_session.add(OrganizationMembership(user_id=multi_user.id, organization_id=org1.id, role=OrgRole.ADMIN))
        db_session.add(OrganizationMembership(user_id=multi_user.id, organization_id=org2.id, role=OrgRole.STUDENT))
        db_session.commit()

        # Login and check active org context
        login_res = client.post(
            "/api/v1/auth/login",
            data={"username": multi_email, "password": "TestPass123!"}
        )
        assert login_res.status_code == 200
        data = login_res.json()
        assert len(data["user"]["roles"]) == 2

        # Switch to Individual Org (where user is STUDENT)
        switch_res = client.post(
            f"/api/v1/auth/switch?organization_id={org2.id}",
            headers={"Authorization": f"Bearer {data['access_token']}"}
        )
        assert switch_res.status_code == 200
        switched = switch_res.json()
        assert switched["active_org_id"] == org2.id
        assert switched["user"]["active_organization"]["role"] == "STUDENT"
        assert "candidates.view" not in switched["user"]["permissions"]

        # Attempt to access candidate roster in Org 2
        student_headers = {"Authorization": f"Bearer {switched['access_token']}"}
        restricted_res = client.get("/api/v1/candidates", headers=student_headers)
        assert restricted_res.status_code == 403
