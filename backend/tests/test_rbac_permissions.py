from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_rbac_and_cross_workspace_isolation():
    # User A creates Consultancy A
    user_a = client.post("/api/v1/auth/register", json={
        "full_name": "User A Admin",
        "email": "usera@agencya.com",
        "password": "Password123!"
    })
    token_a = user_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    org_a = client.post("/api/v1/organizations", json={"name": "Agency A", "type": "CONSULTANCY"}, headers=headers_a).json()
    org_a_id = org_a["id"]

    switch_a = client.post(f"/api/v1/auth/switch?organization_id={org_a_id}", headers=headers_a)
    headers_org_a = {"Authorization": f"Bearer {switch_a.json()['access_token']}"}

    # Add Candidate in Agency A
    cand_a = client.post("/api/v1/candidates", json={
        "full_name": "Secret Candidate A",
        "email": "cand_a@agencya.com"
    }, headers=headers_org_a).json()
    cand_a_id = cand_a["id"]

    # User B creates Consultancy B
    user_b = client.post("/api/v1/auth/register", json={
        "full_name": "User B Admin",
        "email": "userb@agencyb.com",
        "password": "Password123!"
    })
    token_b = user_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    org_b = client.post("/api/v1/organizations", json={"name": "Agency B", "type": "CONSULTANCY"}, headers=headers_b).json()
    org_b_id = org_b["id"]

    switch_b = client.post(f"/api/v1/auth/switch?organization_id={org_b_id}", headers=headers_b)
    headers_org_b = {"Authorization": f"Bearer {switch_b.json()['access_token']}"}

    # 1. User B cannot access Candidate A in Agency A
    get_res = client.get(f"/api/v1/candidates/{cand_a_id}", headers=headers_org_b)
    assert get_res.status_code == 404

    # 2. User B cannot list Candidate A in Agency B's candidate list
    list_res = client.get("/api/v1/candidates", headers=headers_org_b).json()
    cand_ids = [c["id"] for c in list_res]
    assert cand_a_id not in cand_ids

    # 3. User B cannot invite users into Agency A
    inv_res = client.post("/api/v1/organizations/invitations", json={
        "email": "attacker@outside.com",
        "role": "ADMIN"
    }, headers=headers_org_b)
    assert inv_res.status_code == 201
    inv_org_id = inv_res.json()["organization_id"]
    assert inv_org_id == org_b_id
    assert inv_org_id != org_a_id

    # 4. User A switching back to Personal Workspace cannot see Agency A candidates in Personal context
    personal_a_id = user_a.json()["active_org_id"]
    switch_personal = client.post(f"/api/v1/auth/switch?organization_id={personal_a_id}", headers=headers_a)
    headers_personal_a = {"Authorization": f"Bearer {switch_personal.json()['access_token']}"}

    personal_candidates = client.get("/api/v1/candidates", headers=headers_personal_a).json()
    personal_cand_ids = [c["id"] for c in personal_candidates if c["email"] == "cand_a@agencya.com"]
    assert len(personal_cand_ids) == 0
