import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.sms_service import (
    normalize_phone_number,
    otp_rate_limiter,
    UnconfiguredSmsProvider,
    DevMockSmsProvider,
    TwilioSmsProvider,
    Msg91SmsProvider,
    get_sms_provider,
    SmsDeliveryResult
)
from app.services.email_service import (
    generate_verification_url,
    UnconfiguredEmailProvider,
    DevMockEmailProvider,
    SmtpEmailProvider,
    get_email_provider,
    EmailDeliveryResult
)

client = TestClient(app)

# ==============================================================================
# UNIT TESTS: PHONE NUMBER NORMALIZATION & RATE LIMITER
# ==============================================================================

def test_phone_number_normalization():
    # 10-digit Indian standard
    assert normalize_phone_number("9876543210") == "+919876543210"
    assert normalize_phone_number(" 98765 43210 ") == "+919876543210"
    
    # Existing country codes
    assert normalize_phone_number("+91 98765 43210") == "+919876543210"
    assert normalize_phone_number("+1 (555) 123-4567") == "+15551234567"
    assert normalize_phone_number("+44 7911 123456") == "+447911123456"
    assert normalize_phone_number("+971 50 123 4567") == "+971501234567"

    # Invalid phone numbers
    with pytest.raises(ValueError):
        normalize_phone_number("")

    with pytest.raises(ValueError):
        normalize_phone_number("123")  # Too short

    with pytest.raises(ValueError):
        normalize_phone_number("+1234567890123456789")  # Too long

    with pytest.raises(ValueError):
        normalize_phone_number("abcdefghij")  # Non-numeric


def test_otp_rate_limiter_cooldown_and_window():
    otp_rate_limiter.clear()
    key = "user_test_cooldown"

    # First request: allowed
    allowed, msg = otp_rate_limiter.check_rate_limit(key)
    assert allowed is True

    # Immediate second request: blocked by cooldown
    allowed, msg = otp_rate_limiter.check_rate_limit(key)
    assert allowed is False
    assert "seconds before requesting" in msg

    # Clear limiter
    otp_rate_limiter.clear()
    allowed, _ = otp_rate_limiter.check_rate_limit(key)
    assert allowed is True


# ==============================================================================
# UNIT TESTS: SMS PROVIDER ABSTRACTIONS
# ==============================================================================

def test_sms_provider_unconfigured():
    provider = UnconfiguredSmsProvider()
    result = provider.send_otp("+919876543210", "123456")
    assert result.success is False
    assert result.error_code == "PROVIDER_NOT_CONFIGURED"
    assert result.status_code == 503


def test_sms_provider_dev_mock():
    provider = DevMockSmsProvider()
    result = provider.send_otp("+919876543210", "123456")
    assert result.success is True
    assert result.status_code == 200


@patch("urllib.request.urlopen")
def test_sms_provider_twilio_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 201
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    provider = TwilioSmsProvider("ACtest", "token_test", "+15005550006")
    result = provider.send_otp("+919876543210", "123456")
    assert result.success is True
    assert result.status_code == 200


@patch("urllib.request.urlopen")
def test_sms_provider_twilio_network_failure(mock_urlopen):
    mock_urlopen.side_effect = Exception("Connection refused")

    provider = TwilioSmsProvider("ACtest", "token_test", "+15005550006")
    result = provider.send_otp("+919876543210", "123456")
    assert result.success is False
    assert result.error_code == "PROVIDER_TIMEOUT"
    assert result.status_code == 504


# ==============================================================================
# UNIT TESTS: EMAIL PROVIDER ABSTRACTIONS & URL GENERATION
# ==============================================================================

def test_verification_url_generation():
    token = "test_sample_token_12345"
    
    # GitHub Pages origin / default
    gh_url = generate_verification_url(token, "https://vinaynalavade.github.io/NxtMov")
    assert gh_url == f"https://vinaynalavade.github.io/NxtMov/#/verify-email?token={token}"
    assert "/#" in gh_url

    # Local development origin
    local_url = generate_verification_url(token, "http://127.0.0.1:5501")
    assert local_url == f"http://127.0.0.1:5501/#/verify-email?token={token}"


def test_email_provider_unconfigured():
    provider = UnconfiguredEmailProvider()
    res = provider.send_verification_email("user@example.com", "Test User", "https://example.com/verify")
    assert res.success is False
    assert res.error_code == "PROVIDER_NOT_CONFIGURED"
    assert res.status_code == 503


def test_email_provider_dev_mock():
    provider = DevMockEmailProvider()
    res = provider.send_verification_email("user@example.com", "Test User", "https://example.com/verify")
    assert res.success is True
    assert res.status_code == 200


