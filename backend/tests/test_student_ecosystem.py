import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership, OrgType, OrgRole
from app.models.company import Company
from app.models.requirement import JobRequirement, RequirementStatus, WorkMode, EmploymentType
from app.models.candidate import Candidate
from app.models.student_profile import StudentProfile
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)

@pytest.fixture
def test_setup(reset_db_schema):
    from app.core.database import SessionLocal
    db = SessionLocal()

    # Create Student User
    student_user = User(
        email="student@talent.com",
        hashed_password=get_password_hash("StudentPass123!"),
        full_name="Alex Student",
        phone="+919876543210"
    )
    db.add(student_user)
    db.flush()

    # Create Org
    org = Organization(name="Tech Talent Academy", slug="tech-talent-academy", type=OrgType.CONSULTANCY, owner_id=student_user.id)
    db.add(org)
    db.flush()

    # Create Org Membership for Student
    mem = OrganizationMembership(
        organization_id=org.id,
        user_id=student_user.id,
        role=OrgRole.CANDIDATE
    )
    db.add(mem)

    # Create Mentor User
    mentor_user = User(
        email="mentor@talent.com",
        hashed_password=get_password_hash("MentorPass123!"),
        full_name="Prof. Counselor",
        phone="+919876543211"
    )
    db.add(mentor_user)
    db.flush()

    mem_mentor = OrganizationMembership(
        organization_id=org.id,
        user_id=mentor_user.id,
        role=OrgRole.COUNSELOR
    )
    db.add(mem_mentor)

    # Create Company & Requirement
    comp = Company(organization_id=org.id, name="Acme Innovations", location="Pune, India")
    db.add(comp)
    db.flush()

    req = JobRequirement(
        organization_id=org.id,
        company_id=comp.id,
        title="QA Automation Engineer",
        description="Looking for Selenium, Java, and pytest expertise.",
        skills_req="Selenium, Java, Pytest, SQL",
        min_experience_years=0.0,
        max_experience_years=2.0,
        work_mode=WorkMode.REMOTE,
        employment_type=EmploymentType.FULL_TIME,
        status=RequirementStatus.OPEN,
        min_salary=500000.0,
        max_salary=800000.0
    )
    db.add(req)
    db.commit()

    student_token = create_access_token(subject=student_user.id, org_id=org.id, role="CANDIDATE")
    mentor_token = create_access_token(subject=mentor_user.id, org_id=org.id, role="COUNSELOR")

    yield {
        "org_id": org.id,
        "student_user": student_user,
        "mentor_user": mentor_user,
        "requirement_id": req.id,
        "student_headers": {"Authorization": f"Bearer {student_token}"},
        "mentor_headers": {"Authorization": f"Bearer {mentor_token}"}
    }
    db.close()

