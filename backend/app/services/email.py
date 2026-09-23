"""Email service for verification, password reset, and notifications."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("nebula.email")


class EmailService:
    """Email service with SMTP support."""

    def __init__(self):
        self.enabled = bool(settings.smtp_host and settings.smtp_username)
        if self.enabled:
            logger.info("Email service enabled")
        else:
            logger.warning("Email service disabled - SMTP not configured")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        if not self.enabled:
            logger.warning("Email service not enabled - skipping send to %s", to_email)
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
            msg["To"] = to_email

            # Add text part
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))

            # Add HTML part
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)

            logger.info("Email sent to %s: %s", to_email, subject)
            return True

        except Exception as exc:
            logger.exception("Failed to send email to %s: %s", to_email, exc)
            return False

    async def send_verification_email(self, to_email: str, verification_link: str) -> bool:
        """Send email verification link."""
        subject = "Verify your Nebula Search account"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Welcome to Nebula Search!</h2>
            <p>Please verify your email address by clicking the link below:</p>
            <p>
                <a href="{verification_link}" 
                   style="background-color: #4CAF50; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Verify Email Address
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <hr>
            <p style="color: #999; font-size: 12px;">Nebula Search Engine</p>
        </body>
        </html>
        """
        text_content = f"""
        Welcome to Nebula Search!
        
        Please verify your email address by visiting this link:
        {verification_link}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        
        Nebula Search Engine
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_password_reset_email(self, to_email: str, reset_link: str) -> bool:
        """Send password reset link."""
        subject = "Reset your Nebula Search password"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Click the link below:</p>
            <p>
                <a href="{reset_link}" 
                   style="background-color: #f44336; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Reset Password
                </a>
            </p>
            <p>Or copy and paste this link into your browser:</p>
            <p style="color: #666; word-break: break-all;">{reset_link}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
            <hr>
            <p style="color: #999; font-size: 12px;">Nebula Search Engine</p>
        </body>
        </html>
        """
        text_content = f"""
        Password Reset Request
        
        You requested to reset your password. Visit this link:
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email.
        
        Nebula Search Engine
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_welcome_email(self, to_email: str) -> bool:
        """Send welcome email after registration."""
        subject = "Welcome to Nebula Search!"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Welcome to Nebula Search!</h2>
            <p>Thank you for creating an account. We're excited to have you on board!</p>
            <p>Nebula Search is a powerful AI-powered search engine that helps you find information quickly and efficiently.</p>
            <h3>Getting Started:</h3>
            <ul>
                <li>Perform web searches with AI-powered results</li>
                <li>Upload and search through documents</li>
                <li>Use vector search for semantic understanding</li>
                <li>Access advanced analytics and insights</li>
            </ul>
            <p>If you have any questions, feel free to reach out to our support team.</p>
            <hr>
            <p style="color: #999; font-size: 12px;">Nebula Search Engine</p>
        </body>
        </html>
        """
        text_content = """
        Welcome to Nebula Search!
        
        Thank you for creating an account. We're excited to have you on board!
        
        Getting Started:
        - Perform web searches with AI-powered results
        - Upload and search through documents
        - Use vector search for semantic understanding
        - Access advanced analytics and insights
        
        If you have any questions, feel free to reach out to our support team.
        
        Nebula Search Engine
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_mfa_enabled_email(self, to_email: str) -> bool:
        """Send notification when MFA is enabled."""
        subject = "Multi-Factor Authentication Enabled"
        html_content = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>MFA Enabled</h2>
            <p>Multi-factor authentication has been enabled on your account.</p>
            <p>Your account is now more secure. You'll need to enter a verification code from your authenticator app when logging in.</p>
            <p>If you didn't enable MFA, please contact support immediately.</p>
            <hr>
            <p style="color: #999; font-size: 12px;">Nebula Search Engine</p>
        </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_content)

    async def send_security_alert(
        self, to_email: str, alert_type: str, details: str
    ) -> bool:
        """Send security alert email."""
        subject = f"Security Alert: {alert_type}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Security Alert</h2>
            <p><strong>{alert_type}</strong></p>
            <p>{details}</p>
            <p>If this was you, you can ignore this email.</p>
            <p>If you didn't perform this action, please secure your account immediately:</p>
            <ul>
                <li>Change your password</li>
                <li>Review your active sessions</li>
                <li>Enable multi-factor authentication</li>
            </ul>
            <hr>
            <p style="color: #999; font-size: 12px;">Nebula Search Engine</p>
        </body>
        </html>
        """
        return await self.send_email(to_email, subject, html_content)


# Global email service instance
email_service = EmailService()