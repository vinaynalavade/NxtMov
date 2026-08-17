import abc
import json
import logging
import smtplib
import ssl
import urllib.request
import urllib.error
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class EmailDeliveryResult:
    success: bool
    provider: str
    message: str
    error_code: Optional[str] = None
    status_code: int = 200


def generate_verification_url(token: str, request_origin: Optional[str] = None) -> str:
    """
    Generates the frontend verification URL.
    Maintains compatibility with GitHub Pages subpaths (e.g. /NxtMov/) and hash routing (/#/verify-email?token=...).
    """
    if request_origin and ("localhost" in request_origin or "127.0.0.1" in request_origin):
        base = request_origin.rstrip("/")
    else:
        base = (settings.FRONTEND_URL or "https://vinaynalavade.github.io/NxtMov").rstrip("/")

    return f"{base}/#/verify-email?token={token}"


class BaseEmailProvider(abc.ABC):
    @abc.abstractmethod
    def send_verification_email(self, to_email: str, user_name: str, verification_link: str) -> EmailDeliveryResult:
        pass

    @abc.abstractmethod
    def send_password_reset_email(self, to_email: str, user_name: str, reset_link: str) -> EmailDeliveryResult:
        pass


class UnconfiguredEmailProvider(BaseEmailProvider):
    def send_verification_email(self, to_email: str, user_name: str, verification_link: str) -> EmailDeliveryResult:
        logger.warning(f"Email verification requested for {to_email}, but no email/SMTP provider is configured.")
        return EmailDeliveryResult(
            success=False,
            provider="unconfigured",
            message="Email delivery service is currently not configured on the server. Please contact support.",
            error_code="PROVIDER_NOT_CONFIGURED",
            status_code=503
        )

    def send_password_reset_email(self, to_email: str, user_name: str, reset_link: str) -> EmailDeliveryResult:
        logger.warning(f"Password reset email requested for {to_email}, but no email/SMTP provider is configured.")
        return EmailDeliveryResult(
            success=False,
            provider="unconfigured",
            message="Email delivery service is currently not configured on the server. Please contact support.",
            error_code="PROVIDER_NOT_CONFIGURED",
            status_code=503
        )


class DevMockEmailProvider(BaseEmailProvider):
    def send_verification_email(self, to_email: str, user_name: str, verification_link: str) -> EmailDeliveryResult:
        print(f"[DEV MOCK EMAIL] Verification email to: {to_email} | Link: {verification_link}", flush=True)
        return EmailDeliveryResult(
            success=True,
            provider="dev_mock",
            message="Verification email dispatched successfully.",
            status_code=200
        )

    def send_password_reset_email(self, to_email: str, user_name: str, reset_link: str) -> EmailDeliveryResult:
        print(f"[DEV MOCK EMAIL] Password reset email to: {to_email} | Link: {reset_link}", flush=True)
        return EmailDeliveryResult(
            success=True,
            provider="dev_mock",
            message="Password reset email dispatched successfully.",
            status_code=200
        )