def test_student_profile_crud_and_completeness(test_setup):
    headers = test_setup["student_headers"]

    # GET Initial Profile
    res = client.get("/api/v1/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Alex Student"
    assert "completeness_score" in data

    # UPDATE Profile
    update_payload = {
        "headline": "QA Automation Lead | Java & Selenium Specialist",
        "career_objective": "Build robust test automation suites.",
        "preferred_roles": "QA Engineer, Automation Engineer",
        "preferred_locations": "Pune, Remote",
        "highest_qualification": "Bachelor of Technology",
        "degree": "B.E. Computer Science",
        "college_university": "Pune University",
        "graduation_year": 2025,
        "programming_languages": "Java, Python",
        "testing_tools": "Selenium, TestNG, Pytest",
        "linkedin_url": "https://linkedin.com/in/alexstudent",
        "city": "Pune"
    }

    res_put = client.put("/api/v1/profile", json=update_payload, headers=headers)
    assert res_put.status_code == 200
    updated_data = res_put.json()
    assert updated_data["headline"] == "QA Automation Lead | Java & Selenium Specialist"
    assert updated_data["completeness_score"] > data["completeness_score"]

def test_account_settings_update(test_setup):
    headers = test_setup["student_headers"]

    payload = {
        "full_name": "Alex Student Updated",
        "phone": "+919988776655"
    }

    res = client.put("/api/v1/profile/settings", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["message"] == "Account settings updated successfully."

    # Verify Profile reflected name change
    res_prof = client.get("/api/v1/profile", headers=headers)
    assert res_prof.json()["full_name"] == "Alex Student Updated"

def test_resume_upload_and_analysis(test_setup):
    headers = test_setup["student_headers"]

    sample_resume_content = (
        "Alex Student\n"
        "Email: student@talent.com | Phone: +919876543210\n"
        "Summary: Skilled Automation Tester with experience in Python, Java, Selenium, Pytest, and MySQL.\n"
        "Education: Bachelor of Technology in Computer Science, Pune University (2025).\n"
        "LinkedIn: https://linkedin.com/in/alexstudent\n"
        "GitHub: https://github.com/alexstudent\n"
    ).encode("utf-8")

    files = {"file": ("Alex_Resume.txt", io.BytesIO(sample_resume_content), "text/plain")}

    res = client.post("/api/v1/resumes/upload", files=files, headers=headers)
    assert res.status_code == 200
    resume_data = res.json()
    assert resume_data["file_name"] == "Alex_Resume.txt"
    assert resume_data["quality_score"] > 60
    assert len(resume_data["strengths"]) > 0

    # Get Analysis
    res_analysis = client.get(f"/api/v1/resumes/{resume_data['id']}/analysis", headers=headers)
    assert res_analysis.status_code == 200
    parsed = res_analysis.json()["parsed_data"]
    assert "Selenium" in parsed["skills"] or "Python" in parsed["skills"]

    # Apply Analysis
    res_apply = client.post(f"/api/v1/resumes/{resume_data['id']}/apply-analysis", json={
        "accept_fields": ["phone", "skills", "education", "linkedin_url"]
    }, headers=headers)
    assert res_apply.status_code == 200

def test_role_matching_and_recommendations(test_setup):
    headers = test_setup["student_headers"]

    # Populate profile skills first
    client.put("/api/v1/profile", json={
        "programming_languages": "Java, Python",
        "testing_tools": "Selenium, Pytest, TestNG",
        "preferred_roles": "QA Automation Engineer",
        "highest_qualification": "B.E. Computer Science"
    }, headers=headers)

    res = client.get("/api/v1/recommendations", headers=headers)
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) >= 1
    top_rec = recs[0]
    assert top_rec["title"] == "QA Automation Engineer"
    assert top_rec["match_score"] >= 70
    assert len(top_rec["matched_skills"]) > 0
    assert len(top_rec["why_matches"]) > 0

    # Save & Dismiss
    res_save = client.post(f"/api/v1/recommendations/{top_rec['id']}/save", headers=headers)
    assert res_save.status_code == 200
    assert res_save.json()["is_saved"] is True

def test_candidate_hr_interaction_and_notification(test_setup):
    headers = test_setup["student_headers"]

    payload = {
        "company_name": "Acme Innovations",
        "hr_name": "Priya Sharma",
        "interaction_type": "CALL",
        "outcome": "RESUME_REQUESTED",
        "notes": "Spoke with Priya regarding QA Automation role. Requested updated resume.",
        "next_move": "Send updated resume via email",
        "due_date": "2026-08-20T10:00:00Z"
    }

    res = client.post("/api/v1/interactions", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["company_name"] == "Acme Innovations"
    assert data["outcome"] == "RESUME_REQUESTED"

    # Check Notification generated
    res_notif = client.get("/api/v1/notifications", headers=headers)
    assert res_notif.status_code == 200
    notif_data = res_notif.json()
    assert notif_data["unread_count"] >= 1
    assert any("Recorded interaction with Priya Sharma" in n["message"] for n in notif_data["notifications"])

def test_mentor_dashboard_and_journey(test_setup):
    # Student initializes profile first
    client.get("/api/v1/profile", headers=test_setup["student_headers"])

    mentor_headers = test_setup["mentor_headers"]
    res_students = client.get("/api/v1/mentor/students", headers=mentor_headers)
    assert res_students.status_code == 200
    data = res_students.json()
    assert data["total_students"] >= 1
    student_obj = data["students"][0]
    assert "completeness_score" in student_obj

    # Get Student Journey
    res_journey = client.get(f"/api/v1/mentor/students/{student_obj['id']}/journey", headers=mentor_headers)
    assert res_journey.status_code == 200
    journey_data = res_journey.json()
    assert "timeline" in journey_data