@patch("smtplib.SMTP")
def test_email_provider_smtp_success(mock_smtp):
    instance = MagicMock()
    mock_smtp.return_value = instance

    provider = SmtpEmailProvider(host="smtp.example.com", port=587, username="user", password="pwd")
    res = provider.send_verification_email("recipient@example.com", "Recipient", "https://example.com/verify")
    assert res.success is True
    assert instance.sendmail.called


# ==============================================================================
# INTEGRATION TESTS: FULL OTP & EMAIL VERIFICATION LIFECYCLE
# ==============================================================================

def test_full_phone_otp_and_email_verification_lifecycle():
    otp_rate_limiter.clear()

    # 1. Register a test user
    reg = client.post("/api/v1/auth/register", json={
        "full_name": "Deepak Patil",
        "email": "deepak.patil.verification@test.com",
        "password": "Password123!",
        "phone": "+91 98220 11223"
    })
    assert reg.status_code == 201
    auth_token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}

    # 2. Verify initial state in profile
    prof_before = client.get("/api/v1/profile", headers=headers).json()
    assert prof_before["is_email_verified"] is False
    assert prof_before["is_phone_verified"] is False

    # 3. Request Email Verification Link
    email_req = client.post("/api/v1/auth/verify-email/request", headers=headers)
    assert email_req.status_code == 200
    assert "Verification" in email_req.json()["message"]
    ver_link = email_req.json()["verification_link"]
    token = ver_link.split("token=")[1]

    # 4. Confirm Email via POST endpoint
    confirm_email = client.post("/api/v1/auth/verify-email/confirm", json={"token": token})
    assert confirm_email.status_code == 200
    assert confirm_email.json()["is_verified"] is True

    # 5. Replay attack / Already used email token must fail with 400
    confirm_replay = client.post("/api/v1/auth/verify-email/confirm", json={"token": token})
    assert confirm_replay.status_code == 400
    assert "invalid or has already been used" in confirm_replay.json()["detail"]

    # 6. Request Phone OTP
    otp_req = client.post("/api/v1/auth/verify-phone/request-otp", headers=headers, json={"phone": "+91 98220 11223"})
    assert otp_req.status_code == 200
    dev_otp = otp_req.json()["dev_otp"]
    assert dev_otp is not None
    assert len(dev_otp) == 6

    # 7. Submit Invalid OTP code -> fails with 400
    wrong_otp = "000000" if dev_otp != "000000" else "111111"
    res_wrong = client.post("/api/v1/auth/verify-phone/confirm-otp", headers=headers, json={"phone": "+91 98220 11223", "otp": wrong_otp})
    assert res_wrong.status_code == 400
    assert "Invalid OTP" in res_wrong.json()["detail"]

    # 8. Submit Correct OTP -> succeeds
    res_correct = client.post("/api/v1/auth/verify-phone/confirm-otp", headers=headers, json={"phone": "+91 98220 11223", "otp": dev_otp})
    assert res_correct.status_code == 200
    assert res_correct.json()["is_verified"] is True

    # 9. Replay attack / Already used OTP must fail
    res_otp_replay = client.post("/api/v1/auth/verify-phone/confirm-otp", headers=headers, json={"phone": "+91 98220 11223", "otp": dev_otp})
    assert res_otp_replay.status_code == 400

    # 10. Check Profile after verification
    prof_after = client.get("/api/v1/profile", headers=headers).json()
    assert prof_after["is_email_verified"] is True
    assert prof_after["is_phone_verified"] is True


def test_unconfigured_provider_production_behavior():
    """
    When no SMS or Email provider is configured in production, API must return structured 503
    rather than falsely claiming delivery.
    """
    with patch.object(settings, "NXTMOV_DEMO_MODE", False), \
         patch.object(settings, "SMS_PROVIDER", ""), \
         patch.object(settings, "TWILIO_ACCOUNT_SID", None), \
         patch.object(settings, "MSG91_AUTH_KEY", None), \
         patch.object(settings, "EMAIL_PROVIDER", ""), \
         patch.object(settings, "SMTP_HOST", None), \
         patch.object(settings, "SENDGRID_API_KEY", None):

        # Register user
        reg = client.post("/api/v1/auth/register", json={
            "full_name": "Prod User",
            "email": "prod.user@example.com",
            "password": "Password123!",
            "phone": "+91 91234 56789"
        })
        assert reg.status_code == 201
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        otp_rate_limiter.clear()

        # SMS Request without configured provider -> 503
        otp_res = client.post("/api/v1/auth/verify-phone/request-otp", headers=headers, json={"phone": "+91 91234 56789"})
        assert otp_res.status_code == 503
        assert "not configured" in otp_res.json()["detail"]

        # Email Request without configured provider -> 503
        email_res = client.post("/api/v1/auth/verify-email/request", headers=headers)
        assert email_res.status_code == 503
        assert "not configured" in email_res.json()["detail"]
