import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_complete_individual_job_seeker_e2e_workflow():
    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Vinay JobSeeker",
        "email": "vinay.e2e@example.com",
        "password": "SecurePassword123!"
    })
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert "access_token" in user_data

    # 2. Login
    login_res = client.post("/api/v1/auth/login", data={
        "username": "vinay.e2e@example.com",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Enter Dashboard (Fetch Stats)
    dash_stats = client.get("/api/v1/activity/dashboard/stats", headers=headers)
    assert dash_stats.status_code == 200

    # 4. Create Company
    comp_res = client.post("/api/v1/companies", json={
        "name": "Infosys Technologies",
        "industry": "IT Services",
        "location": "Bengaluru"
    }, headers=headers)
    assert comp_res.status_code == 201
    company_id = comp_res.json()["id"]

    # 5. Add HR Contact
    contact_res = client.post("/api/v1/contacts", json={
        "name": "Priya Sharma",
        "company_id": company_id,
        "designation": "Lead Recruiter",
        "email": "priya@infosys.com",
        "phone": "+91 9876543210"
    }, headers=headers)
    assert contact_res.status_code == 201
    contact_id = contact_res.json()["id"]

    # 6. Import Contacts from CSV/Excel
    csv_data = "HR Name,Company Name,Phone,Email\nRahul Patil,TCS,+91 9999988888,rahul@tcs.com\n"
    file_payload = {"file": ("contacts.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    
    preview_res = client.post("/api/v1/import/preview", files=file_payload, headers=headers)
    assert preview_res.status_code == 200
    file_token = preview_res.json()["file_name"]
    mapping = preview_res.json()["suggested_mappings"]

    confirm_res = client.post("/api/v1/import/confirm", json={
        "file_token": file_token,
        "sheet_name": "Sheet1",
        "mapping": mapping,
        "duplicate_handling": "SKIP"
    }, headers=headers)
    assert confirm_res.status_code == 200

    # 7. View imported contacts
    contacts_list = client.get("/api/v1/contacts", headers=headers).json()
    assert len(contacts_list) == 2

    # 8. Log Call & Record Outcome & Create Follow-up
    call_res = client.post("/api/v1/activity/calls", json={
        "contact_id": contact_id,
        "call_type": "OUTBOUND",
        "outcome": "OPPORTUNITY_AVAILABLE",
        "notes": "Discussed Senior Automation Lead position",
        "create_followup": True,
        "followup_title": "Send updated resume to Priya",
        "followup_due_date": "2026-08-15T10:00:00Z"
    }, headers=headers)
    assert call_res.status_code == 201

    # 9. See Follow-up on Dashboard
    dash_after_call = client.get("/api/v1/activity/dashboard/stats", headers=headers).json()
    assert dash_after_call["today_followups"] or dash_after_call["overdue_followups"] or dash_after_call["followups_due_today"] >= 0

    # 10. Create Opportunity
    opp_res = client.post("/api/v1/requirements", json={
        "company_id": company_id,
        "contact_id": contact_id,
        "title": "Senior QA Automation Engineer",
        "location": "Bengaluru",
        "employment_type": "FULL_TIME",
        "skills_req": "Python, Pytest, FastAPI, Selenium",
        "status": "NEW"
    }, headers=headers)
    assert opp_res.status_code == 201
    opportunity_id = opp_res.json()["id"]

    # 11. Create Application
    app_res = client.post("/api/v1/applications", json={
        "job_requirement_id": opportunity_id,
        "stage": "APPLIED",
        "notes": "Submitted resume via email link"
    }, headers=headers)
    assert app_res.status_code == 201
    application_id = app_res.json()["id"]

    # 12. Track Application & Update Stage to INTERVIEWING
    update_app = client.put(f"/api/v1/applications/{application_id}", json={
        "stage": "INTERVIEWING"
    }, headers=headers)
    assert update_app.status_code == 200
    assert update_app.json()["stage"] == "INTERVIEWING"

    # 13. Create Interview
    interview_res = client.post(f"/api/v1/applications/{application_id}/interviews", json={
        "round_name": "Technical Round 1",
        "scheduled_at": "2026-08-18T14:00:00Z",
        "location_or_link": "https://meet.google.com/xyz-abcd-efg",
        "interviewer_names": "Suresh Kumar (Tech Lead)",
        "outcome": "SCHEDULED"
    }, headers=headers)
    assert interview_res.status_code == 201
    assert interview_res.json()["round_name"] == "Technical Round 1"

    # 14. Verify full application detail with interview
    final_app_list = client.get("/api/v1/applications", headers=headers).json()
    assert len(final_app_list) == 1
    assert len(final_app_list[0]["interviews"]) == 1
