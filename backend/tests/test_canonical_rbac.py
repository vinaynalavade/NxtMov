import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import Base, engine, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, AccountType
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
            account_type=AccountType.ADMIN,
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
            data={"username": multi_email, "password": "TestPass123!", "selected_role": "admin"}
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

    def test_mentor_application_approval_and_notification_regression(self, db_session):
        from app.models.notification import Notification
        from app.models.mentor_application import MentorApplication, MentorApplicationStatus
        from app.core.rate_limiter import register_rate_limiter, login_rate_limiter
        register_rate_limiter._records.clear()
        login_rate_limiter._records.clear()

        # 1. Admin setup
        admin_user, admin_org, _ = create_test_user_and_org(db_session, "admin_approver", OrgRole.ADMIN, "Admin Approver Org")
        admin_user.account_type = AccountType.ADMIN
        db_session.commit()
        admin_headers = get_auth_headers(admin_user, admin_org, OrgRole.ADMIN)

        # 2. Submit Mentor Application
        mentor_email = f"prof_mentor_{uuid.uuid4().hex[:6]}@univ.ac.in"
        apply_res = client.post("/api/v1/auth/apply-mentor", json={
            "full_name": "Professor Mentor",
            "official_email": mentor_email,
            "password": "SecurePassword123!",
            "phone": "+91 9876543210",
            "institute_name": "Indian Institute of Science",
            "employee_id": "IIS-FAC-2026",
            "department": "Computer Science",
            "designation": "Professor"
        })
        assert apply_res.status_code == 200
        app_id = apply_res.json()["application_id"]

        # 3. Verify user is PENDING prior to approval
        pending_user = db_session.query(User).filter(User.email == mentor_email).first()
        assert pending_user is not None
        assert pending_user.account_type == AccountType.MENTOR
        assert pending_user.status.value == "PENDING"
        assert pending_user.is_active is False

        # Attempt login before approval -> 403
        unapproved_login = client.post("/api/v1/auth/login", data={
            "username": mentor_email,
            "password": "SecurePassword123!",
            "selected_role": "mentor"
        })
        assert unapproved_login.status_code == 403
        assert "Your mentor application is currently under review" in unapproved_login.json()["detail"]

        # 4. Admin Approves Mentor Application
        approve_res = client.post(f"/api/v1/admin/mentor-applications/{app_id}/approve", headers=admin_headers)
        assert approve_res.status_code == 200
        approved_app = approve_res.json()
        assert approved_app["status"] == "APPROVED"

        # 5. Verify database state after approval
        db_session.expire_all()
        approved_user = db_session.query(User).filter(User.email == mentor_email).first()
        assert approved_user.status.value == "ACTIVE"
        assert approved_user.is_active is True
        assert approved_user.is_email_verified is True

        mentor_org = db_session.query(Organization).filter(
            Organization.owner_id == approved_user.id,
            Organization.type == OrgType.CONSULTANCY
        ).first()
        assert mentor_org is not None, "Mentor workspace organization must be provisioned"

        mentor_membership = db_session.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == approved_user.id,
            OrganizationMembership.organization_id == mentor_org.id
        ).first()
        assert mentor_membership is not None
        assert mentor_membership.role == OrgRole.MENTOR

        # 6. Verify Notification with non-null organization_id
        notif = db_session.query(Notification).filter(
            Notification.user_id == approved_user.id,
            Notification.title == "Mentor Application Approved!"
        ).first()
        assert notif is not None, "Approval notification must be created"
        assert notif.organization_id is not None, "Notification organization_id must NOT be None"
        assert notif.organization_id == mentor_org.id, "Notification organization_id must match mentor's workspace organization"
        assert notif.notification_type == "INFO"

        # 7. Mentor logs in after approval
        approved_login = client.post("/api/v1/auth/login", data={
            "username": mentor_email,
            "password": "SecurePassword123!",
            "selected_role": "mentor"
        })
        assert approved_login.status_code == 200
        login_data = approved_login.json()
        assert "access_token" in login_data
        assert login_data["user"]["account_type"] == "MENTOR"
        assert login_data["active_org_id"] == mentor_org.id
        assert login_data["user"]["active_organization"]["role"] == "MENTOR"

        # 8. Fetch notifications as logged-in mentor
        mentor_token = login_data["access_token"]
        notif_res = client.get("/api/v1/notifications", headers={"Authorization": f"Bearer {mentor_token}"})
        assert notif_res.status_code == 200
        notifs = notif_res.json()["notifications"]
        assert any(n["title"] == "Mentor Application Approved!" for n in notifs)

    def test_mentor_approval_error_message_is_not_misleading(self, db_session):
        admin_user, admin_org, _ = create_test_user_and_org(db_session, "admin_err_check", OrgRole.ADMIN, "Admin Org")
        admin_user.account_type = AccountType.ADMIN
        db_session.commit()
        admin_headers = get_auth_headers(admin_user, admin_org, OrgRole.ADMIN)

        # 1. Non-existent application
        res_404 = client.post("/api/v1/admin/mentor-applications/9999999/approve", headers=admin_headers)
        assert res_404.status_code == 404
        detail_404 = res_404.json()["detail"]
        assert "Mentor application not found" in detail_404
        assert "Resume processing" not in detail_404

        # 2. Non-admin forbidden
        student_user, student_org, _ = create_test_user_and_org(db_session, "student_err_check", OrgRole.STUDENT, "Student Org")
        student_headers = get_auth_headers(student_user, student_org, OrgRole.STUDENT)
        res_403 = client.post("/api/v1/admin/mentor-applications/1/approve", headers=student_headers)
        assert res_403.status_code == 403
        assert "Resume processing" not in res_403.json().get("detail", "")

    def test_admin_student_resume_and_application_counts(self, db_session):
        from app.models.resume import Resume
        from app.models.application import Application, ApplicationStage
        from app.models.candidate import Candidate, CandidateStatus

        # 1. Setup admin
        admin_user, admin_org, _ = create_test_user_and_org(db_session, "admin_counter", OrgRole.ADMIN, "Admin Count Org")
        admin_user.account_type = AccountType.ADMIN
        db_session.commit()
        admin_headers = get_auth_headers(admin_user, admin_org, OrgRole.ADMIN)

        # 2. Setup student with Candidate record and Resume
        student_email = f"student_count_{uuid.uuid4().hex[:6]}@example.com"
        student_user = User(
            email=student_email,
            full_name="Counting Student",
            hashed_password=get_password_hash("Password123!"),
            account_type=AccountType.STUDENT,
            is_active=True
        )
        db_session.add(student_user)
        db_session.flush()

        candidate = Candidate(
            organization_id=admin_org.id,
            user_id=student_user.id,
            full_name=student_user.full_name,
            email=student_user.email,
            status=CandidateStatus.NEW
        )
        db_session.add(candidate)
        db_session.flush()

        resume = Resume(
            organization_id=admin_org.id,
            candidate_id=candidate.id,
            file_name="Student_Resume.pdf",
            file_type="application/pdf",
            file_url="/uploads/resumes/dummy.pdf",
            file_size_bytes=1024,
            is_current=True
        )
        db_session.add(resume)
        db_session.commit()

        # 3. Query Admin Students Endpoint
        res = client.get("/api/v1/admin/students", headers=admin_headers)
        assert res.status_code == 200
        students_list = res.json()
        target_student = next((s for s in students_list if s["id"] == student_user.id), None)
        assert target_student is not None
        assert target_student["resumes_count"] >= 1, "Resume count must reflect actual linked resumes"

    def test_rejected_mentor_login_message(self, db_session):
        from app.models.mentor_application import MentorApplication, MentorApplicationStatus
        from app.core.rate_limiter import login_rate_limiter, register_rate_limiter
        login_rate_limiter._records.clear()
        register_rate_limiter._records.clear()

        # 1. Admin setup
        admin_user, admin_org, _ = create_test_user_and_org(db_session, "admin_rejector", OrgRole.ADMIN, "Admin Reject Org")
        admin_user.account_type = AccountType.ADMIN
        db_session.commit()
        admin_headers = get_auth_headers(admin_user, admin_org, OrgRole.ADMIN)

        # 2. Submit Mentor Application
        mentor_email = f"prof_reject_{uuid.uuid4().hex[:6]}@univ.edu"
        apply_res = client.post("/api/v1/auth/apply-mentor", json={
            "full_name": "Rejected Mentor",
            "official_email": mentor_email,
            "password": "Password123!",
            "phone": "+91 9123456780",
            "institute_name": "Test Institute",
            "employee_id": "REJ-101",
            "department": "Physics",
            "designation": "Lecturer"
        })
        assert apply_res.status_code == 200
        app_id = apply_res.json()["application_id"]

        # 3. Admin Rejects Mentor Application
        reject_res = client.post(
            f"/api/v1/admin/mentor-applications/{app_id}/reject",
            headers=admin_headers,
            json={"rejection_reason": "Incomplete institutional credentials"}
        )
        assert reject_res.status_code == 200

        # 4. Mentor Login attempt after rejection
        login_res = client.post("/api/v1/auth/login", data={
            "username": mentor_email,
            "password": "Password123!",
            "selected_role": "mentor"
        })
        assert login_res.status_code == 403
        detail = login_res.json()["detail"]
        assert "Your mentor application was not approved" in detail
        assert "Incomplete institutional credentials" in detail

    def test_password_reset_flow_with_valid_and_expired_tokens(self, db_session):
        # 1. Create user
        reset_email = f"reset_user_{uuid.uuid4().hex[:6]}@example.com"
        user = User(
            email=reset_email,
            full_name="Reset User",
            hashed_password=get_password_hash("OldPassword123!"),
            account_type=AccountType.STUDENT,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # 2. Request forgot password
        forgot_res = client.post("/api/v1/auth/forgot-password", json={"email": reset_email})
        assert forgot_res.status_code == 200
        assert "password reset link has been sent" in forgot_res.json()["message"]

        # 3. Retrieve generated token from DB
        db_session.expire_all()
        user_db = db_session.query(User).filter(User.email == reset_email).first()
        assert user_db.password_reset_token is not None
        token_val = user_db.password_reset_token.split(":")[0]

        # 4. Perform Reset with valid token
        reset_res = client.post("/api/v1/auth/reset-password", json={
            "token": token_val,
            "new_password": "NewPassword123!"
        })
        assert reset_res.status_code == 200
        assert "Password updated successfully" in reset_res.json()["message"]

        # 5. Verify login with new password
        login_new = client.post("/api/v1/auth/login", data={
            "username": reset_email,
            "password": "NewPassword123!",
            "selected_role": "student"
        })
        assert login_new.status_code == 200

        # 6. Attempt reset with already used / invalid token -> 400
        invalid_reset = client.post("/api/v1/auth/reset-password", json={
            "token": token_val,
            "new_password": "AnotherPassword123!"
        })
        assert invalid_reset.status_code == 400
        assert "invalid or has expired" in invalid_reset.json()["detail"]

