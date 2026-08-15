import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_preflight_options_auth_config_localhost_5501():
    headers = {
        "Origin": "http://localhost:5501",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type"
    }
    response = client.options("/api/v1/auth/config", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5501"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "GET" in response.headers.get("access-control-allow-methods", "")

def test_cors_get_auth_config_localhost_5501():
    headers = {"Origin": "http://localhost:5501"}
    response = client.get("/api/v1/auth/config", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5501"
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_preflight_options_auth_login_localhost_5501():
    headers = {
        "Origin": "http://localhost:5501",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    }
    response = client.options("/api/v1/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5501"
    assert response.headers.get("access-control-allow-credentials") == "true"
    assert "POST" in response.headers.get("access-control-allow-methods", "")

def test_cors_post_auth_login_127_0_0_1_5501():
    headers = {"Origin": "http://127.0.0.1:5501"}
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "demo@nxtmov.local", "password": "NxtMov@123"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5501"
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_production_github_pages_origin():
    headers = {
        "Origin": "https://vinaynalavade.github.io",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type"
    }
    response = client.options("/api/v1/auth/login", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://vinaynalavade.github.io"
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_dynamic_local_ports():
    # Any local dev port (e.g. 5173, 5500, 5502, 3000, 8080)
    for origin in ["http://localhost:5173", "http://127.0.0.1:5502", "http://localhost:3000", "http://localhost:8080"]:
        response = client.options(
            "/api/v1/auth/config",
            headers={"Origin": origin, "Access-Control-Request-Method": "GET"}
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_rejects_unauthorized_external_origin():
    response = client.options(
        "/api/v1/auth/config",
        headers={"Origin": "https://malicious-external-site.com", "Access-Control-Request-Method": "GET"}
    )
    # Disallowed origin should not have access-control-allow-origin header
    assert response.headers.get("access-control-allow-origin") is None
