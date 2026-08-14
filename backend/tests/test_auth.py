from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_registration_and_personal_workspace():
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

def test_login_success():
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
    payload = {
        "full_name": "Test User One",
        "email": "user1@example.com",
        "password": "Password123!"
    }
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/login", data={"username": "user1@example.com", "password": "WrongPassword"})
    assert response.status_code == 401
