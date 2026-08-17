import abc
import json
import logging
import re
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional, Dict, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class SmsDeliveryResult:
    success: bool
    provider: str
    message: str
    error_code: Optional[str] = None
    status_code: int = 200


def normalize_phone_number(phone: str, default_country_code: str = "+91") -> str:
    """
    Normalizes phone number to standard E.164 format and validates digit count.
    Supports numbers with leading + country code, spaces, hyphens, and 10-digit standard formats.
    """
    if not phone or not str(phone).strip():
        raise ValueError("Please enter a valid mobile number.")
    
    cleaned = re.sub(r"[\s\-\(\)\.]+", "", str(phone).strip())
    if not cleaned:
        raise ValueError("Please enter a valid mobile number.")
    
    # If starts with +, validate international format
    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if not digits.isdigit() or len(digits) < 7 or len(digits) > 15:
            raise ValueError("Mobile number must contain between 7 and 15 digits.")
        return cleaned
    
    # Without leading +, must be all digits
    if not cleaned.isdigit() or len(cleaned) < 7 or len(cleaned) > 15:
        raise ValueError("Mobile number must contain between 7 and 15 digits.")
    
    # 10 digits default country code normalization
    if len(cleaned) == 10 and default_country_code:
        prefix = default_country_code if default_country_code.startswith("+") else f"+{default_country_code}"
        return f"{prefix}{cleaned}"
    
    return f"+{cleaned}"


class OtpRateLimiter:
    """
    Thread-safe rate limiter for OTP requests to prevent SMS flooding and exhaustion attacks.
    """
    def __init__(self, cooldown_seconds: int = 30, max_requests: int = 5, window_seconds: int = 900):
        self.cooldown_seconds = cooldown_seconds
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, list] = {}
        self._last_request: Dict[str, float] = {}
        self._lock = threading.Lock()

    def check_rate_limit(self, identifier: str) -> Tuple[bool, str]:
        now = time.time()
        with self._lock:
            # 1. Check cooldown
            last_ts = self._last_request.get(identifier, 0)
            elapsed = now - last_ts
            if elapsed < self.cooldown_seconds:
                wait_sec = int(self.cooldown_seconds - elapsed) + 1
                return False, f"Please wait {wait_sec} seconds before requesting another verification code."

            # 2. Clean history outside window
            cutoff = now - self.window_seconds
            timestamps = [ts for ts in self._history.get(identifier, []) if ts > cutoff]
            
            if len(timestamps) >= self.max_requests:
                return False, "Too many OTP requests. Please wait a few minutes before trying again."

            timestamps.append(now)
            self._history[identifier] = timestamps
            self._last_request[identifier] = now
            return True, ""

    def clear(self):
        with self._lock:
            self._history.clear()
            self._last_request.clear()


otp_rate_limiter = OtpRateLimiter()


class BaseSmsProvider(abc.ABC):
    @abc.abstractmethod
    def send_otp(self, to_phone: str, otp: str) -> SmsDeliveryResult:
        pass


class UnconfiguredSmsProvider(BaseSmsProvider):
    def send_otp(self, to_phone: str, otp: str) -> SmsDeliveryResult:
        logger.warning(f"SMS dispatch requested for {to_phone}, but no SMS provider is configured.")
        return SmsDeliveryResult(
            success=False,
            provider="unconfigured",
            message="SMS delivery service is currently not configured on the server. Please contact support.",
            error_code="PROVIDER_NOT_CONFIGURED",
            status_code=503
        )


class DevMockSmsProvider(BaseSmsProvider):
    def send_otp(self, to_phone: str, otp: str) -> SmsDeliveryResult:
        print(f"[DEV MOCK SMS] Dispatched OTP '{otp}' to phone '{to_phone}'", flush=True)
        return SmsDeliveryResult(
            success=True,
            provider="dev_mock",
            message="Verification code sent to your mobile number.",
            status_code=200
        )


