from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.rate_limiter import login_rate_limiter, register_rate_limiter
from app.services.sms_service import otp_rate_limiter

client = TestClient(app)

def test_auth_config_endpoint():
    res = client.get("/api/v1/auth/config")
    assert res.status_code == 200
    data = res.json()
    assert "demo_mode" in data
    assert data["demo_mode"] is True
    assert data["demo_email"] == settings.DEMO_USER_EMAIL
    assert data["demo_password"] == settings.DEMO_USER_PASSWORD

def test_demo_user_deterministic_login():
    """
    Guarantees demo account login always succeeds deterministically without manual setup.
    """
    res = client.post("/api/v1/auth/login", data={
        "username": settings.DEMO_USER_EMAIL,
        "password": settings.DEMO_USER_PASSWORD
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == settings.DEMO_USER_EMAIL
    assert data["user"]["is_email_verified"] is True
    assert data["user"]["is_phone_verified"] is True

def test_user_registration_and_personal_workspace():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    payload = {
        "full_name": "Test User One",
        "email": "user1@example.com",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "user1@example.com"
    assert data["active_org_id"] > 0

def test_duplicate_registration_fails():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    payload = {
        "full_name": "Test User One",
        "email": "user1@example.com",
        "password": "Password123!"
    }
    # First registration
    client.post("/api/v1/auth/register", json=payload)
    # Duplicate registration attempt
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_login_success():
    login_rate_limiter._records.clear()

    payload = {
        "full_name": "Test User One",
        "email": "user1@example.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", data={"username": "user1@example.com", "password": "Password123!"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "user1@example.com"

def test_login_invalid_password():
    login_rate_limiter._records.clear()

    payload = {
        "full_name": "Test User One",
        "email": "user1@example.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", data={"username": "user1@example.com", "password": "WrongPassword"})
    assert response.status_code == 401
    assert "Incorrect password" in response.json()["detail"]

def test_login_nonexistent_user():
    login_rate_limiter._records.clear()

    response = client.post("/api/v1/auth/login", data={"username": "nonexistent@example.com", "password": "Password123!"})
    assert response.status_code == 401
    assert "No account found" in response.json()["detail"]

def test_login_rate_limiting():
    login_rate_limiter._records.clear()

    key = "203.0.113.195:ratelimit_user@example.com"
    for _ in range(15):
        assert login_rate_limiter.is_rate_limited(key) is False

    assert login_rate_limiter.is_rate_limited(key) is True
    login_rate_limiter._records.clear()

def test_email_and_mobile_verification_flow():
    # 1. Register new user
    reg = client.post("/api/v1/auth/register", json={
        "full_name": "Rohan Verma",
        "email": "rohan.verification@example.com",
        "password": "Password123!",
        "phone": "+91 9359345433"
    })
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check profile verification initial state
    prof = client.get("/api/v1/profile", headers=headers)
    assert prof.status_code == 200

    # 3. Request email verification
    ver_req = client.post("/api/v1/auth/verify-email/request", headers=headers)
    assert ver_req.status_code == 200
    ver_link = ver_req.json().get("verification_link")
    assert ver_link is not None
    token_extracted = ver_link.split("token=")[1]

    # Confirm email
    confirm_email = client.post("/api/v1/auth/verify-email/confirm", json={"token": token_extracted})
    assert confirm_email.status_code == 200
    assert confirm_email.json()["is_verified"] is True

    # 4. Request Phone OTP
    otp_rate_limiter.clear()
    otp_req = client.post("/api/v1/auth/verify-phone/request-otp", headers=headers, json={"phone": "+91 9359345433"})
    assert otp_req.status_code == 200
    dev_otp = otp_req.json()["dev_otp"]
    assert dev_otp is not None

    # 5. Confirm Phone OTP
    confirm_res = client.post("/api/v1/auth/verify-phone/confirm-otp", headers=headers, json={"phone": "+91 9359345433", "otp": dev_otp})
    assert confirm_res.status_code == 200
    assert confirm_res.json()["is_verified"] is True
