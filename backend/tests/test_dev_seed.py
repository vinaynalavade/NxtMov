from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_development_seed_generator():
    # Bootstrap Admin user
    boot = client.post("/api/v1/auth/admin/bootstrap", json={
        "bootstrap_key": settings.ADMIN_BOOTSTRAP_SECRET,
        "full_name": "Seed Admin User",
        "email": "seed.test@example.com",
        "password": "Password123!"
    })
    token = boot.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate Seed Data
    seed_res = client.post("/api/v1/dev/seed", headers=headers)
    assert seed_res.status_code == 200
    data = seed_res.json()
    assert data["companies_created"] >= 20
    assert data["contacts_created"] >= 40

    # Verify Dashboard Stats under realistic volume
    stats = client.get("/api/v1/activity/dashboard/stats", headers=headers).json()
    assert stats["active_opportunities"] > 0
    assert stats["followups_due_today"] >= 0
