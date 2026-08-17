from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def get_auth_header():
    # Bootstrap temporary admin user for CRM management
    email = "crmuser@example.com"
    boot = client.post("/api/v1/auth/admin/bootstrap", json={
        "bootstrap_key": settings.ADMIN_BOOTSTRAP_SECRET,
        "full_name": "CRM Admin User",
        "email": email,
        "password": "Password123!"
    })
    token = boot.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_company_and_contact_crud():
    headers = get_auth_header()

    # 1. Create Company
    comp_res = client.post("/api/v1/companies", json={
        "name": "Infosys",
        "industry": "IT Services",
        "location": "Bengaluru"
    }, headers=headers)
    assert comp_res.status_code == 201
    comp_data = comp_res.json()
    assert comp_data["name"] == "Infosys"
    company_id = comp_data["id"]

    # 2. Create HR Contact
    contact_res = client.post("/api/v1/contacts", json={
        "name": "Priya Sharma",
        "company_id": company_id,
        "designation": "Technical Recruiter",
        "email": "priya@infosys.com",
        "phone": "+91 9876543210"
    }, headers=headers)
    assert contact_res.status_code == 201
    contact_data = contact_res.json()
    assert contact_data["name"] == "Priya Sharma"
    assert contact_data["company"]["name"] == "Infosys"

    # 3. List Companies & Contacts
    list_comp = client.get("/api/v1/companies?search=Infosys", headers=headers)
    assert list_comp.status_code == 200
    assert len(list_comp.json()) == 1

    list_cont = client.get("/api/v1/contacts?search=Priya", headers=headers)
    assert list_cont.status_code == 200
    assert len(list_cont.json()) == 1
