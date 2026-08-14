import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_consultancy_end_to_end_workflow(reset_db_schema):
    # 1. Register Admin User
    admin_reg = client.post("/api/v1/auth/register", json={
        "full_name": "Agency Admin",
        "email": "admin@apexrecruitment.com",
        "password": "SecurePassword123!"
    })
    assert admin_reg.status_code == 201
    admin_token = admin_reg.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Consultancy Workspace
    create_org = client.post("/api/v1/organizations", json={
        "name": "Apex Recruitment Partners",
        "type": "CONSULTANCY",
        "phone": "+91 80 1234 5678",
        "website": "https://apexrecruitment.com",
        "location": "Bengaluru"
    }, headers=admin_headers)
    assert create_org.status_code == 201
    consultancy_id = create_org.json()["id"]

    # Switch Admin Token to Consultancy Workspace
    switch_res = client.post(f"/api/v1/auth/switch?organization_id={consultancy_id}", headers=admin_headers)
    assert switch_res.status_code == 200
    consultancy_token = switch_res.json()["access_token"]
    c_headers = {"Authorization": f"Bearer {consultancy_token}"}

    # 3. Invite Recruiter Team Member
    inv_res = client.post("/api/v1/organizations/invitations", json={
        "email": "recruiter@apexrecruitment.com",
        "role": "RECRUITER"
    }, headers=c_headers)
    assert inv_res.status_code == 201
    inv_token = inv_res.json()["token"]

    # Recruiter Registers & Accepts Invitation
    rec_reg = client.post("/api/v1/auth/register", json={
        "full_name": "Senior Recruiter Rahul",
        "email": "recruiter@apexrecruitment.com",
        "password": "RecruiterPass123!"
    })
    assert rec_reg.status_code == 201
    rec_token = rec_reg.json()["access_token"]
    rec_headers = {"Authorization": f"Bearer {rec_token}"}

    accept_res = client.post("/api/v1/organizations/invitations/accept", json={"token": inv_token}, headers=rec_headers)
    assert accept_res.status_code == 200

    # Switch Recruiter Token to Consultancy
    rec_switch = client.post(f"/api/v1/auth/switch?organization_id={consultancy_id}", headers=rec_headers)
    assert rec_switch.status_code == 200
    rec_c_headers = {"Authorization": f"Bearer {rec_switch.json()['access_token']}"}

    # 4. Create Company & Contact
    comp_res = client.post("/api/v1/companies", json={
        "name": "Acme Technologies",
        "industry": "Software",
        "location": "Bengaluru"
    }, headers=rec_c_headers)
    company_id = comp_res.json()["id"]

    contact_res = client.post("/api/v1/contacts", json={
        "name": "Suresh VicePresident",
        "company_id": company_id,
        "email": "suresh@acme.com",
        "phone": "+91 9988776655"
    }, headers=rec_c_headers)
    contact_id = contact_res.json()["id"]

    # 5. Create Job Requirement / Opening
    req_res = client.post("/api/v1/requirements", json={
        "company_id": company_id,
        "contact_id": contact_id,
        "title": "Senior Python Backend Engineer",
        "location": "Bengaluru",
        "employment_type": "FULL_TIME",
        "min_experience_years": 3.0,
        "max_experience_years": 8.0,
        "skills_req": "Python, FastAPI, PostgreSQL, Docker",
        "max_salary": 2200000.0,
        "status": "OPEN"
    }, headers=rec_c_headers)
    assert req_res.status_code == 201
    req_id = req_res.json()["id"]

    # 6. Create Managed Candidate
    cand_res = client.post("/api/v1/candidates", json={
        "full_name": "Ananya Sharma",
        "email": "ananya.sharma@example.com",
        "phone": "+91 9876500011",
        "location": "Bengaluru",
        "current_title": "Python Developer",
        "experience_years": 4.5,
        "primary_skills": "Python, FastAPI, Docker, Pytest",
        "expected_salary": 1800000.0,
        "status": "READY"
    }, headers=rec_c_headers)
    assert cand_res.status_code == 201
    cand_id = cand_res.json()["id"]

    # 7. Candidate Matching Engine Test
    matches_res = client.get(f"/api/v1/requirements/{req_id}/matches", headers=rec_c_headers)
    assert matches_res.status_code == 200
    matches = matches_res.json()
    assert len(matches) >= 1
    top_match = matches[0]
    assert top_match["match_score"] > 70.0
    assert top_match["score_label"] == "NxtMov Match Score"
    assert len(top_match["pros"]) >= 1

    # 8. Submit Candidate to Requirement
    sub_res = client.post("/api/v1/submissions", json={
        "job_requirement_id": req_id,
        "candidate_id": cand_id,
        "notes": "Top matched candidate with 4.5 yrs FastAPI experience"
    }, headers=rec_c_headers)
    assert sub_res.status_code == 201
    sub_id = sub_res.json()["id"]

    # Update Submission Stage to INTERVIEW
    update_sub = client.put(f"/api/v1/submissions/{sub_id}", json={
        "status": "INTERVIEW",
        "client_feedback": "HR shortlisted candidate for Round 1"
    }, headers=rec_c_headers)
    assert update_sub.status_code == 200
    assert update_sub.json()["status"] == "INTERVIEW"

    # 9. Record Confirmed Placement
    place_res = client.post("/api/v1/placements", json={
        "candidate_id": cand_id,
        "company_id": company_id,
        "job_requirement_id": req_id,
        "join_date": "2026-09-01",
        "offered_salary": 1900000.0,
        "billing_amount": 150000.0,
        "status": "CONFIRMED"
    }, headers=rec_c_headers)
    assert place_res.status_code == 201
    assert place_res.json()["candidate_name"] == "Ananya Sharma"

    # 10. Test Candidate Spreadsheet Import
    csv_candidates = (
        "Student Name,Email,Mobile,Technical Skills,Total Exp,Current Company\n"
        "Vikram Rao,vikram@example.com,+91 9999000011,Java / Spring,5.0,Infosys\n"
        "Divya Nair,divya@example.com,+91 9999000022,React / JavaScript,3.0,Wipro\n"
    )
    files = {"file": ("students.csv", io.BytesIO(csv_candidates.encode("utf-8")), "text/csv")}

    preview_res = client.post("/api/v1/import/preview?import_type=CANDIDATES", files=files, headers=rec_c_headers)
    assert preview_res.status_code == 200
    file_token = preview_res.json()["file_name"]
    mapping = preview_res.json()["suggested_mappings"]

    confirm_res = client.post("/api/v1/import/confirm", json={
        "file_token": file_token,
        "import_type": "CANDIDATES",
        "sheet_name": "Sheet1",
        "mapping": mapping,
        "duplicate_handling": "SKIP"
    }, headers=rec_c_headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["imported_candidates_count"] == 2

    # 11. Verify Dashboard Consultancy Metrics
    dash_stats = client.get("/api/v1/activity/dashboard/stats", headers=rec_c_headers).json()
    assert dash_stats["org_type"] == "CONSULTANCY"
    assert dash_stats["active_candidates"] >= 3
    assert dash_stats["placements_count"] == 1
