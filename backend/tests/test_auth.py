from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.rate_limiter import login_rate_limiter, register_rate_limiter
from app.services.sms_service import otp_rate_limiter
from app.models.user import User, AccountType, AccountStatus
from app.models.mentor_application import MentorApplication, MentorApplicationStatus
from app.core.database import SessionLocal
from app.core.security import get_password_hash

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
    Guarantees demo account login succeeds deterministically with ADMIN role.
    """
    login_rate_limiter._records.clear()
    res = client.post("/api/v1/auth/login", data={
        "username": settings.DEMO_USER_EMAIL,
        "password": settings.DEMO_USER_PASSWORD,
        "selected_role": "admin"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == settings.DEMO_USER_EMAIL
    assert data["user"]["account_type"] == "ADMIN"
    assert data["user"]["is_email_verified"] is True
    assert data["user"]["is_phone_verified"] is True

def test_login_missing_role_error():
    login_rate_limiter._records.clear()
    res = client.post("/api/v1/auth/login", data={
        "username": settings.DEMO_USER_EMAIL,
        "password": settings.DEMO_USER_PASSWORD
    })
    assert res.status_code == 400
    assert "Please select your role" in res.json()["detail"]

def test_login_missing_credentials_error():
    login_rate_limiter._records.clear()
    # Missing password
    res = client.post("/api/v1/auth/login", data={
        "username": "user1@example.com",
        "selected_role": "student"
    })
    assert res.status_code == 400
    assert "Please enter your credentials" in res.json()["detail"]

    # Missing username
    res2 = client.post("/api/v1/auth/login", data={
        "password": "Password123!",
        "selected_role": "student"
    })
    assert res2.status_code == 400
    assert "Please enter your credentials" in res2.json()["detail"]

def test_login_invalid_role_error():
    login_rate_limiter._records.clear()
    res = client.post("/api/v1/auth/login", data={
        "username": "user1@example.com",
        "password": "Password123!",
        "selected_role": "superhero"
    })
    assert res.status_code == 400
    assert "Invalid role selected" in res.json()["detail"]

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
    assert data["user"]["account_type"] == "STUDENT"
    assert data["active_org_id"] > 0

def test_duplicate_registration_fails():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    payload = {
        "full_name": "Test User One",
        "email": "dupuser@example.com",
        "password": "Password123!"
    }
    # First registration
    client.post("/api/v1/auth/register", json=payload)
    # Duplicate registration attempt
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_student_login_success():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    payload = {
        "full_name": "Student Tester",
        "email": "student.tester@example.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", data={
        "username": "student.tester@example.com",
        "password": "Password123!",
        "selected_role": "student"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "student.tester@example.com"
    assert data["user"]["account_type"] == "STUDENT"

def test_student_login_with_json_payload():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    payload = {
        "full_name": "Student JSON",
        "email": "student.json@example.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", json={
        "email": "student.json@example.com",
        "password": "Password123!",
        "selected_role": "student"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "student.json@example.com"

def test_student_login_with_mentor_role_rejected():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    payload = {
        "full_name": "Student Reject",
        "email": "student.reject@example.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", data={
        "username": "student.reject@example.com",
        "password": "Password123!",
        "selected_role": "mentor"
    })
    assert response.status_code == 403
    assert "This account is not registered for the selected role" in response.json()["detail"]

def test_student_login_with_admin_role_rejected():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    payload = {
        "full_name": "Student Reject Two",
        "email": "student.reject2@example.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", data={
        "username": "student.reject2@example.com",
        "password": "Password123!",
        "selected_role": "admin"
    })
    assert response.status_code == 403
    assert "This account is not registered for the selected role" in response.json()["detail"]

def test_mentor_login_and_cross_role_validation():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    # Create approved mentor account
    db = SessionLocal()
    mentor_email = "prof.mentor@example.edu"
    mentor_user = db.query(User).filter(User.email == mentor_email).first()
    if not mentor_user:
        mentor_user = User(
            email=mentor_email,
            hashed_password=get_password_hash("MentorPass123!"),
            full_name="Prof Mentor",
            account_type=AccountType.MENTOR,
            status=AccountStatus.ACTIVE,
            is_active=True,
            is_email_verified=True,
            is_phone_verified=True
        )
        db.add(mentor_user)
        db.commit()
    else:
        mentor_user.account_type = AccountType.MENTOR
        mentor_user.status = AccountStatus.ACTIVE
        mentor_user.is_active = True
        mentor_user.hashed_password = get_password_hash("MentorPass123!")
        db.commit()
    db.close()

    # 1. Mentor logs in with Mentor selected -> SUCCESS
    res_success = client.post("/api/v1/auth/login", data={
        "username": mentor_email,
        "password": "MentorPass123!",
        "selected_role": "mentor"
    })
    assert res_success.status_code == 200
    assert res_success.json()["user"]["account_type"] == "MENTOR"

    # 2. Mentor logs in with Student selected -> REJECTED
    res_as_student = client.post("/api/v1/auth/login", data={
        "username": mentor_email,
        "password": "MentorPass123!",
        "selected_role": "student"
    })
    assert res_as_student.status_code == 403
    assert "This account is not registered for the selected role" in res_as_student.json()["detail"]

    # 3. Mentor logs in with Admin selected -> REJECTED
    res_as_admin = client.post("/api/v1/auth/login", data={
        "username": mentor_email,
        "password": "MentorPass123!",
        "selected_role": "admin"
    })
    assert res_as_admin.status_code == 403
    assert "This account is not registered for the selected role" in res_as_admin.json()["detail"]

def test_admin_cross_role_validation():
    login_rate_limiter._records.clear()

    # 1. Admin selects Student -> REJECTED
    res_student = client.post("/api/v1/auth/login", data={
        "username": settings.DEMO_USER_EMAIL,
        "password": settings.DEMO_USER_PASSWORD,
        "selected_role": "student"
    })
    assert res_student.status_code == 403
    assert "This account is not registered for the selected role" in res_student.json()["detail"]

    # 2. Admin selects Mentor -> REJECTED
    res_mentor = client.post("/api/v1/auth/login", data={
        "username": settings.DEMO_USER_EMAIL,
        "password": settings.DEMO_USER_PASSWORD,
        "selected_role": "mentor"
    })
    assert res_mentor.status_code == 403
    assert "This account is not registered for the selected role" in res_mentor.json()["detail"]

def test_login_invalid_password():
    login_rate_limiter._records.clear()
    register_rate_limiter._records.clear()

    payload = {
        "full_name": "Test User One",
        "email": "pwd.check@example.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", data={
        "username": "pwd.check@example.com",
        "password": "WrongPassword",
        "selected_role": "student"
    })
    assert response.status_code == 401
    assert "The email address or password you entered is incorrect" in response.json()["detail"]

def test_login_nonexistent_user():
    login_rate_limiter._records.clear()

    response = client.post("/api/v1/auth/login", data={
        "username": "nonexistent@example.com",
        "password": "Password123!",
        "selected_role": "student"
    })
    assert response.status_code == 401
    assert "The email address or password you entered is incorrect" in response.json()["detail"]

def test_disabled_account_login_rejected():
    login_rate_limiter._records.clear()

    db = SessionLocal()
    disabled_email = "disabled.user@example.com"
    disabled_user = db.query(User).filter(User.email == disabled_email).first()
    if not disabled_user:
        disabled_user = User(
            email=disabled_email,
            hashed_password=get_password_hash("Password123!"),
            full_name="Disabled User",
            account_type=AccountType.STUDENT,
            status=AccountStatus.SUSPENDED,
            is_active=False
        )
        db.add(disabled_user)
        db.commit()
    else:
        disabled_user.is_active = False
        disabled_user.status = AccountStatus.SUSPENDED
        db.commit()
    db.close()

    res = client.post("/api/v1/auth/login", data={
        "username": disabled_email,
        "password": "Password123!",
        "selected_role": "student"
    })
    assert res.status_code == 403
    assert "Your account has been disabled" in res.json()["detail"]

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
