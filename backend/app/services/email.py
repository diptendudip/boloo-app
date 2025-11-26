"""
Email service for sending OTPs
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_otp_email(email: str, otp_code: str) -> bool:
    """
    Send OTP email to user.
    For Phase 1, always sends to diptendudip@gmail.com
    """
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Your {settings.APP_NAME} OTP Code"
        message["From"] = settings.SMTP_USER
        message["To"] = settings.OTP_EMAIL  # Always send to configured email in Phase 1

        # HTML body
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #333;">Your OTP Code</h2>
            <p>Someone (hopefully you!) requested an OTP for the email: <strong>{email}</strong></p>
            <div style="background-color: #f0f0f0; padding: 20px; margin: 20px 0; border-radius: 5px;">
              <h1 style="color: #2196F3; text-align: center; font-size: 48px; margin: 0;">
                {otp_code}
              </h1>
            </div>
            <p>This code will expire in 5 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
              This is an automated message from {settings.APP_NAME}. Please do not reply.
            </p>
            <p style="color: #999; font-size: 10px;">
              Phase 1 Development: All OTPs are sent to {settings.OTP_EMAIL}
            </p>
          </body>
        </html>
        """

        # Text body
        text = f"""
        Your OTP Code for {settings.APP_NAME}

        Requested for email: {email}

        Your OTP Code: {otp_code}

        This code will expire in 5 minutes.

        If you didn't request this, please ignore this email.

        ---
        Phase 1 Development: All OTPs are sent to {settings.OTP_EMAIL}
        """

        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        # Send email
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True,
            )
            logger.info(f"OTP email sent to {settings.OTP_EMAIL} for user {email}")
            return True
        else:
            # Development mode: just log the OTP
            logger.warning(f"SMTP not configured. OTP for {email}: {otp_code}")
            return True

    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}", exc_info=True)
        return False


async def send_notification_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send generic notification email
    """
    try:
        message = MIMEText(body, "html")
        message["Subject"] = subject
        message["From"] = settings.SMTP_USER
        message["To"] = to_email

        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=True,
            )
            logger.info(f"Notification email sent to {to_email}")
            return True
        else:
            logger.warning(f"SMTP not configured. Would send to {to_email}: {subject}")
            return True

    except Exception as e:
        logger.error(f"Failed to send notification email: {e}", exc_info=True)
        return False