class SmtpEmailProvider(BaseEmailProvider):
    def __init__(
        self,
        host: str,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        from_email: str = "noreply@nxtmov.com",
        from_name: str = "NxtMov Platform"
    ):
        self.host = host.strip() if host else ""
        self.port = port
        self.username = username.strip() if username else None
        self.password = password.strip() if password else None
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.from_email = from_email
        self.from_name = from_name

    def _send_smtp_message(self, to_email: str, subject: str, text_body: str, html_body: str) -> EmailDeliveryResult:
        if not self.host:
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                message="SMTP server host is not configured.",
                error_code="PROVIDER_AUTH_ERROR",
                status_code=500
            )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=10)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=10)
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)

            if self.username and self.password:
                server.login(self.username, self.password)

            server.sendmail(self.from_email, [to_email], msg.as_string())
            server.quit()

            return EmailDeliveryResult(
                success=True,
                provider="smtp",
                message="Verification email sent. Please check your inbox.",
                status_code=200
            )
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                message="SMTP email provider authentication failed.",
                error_code="PROVIDER_AUTH_ERROR",
                status_code=502
            )
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError) as e:
            logger.error(f"SMTP connection failed: {e}")
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                message="SMTP email server connection timeout or network failure.",
                error_code="PROVIDER_TIMEOUT",
                status_code=504
            )
        except Exception as e:
            logger.error(f"SMTP sendmail error: {e}")
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                message=f"Failed to deliver email: {str(e)}",
                error_code="PROVIDER_ERROR",
                status_code=502
            )

    def send_verification_email(self, to_email: str, user_name: str, verification_link: str) -> EmailDeliveryResult:
        subject = "Verify your email address — NxtMov Platform"
        text_body = (
            f"Hello {user_name},\n\n"
            f"Thank you for joining NxtMov. Please verify your email address by opening the link below:\n\n"
            f"{verification_link}\n\n"
            f"This verification link is valid for 24 hours. If you did not create a NxtMov account, please ignore this email.\n\n"
            f"Best regards,\n"
            f"The NxtMov Team"
        )
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; padding: 2rem; color: #0f172a;">
          <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <div style="text-align: center; margin-bottom: 1.5rem;">
              <h2 style="color: #2563EB; margin: 0; font-size: 1.5rem; font-weight: 800;">NxtMov</h2>
              <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.25rem;">Talent & Recruitment Platform</p>
            </div>
            <h3 style="font-size: 1.15rem; color: #0f172a; margin-bottom: 0.75rem;">Verify your email address</h3>
            <p style="color: #334155; font-size: 0.95rem; line-height: 1.5;">
              Hello <strong>{user_name}</strong>,<br><br>
              Please confirm your email address to unlock verified status and job recommendations across your NxtMov workspace.
            </p>
            <div style="text-align: center; margin: 2rem 0;">
              <a href="{verification_link}" style="background-color: #2563EB; color: #ffffff; padding: 0.75rem 1.75rem; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.95rem; display: inline-block;">
                Verify Email Address
              </a>
            </div>
            <p style="color: #64748b; font-size: 0.8rem; line-height: 1.4;">
              Or copy and paste this link into your browser:<br>
              <a href="{verification_link}" style="color: #2563EB; word-break: break-all;">{verification_link}</a>
            </p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 1.5rem 0;">
            <p style="color: #94a3b8; font-size: 0.75rem; text-align: center; margin: 0;">
              This link expires in 24 hours. If you did not create this account, you can safely ignore this email.
            </p>
          </div>
        </body>
        </html>
        """
        return self._send_smtp_message(to_email, subject, text_body, html_body)

    def send_password_reset_email(self, to_email: str, user_name: str, reset_link: str) -> EmailDeliveryResult:
        subject = "Reset your password — NxtMov Platform"
        text_body = (
            f"Hello {user_name},\n\n"
            f"We received a request to reset your password. Open the link below to set a new password:\n\n"
            f"{reset_link}\n\n"
            f"If you did not request a password reset, please ignore this email.\n\n"
            f"Best regards,\n"
            f"The NxtMov Team"
        )
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; padding: 2rem; color: #0f172a;">
          <div style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 2rem;">
            <h3 style="font-size: 1.15rem; color: #0f172a; margin-bottom: 0.75rem;">Password Reset Request</h3>
            <p style="color: #334155; font-size: 0.95rem; line-height: 1.5;">
              Hello <strong>{user_name}</strong>,<br><br>
              Click the button below to choose a new password for your account.
            </p>
            <div style="text-align: center; margin: 2rem 0;">
              <a href="{reset_link}" style="background-color: #2563EB; color: #ffffff; padding: 0.75rem 1.75rem; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 0.95rem; display: inline-block;">
                Reset Password
              </a>
            </div>
            <p style="color: #94a3b8; font-size: 0.75rem; text-align: center; margin: 0;">
              If you did not request this password reset, please ignore this message.
            </p>
          </div>
        </body>
        </html>
        """
        return self._send_smtp_message(to_email, subject, text_body, html_body)


