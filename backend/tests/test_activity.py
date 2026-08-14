from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_header():
    email = "actuser@example.com"
    reg = client.post("/api/v1/auth/register", json={
        "full_name": "Activity User",
        "email": email,
        "password": "Password123!"
    })
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_log_call_and_create_followup():
    headers = get_auth_header()

    # Create contact
    contact = client.post("/api/v1/contacts", json={"name": "Rahul Patil", "phone": "+91 9999988888"}, headers=headers).json()

    due_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    # Log call
    call_res = client.post("/api/v1/activity/calls", json={
        "contact_id": contact["id"],
        "call_type": "OUTBOUND",
        "outcome": "OPPORTUNITY_AVAILABLE",
        "notes": "Discussed automation engineer role",
        "create_followup": True,
        "followup_title": "Follow up with Rahul",
        "followup_due_date": due_date
    }, headers=headers)

    assert call_res.status_code == 201
    call_data = call_res.json()
    assert call_data["notes"] == "Discussed automation engineer role"

    # Verify contact status auto-updated
    updated_contact = client.get(f"/api/v1/contacts/{contact['id']}", headers=headers).json()
    assert updated_contact["status"] == "OPPORTUNITY_AVAILABLE"

    # Verify dashboard stats
    stats = client.get("/api/v1/activity/dashboard/stats", headers=headers).json()
    assert "followups_due_today" in stats
    assert "active_opportunities" in stats