class TwilioSmsProvider(BaseSmsProvider):
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid.strip()
        self.auth_token = auth_token.strip()
        self.from_number = from_number.strip()

    def send_otp(self, to_phone: str, otp: str) -> SmsDeliveryResult:
        if not self.account_sid or not self.auth_token or not self.from_number:
            return SmsDeliveryResult(
                success=False,
                provider="twilio",
                message="Twilio SMS provider credentials are misconfigured.",
                error_code="PROVIDER_AUTH_ERROR",
                status_code=500
            )

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        body = f"Your NxtMov verification code is {otp}. Valid for 10 minutes."
        data = urllib.parse.urlencode({
            "To": to_phone,
            "From": self.from_number,
            "Body": body
        }).encode("utf-8")

        import base64
        auth_header = "Basic " + base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode("utf-8")).decode("ascii")

        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", auth_header)
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    return SmsDeliveryResult(
                        success=True,
                        provider="twilio",
                        message="Verification code sent to your mobile number.",
                        status_code=200
                    )
                return SmsDeliveryResult(
                    success=False,
                    provider="twilio",
                    message=f"Twilio returned status {resp.status}.",
                    error_code="PROVIDER_ERROR",
                    status_code=502
                )
        except urllib.error.HTTPError as e:
            try:
                err_body = e.read().decode("utf-8")
                err_json = json.loads(err_body)
                err_msg = err_json.get("message") or f"Twilio error {e.code}"
            except Exception:
                err_msg = f"Twilio HTTP Error {e.code}"
            logger.error(f"Twilio SMS delivery failed: {err_msg}")
            return SmsDeliveryResult(
                success=False,
                provider="twilio",
                message=f"SMS delivery failed: {err_msg}",
                error_code="PROVIDER_ERROR",
                status_code=502
            )
        except Exception as e:
            logger.error(f"Twilio SMS connection error: {e}")
            return SmsDeliveryResult(
                success=False,
                provider="twilio",
                message="SMS provider connection timeout or network failure.",
                error_code="PROVIDER_TIMEOUT",
                status_code=504
            )


class Msg91SmsProvider(BaseSmsProvider):
    def __init__(self, auth_key: str, sender_id: str, template_id: Optional[str] = None):
        self.auth_key = auth_key.strip()
        self.sender_id = sender_id.strip()
        self.template_id = template_id.strip() if template_id else None

    def send_otp(self, to_phone: str, otp: str) -> SmsDeliveryResult:
        if not self.auth_key:
            return SmsDeliveryResult(
                success=False,
                provider="msg91",
                message="MSG91 credentials are misconfigured.",
                error_code="PROVIDER_AUTH_ERROR",
                status_code=500
            )

        clean_digits = re.sub(r"\D", "", to_phone)
        template_param = f"&template_id={self.template_id}" if self.template_id else ""
        url = f"https://control.msg91.com/api/v5/otp?mobile={clean_digits}&authkey={self.auth_key}&otp={otp}{template_param}"
        req = urllib.request.Request(url, method="POST")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    return SmsDeliveryResult(
                        success=True,
                        provider="msg91",
                        message="Verification code sent to your mobile number.",
                        status_code=200
                    )
                return SmsDeliveryResult(
                    success=False,
                    provider="msg91",
                    message=f"MSG91 returned status {resp.status}.",
                    error_code="PROVIDER_ERROR",
                    status_code=502
                )
        except Exception as e:
            logger.error(f"MSG91 SMS connection error: {e}")
            return SmsDeliveryResult(
                success=False,
                provider="msg91",
                message="MSG91 SMS provider timeout or failure.",
                error_code="PROVIDER_TIMEOUT",
                status_code=504
            )


def get_sms_provider() -> BaseSmsProvider:
    """
    Factory resolving the active SMS provider based on environment configuration.
    """
    provider_name = (settings.SMS_PROVIDER or "").strip().lower()

    if provider_name == "twilio" or (not provider_name and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN):
        return TwilioSmsProvider(
            account_sid=settings.TWILIO_ACCOUNT_SID or "",
            auth_token=settings.TWILIO_AUTH_TOKEN or "",
            from_number=settings.TWILIO_FROM_NUMBER or ""
        )
    elif provider_name == "msg91" or (not provider_name and settings.MSG91_AUTH_KEY):
        return Msg91SmsProvider(
            auth_key=settings.MSG91_AUTH_KEY or "",
            sender_id=settings.MSG91_SENDER_ID or "",
            template_id=settings.MSG91_TEMPLATE_ID
        )
    elif provider_name in ("mock", "dev", "log"):
        return DevMockSmsProvider()
    elif settings.NXTMOV_DEMO_MODE:
        return DevMockSmsProvider()

    return UnconfiguredSmsProvider()