class SendGridEmailProvider(BaseEmailProvider):
    def __init__(self, api_key: str, from_email: str = "noreply@nxtmov.com", from_name: str = "NxtMov Platform"):
        self.api_key = api_key.strip()
        self.from_email = from_email
        self.from_name = from_name

    def send_verification_email(self, to_email: str, user_name: str, verification_link: str) -> EmailDeliveryResult:
        if not self.api_key:
            return EmailDeliveryResult(
                success=False,
                provider="sendgrid",
                message="SendGrid API key is not configured.",
                error_code="PROVIDER_AUTH_ERROR",
                status_code=500
            )

        url = "https://api.sendgrid.com/v3/mail/send"
        payload = {
            "personalizations": [{"to": [{"email": to_email, "name": user_name}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": "Verify your email address — NxtMov Platform",
            "content": [
                {
                    "type": "text/html",
                    "value": f"<p>Hello {user_name},</p><p>Please verify your email address: <a href='{verification_link}'>{verification_link}</a></p>"
                }
            ]
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    return EmailDeliveryResult(
                        success=True,
                        provider="sendgrid",
                        message="Verification email sent. Please check your inbox.",
                        status_code=200
                    )
                return EmailDeliveryResult(
                    success=False,
                    provider="sendgrid",
                    message=f"SendGrid returned status {resp.status}.",
                    error_code="PROVIDER_ERROR",
                    status_code=502
                )
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return EmailDeliveryResult(
                success=False,
                provider="sendgrid",
                message="Email provider timeout or connection error.",
                error_code="PROVIDER_TIMEOUT",
                status_code=504
            )

    def send_password_reset_email(self, to_email: str, user_name: str, reset_link: str) -> EmailDeliveryResult:
        if not self.api_key:
            return EmailDeliveryResult(
                success=False,
                provider="sendgrid",
                message="SendGrid API key is not configured.",
                error_code="PROVIDER_AUTH_ERROR",
                status_code=500
            )

        url = "https://api.sendgrid.com/v3/mail/send"
        payload = {
            "personalizations": [{"to": [{"email": to_email, "name": user_name}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": "Reset your password — NxtMov Platform",
            "content": [
                {
                    "type": "text/html",
                    "value": f"<p>Hello {user_name},</p><p>Reset your password: <a href='{reset_link}'>{reset_link}</a></p>"
                }
            ]
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    return EmailDeliveryResult(
                        success=True,
                        provider="sendgrid",
                        message="Password reset email sent. Please check your inbox.",
                        status_code=200
                    )
                return EmailDeliveryResult(
                    success=False,
                    provider="sendgrid",
                    message=f"SendGrid returned status {resp.status}.",
                    error_code="PROVIDER_ERROR",
                    status_code=502
                )
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return EmailDeliveryResult(
                success=False,
                provider="sendgrid",
                message="Email provider timeout or connection error.",
                error_code="PROVIDER_TIMEOUT",
                status_code=504
            )


def get_email_provider() -> BaseEmailProvider:
    """
    Factory resolving the active Email provider based on environment configuration.
    """
    provider_name = (settings.EMAIL_PROVIDER or "").strip().lower()

    if provider_name == "smtp" or (not provider_name and settings.SMTP_HOST):
        return SmtpEmailProvider(
            host=settings.SMTP_HOST or "",
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_TLS,
            use_ssl=settings.SMTP_SSL,
            from_email=settings.EMAILS_FROM_EMAIL,
            from_name=settings.EMAILS_FROM_NAME
        )
    elif provider_name == "sendgrid" or (not provider_name and settings.SENDGRID_API_KEY):
        return SendGridEmailProvider(
            api_key=settings.SENDGRID_API_KEY or "",
            from_email=settings.EMAILS_FROM_EMAIL,
            from_name=settings.EMAILS_FROM_NAME
        )
    elif provider_name in ("mock", "dev", "log"):
        return DevMockEmailProvider()
    elif settings.NXTMOV_DEMO_MODE:
        return DevMockEmailProvider()

    return UnconfiguredEmailProvider()
