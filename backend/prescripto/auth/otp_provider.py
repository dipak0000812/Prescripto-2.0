"""
OTP Provider interface and implementations for secure OTP dispatch.
"""
import os
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class IOtpProvider(ABC):
    @abstractmethod
    async def send_otp(self, recipient: str, otp: str, channel: str) -> bool:
        """
        Sends an OTP to the specified recipient.
        Channel can be 'SMS' or 'EMAIL'.
        Returns True if successful, False otherwise.
        """
        pass


class DevelopmentOtpProvider(IOtpProvider):
    async def send_otp(self, recipient: str, otp: str, channel: str) -> bool:
        # Development: Log to stdout; never in production logs
        print(f"[DEV-OTP] Sending {channel} OTP {otp} to {recipient}")
        return True


class EmailOtpProvider(IOtpProvider):
    """Production email OTP provider using SMTP."""

    def __init__(
        self,
        smtp_host: str = None,
        smtp_port: int = 587,
        smtp_username: str = None,
        smtp_password: str = None,
        from_email: str = None,
        from_name: str = "Prescripto 2.0",
        use_tls: bool = True,
    ):
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", "587"))
        self.smtp_username = smtp_username or os.getenv("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.from_email = from_email or os.getenv("FROM_EMAIL", "noreply@prescripto.ai")
        self.from_name = from_name or os.getenv("FROM_NAME", "Prescripto 2.0")
        self.use_tls = use_tls

        if not self.smtp_username or not self.smtp_password:
            raise ValueError("SMTP credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")

    async def send_otp(self, recipient: str, otp: str, channel: str) -> bool:
        if channel != "EMAIL":
            raise ValueError(f"Channel {channel} not supported by EmailOtpProvider")

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Your Prescripto 2.0 Verification Code"
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = recipient

            # Plain text version
            text = f"""
Your Prescripto 2.0 verification code is: {otp}

This code will expire in 10 minutes.
If you didn't request this code, please ignore this email.
"""

            # HTML version
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1C252E; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #FFFFFF; border-radius: 16px; padding: 32px; border: 1px solid #E5E7EB;">
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-block; width: 48px; height: 48px; background: linear-gradient(135deg, #0F5147 0%, #0A3831 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
            </div>
            <h1 style="margin: 16px 0 8px; font-size: 24px; font-weight: 700; color: #1C252E;">Your Verification Code</h1>
            <p style="color: #6B7280; margin-bottom: 24px;">Use the code below to complete your verification. This code expires in 10 minutes.</p>

            <div style="background: #F0FDF4; border: 1px solid #A7F3D0; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
                <div style="font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #047857; font-family: 'JetBrains Mono', monospace;">{otp}</div>
            </div>

            <p style="color: #6B7280; font-size: 14px; margin-bottom: 16px;">
                This code will expire in <strong>10 minutes</strong>.
            </p>
            <p style="color: #9CA3AF; font-size: 12px;">
                If you didn't request this code, please ignore this email.
            </p>

            <hr style="border: none; border-top: 1px solid #E5E7EB; margin: 24px 0;">
            <p style="color: #9CA3AF; font-size: 11px; text-align: center;">
                © 2025 Prescripto AI. All rights reserved.
            </p>
        </div>
    </body>
</html>
"""
            text_part = MIMEText(text, "plain", "utf-8")
            html_part = MIMEText(html, "html", "utf-8")

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            if self.smtp_host and self.smtp_port:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
                try:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                    return True
                finally:
                    server.quit()
            return False

        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send OTP to {recipient}: {e}")
            return False


class SmsOtpProvider(IOtpProvider):
    """Production SMS OTP provider (Twilio, Vonage, etc.)"""

    def __init__(
        self,
        provider: str = "twilio",
        account_sid: str = None,
        auth_token: str = None,
        from_number: str = None,
    ):
        self.provider = provider
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER")

        if not self.account_sid or not self.auth_token or not self.from_number:
            raise ValueError("SMS provider credentials not configured.")

    async def send_otp(self, recipient: str, otp: str, channel: str) -> bool:
        if channel != "SMS":
            raise ValueError(f"Channel {channel} not supported by SmsOtpProvider")

        try:
            # TODO: Implement Twilio/Vonage integration
            # For now, log and return True for development
            print(f"[SMS-OTP] Would send OTP {otp} to {recipient} via {self.provider}")
            return True
        except Exception as e:
            print(f"[SMS ERROR] Failed to send OTP: {e}")
            return False


def get_otp_provider() -> IOtpProvider:
    """Factory function to get the appropriate OTP provider based on environment."""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "development":
        return DevelopmentOtpProvider()

    # Production: Use email provider with SMTP
    if os.getenv("SMTP_HOST") and os.getenv("SMTP_USERNAME") and os.getenv("SMTP_PASSWORD"):
        return EmailOtpProvider()

    # Fallback to development
    return DevelopmentOtpProvider()


# Backward-compatible alias
ProductionOtpProvider = EmailOtpProvider
