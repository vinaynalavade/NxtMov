import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_strict_multi_tenant_data_isolation():
    uid = uuid.uuid4().hex[:6]
    # 1. Bootstrap Admin User A in Tenant A
    user_a_res = client.post("/api/v1/auth/admin/bootstrap", json={
        "bootstrap_key": settings.ADMIN_BOOTSTRAP_SECRET,
        "full_name": "User Alpha Admin",
        "email": f"user_a_{uid}@tenant.com",
        "password": "Password123!"
    }).json()
    token_a = user_a_res["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Bootstrap Admin User B in Tenant B
    user_b_res = client.post("/api/v1/auth/admin/bootstrap", json={
        "bootstrap_key": settings.ADMIN_BOOTSTRAP_SECRET,
        "full_name": "User Beta Admin",
        "email": f"user_b_{uid}@tenant.com",
        "password": "Password123!"
    }).json()
    token_b = user_b_res["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates a company and contact in Tenant A
    company_a = client.post("/api/v1/companies", json={
        "name": "Secret Enterprise A",
        "industry": "Defense Technology"
    }, headers=headers_a).json()
    company_a_id = company_a["id"]

    res_contact_a = client.post("/api/v1/contacts", json={
        "name": "Confidential Executive A",
        "company_id": company_a_id,
        "email": "exec@secreta.com"
    }, headers=headers_a)
    assert res_contact_a.status_code == 201, f"Contact creation failed: {res_contact_a.text}"
    contact_a = res_contact_a.json()
    contact_a_id = contact_a["id"]

    # 4. User B attempts to access Tenant A's company -> MUST FAIL (404)
    get_comp_b = client.get(f"/api/v1/companies/{company_a_id}", headers=headers_b)
    assert get_comp_b.status_code == 404

    # 5. User B lists companies -> MUST NOT return Tenant A's company
    list_comp_b = client.get("/api/v1/companies", headers=headers_b)
    assert list_comp_b.status_code == 200
    b_companies = list_comp_b.json()
    assert all(c["id"] != company_a_id for c in b_companies)

    # 6. User B attempts to access Tenant A's contact -> MUST FAIL (404)
    get_cont_b = client.get(f"/api/v1/contacts/{contact_a_id}", headers=headers_b)
    assert get_cont_b.status_code == 404

    # 7. User B attempts to log call against Tenant A's contact -> MUST FAIL (404)
    log_call_b = client.post("/api/v1/activity/calls", json={
        "contact_id": contact_a_id,
        "notes": "Attempting cross-tenant data leak"
    }, headers=headers_b)
    assert log_call_b.status_code == 404
