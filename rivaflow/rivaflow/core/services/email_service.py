"""Email service for sending transactional emails."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from rivaflow.core.services.email_transactional import (
    send_coach_settings_reminder,
    send_drip_day1,
    send_drip_day3,
    send_drip_day5,
    send_feedback_notification,
    send_password_changed_confirmation,
    send_password_reset_email,
    send_waitlist_invite_email,
    send_welcome_email,
)

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SendGrid API or SMTP fallback."""

    # ------------------------------------------------------------------
    # Transactional methods (delegated to email_transactional module)
    # ------------------------------------------------------------------
    send_password_reset_email = send_password_reset_email
    send_password_changed_confirmation = send_password_changed_confirmation
    send_welcome_email = send_welcome_email
    send_waitlist_invite_email = send_waitlist_invite_email
    send_drip_day1 = send_drip_day1
    send_drip_day3 = send_drip_day3
    send_drip_day5 = send_drip_day5
    send_feedback_notification = send_feedback_notification
    send_coach_settings_reminder = send_coach_settings_reminder

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def __init__(self):
        # Try SendGrid HTTP API first (works on Render)
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

        # Fallback to SMTP for local development
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "RivaFlow")

        # Determine which method to use
        if self.sendgrid_api_key:
            self.method = "sendgrid"
            self.enabled = True
            logger.info("Email service configured with SendGrid HTTP API")
        elif self.smtp_user and self.smtp_password:
            self.method = "smtp"
            self.enabled = True
            logger.info("Email service configured with SMTP")
        else:
            self.method = None
            self.enabled = False
            logger.warning(
                "Email service not configured. Set SENDGRID_API_KEY "
                "or SMTP_USER/SMTP_PASSWORD environment variables."
            )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.error(
                f"Email service not configured. Cannot send email to {to_email}"
            )
            return False

        if self.method == "sendgrid":
            return self._send_via_sendgrid(
                to_email, subject, html_content, text_content
            )
        else:
            return self._send_via_smtp(to_email, subject, html_content, text_content)

    def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Send email via SendGrid HTTP API."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Content, Email, Mail, To

            # Create message
            from_email_obj = Email(self.from_email, self.from_name)
            to_email_obj = To(to_email)

            # Use text content as fallback if provided, otherwise use HTML
            plain_text = Content(
                "text/plain",
                (
                    text_content
                    if text_content
                    else "Please view this email in HTML format."
                ),
            )
            html = Content("text/html", html_content)

            mail = Mail(
                from_email=from_email_obj,
                to_emails=to_email_obj,
                subject=subject,
                plain_text_content=plain_text,
                html_content=html,
            )

            # Send via SendGrid API
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(mail)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email} via SendGrid")
                return True
            else:
                logger.error(
                    f"SendGrid returned status {response.status_code} "
                    f"for {to_email}"
                )
                return False

        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                logger.error(
                    f"SendGrid 403 Forbidden error. "
                    f"This usually means the sender email "
                    f"'{self.from_email}' "
                    f"is not verified in SendGrid. "
                    f"Please verify the sender in SendGrid dashboard. "
                    f"Error: {e}"
                )
            elif "400" in error_msg or "Bad Request" in error_msg:
                logger.error(
                    f"SendGrid 400 Bad Request. "
                    f"Check sender verification for "
                    f"'{self.from_email}' "
                    f"and API key permissions. Error: {e}"
                )
            else:
                logger.error(f"Failed to send email via SendGrid to {to_email}: {e}")

            # Try SMTP fallback if configured
            if self.smtp_user and self.smtp_password:
                logger.info(f"Attempting SMTP fallback for {to_email}")
                return self._send_via_smtp(
                    to_email, subject, html_content, text_content
                )

            return False

    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Send email via SMTP (fallback for local development)."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Attach text and HTML parts
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email} via SMTP")
            return True

        except (ConnectionError, OSError, smtplib.SMTPException) as e:
            logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
            return False
