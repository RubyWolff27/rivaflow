"""Email service for sending transactional emails."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SendGrid API or SMTP fallback."""

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
                "Email service not configured. Set SENDGRID_API_KEY or SMTP_USER/SMTP_PASSWORD environment variables."
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
                    f"SendGrid returned status {response.status_code} for {to_email}"
                )
                return False

        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                logger.error(
                    f"SendGrid 403 Forbidden error. "
                    f"This usually means the sender email '{self.from_email}' "
                    f"is not verified in SendGrid. "
                    f"Please verify the sender in SendGrid dashboard. "
                    f"Error: {e}"
                )
            elif "400" in error_msg or "Bad Request" in error_msg:
                logger.error(
                    f"SendGrid 400 Bad Request. "
                    f"Check sender verification for '{self.from_email}' "
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

    def send_password_reset_email(
        self, to_email: str, reset_token: str, user_name: str | None = None
    ) -> bool:
        """
        Send password reset email with reset link.

        Args:
            to_email: User's email address
            reset_token: Password reset token
            user_name: User's first name (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        # Get base URL from environment or use default
        base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
        reset_link = f"{base_url}/reset-password?token={reset_token}"

        greeting = f"Hi {user_name}," if user_name else "Hi,"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #4F46E5;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Reset Your RivaFlow Password</h2>
        <p>{greeting}</p>
        <p>You requested to reset your password for your RivaFlow account. Click the button below to set a new password:</p>
        <a href="{reset_link}" class="button">Reset Password</a>
        <p>Or copy and paste this link into your browser:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p><strong>This link will expire in 1 hour.</strong></p>
        <p>If you didn't request this password reset, you can safely ignore this email. Your password will not be changed.</p>
        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
Reset Your RivaFlow Password

{greeting}

You requested to reset your password for your RivaFlow account.

Click this link to set a new password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this password reset, you can safely ignore this email.

---
RivaFlow - Training OS for the Mat
"""

        return self.send_email(
            to_email=to_email,
            subject="Reset Your RivaFlow Password",
            html_content=html_content,
            text_content=text_content,
        )

    def send_password_changed_confirmation(
        self, to_email: str, user_name: str | None = None
    ) -> bool:
        """
        Send confirmation email after password change.

        Args:
            to_email: User's email address
            user_name: User's first name (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        greeting = f"Hi {user_name}," if user_name else "Hi,"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Password Changed Successfully</h2>
        <p>{greeting}</p>
        <p>Your RivaFlow password has been changed successfully.</p>
        <p>If you did not make this change, please contact support immediately.</p>
        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
Password Changed Successfully

{greeting}

Your RivaFlow password has been changed successfully.

If you did not make this change, please contact support immediately.

---
RivaFlow - Training OS for the Mat
"""

        return self.send_email(
            to_email=to_email,
            subject="Your RivaFlow Password Was Changed",
            html_content=html_content,
            text_content=text_content,
        )

    def send_welcome_email(self, email: str, first_name: str | None = None) -> bool:
        """
        Send welcome email to a newly registered user.

        Args:
            email: User's email address
            first_name: User's first name (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        # Get base URL from environment or use default
        base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")

        greeting = f"Hey {first_name}," if first_name else "Hey there,"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #e0e0e0;
            background-color: #1a1a2e;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 30px 20px;
            background-color: #1a1a2e;
        }}
        .header {{
            text-align: center;
            padding-bottom: 20px;
            border-bottom: 1px solid #2a2a4a;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #ffffff;
            font-size: 28px;
            margin: 0;
        }}
        .greeting {{
            font-size: 18px;
            color: #ffffff;
            margin-bottom: 10px;
        }}
        .welcome-text {{
            font-size: 16px;
            color: #c0c0c0;
            margin-bottom: 30px;
        }}
        .step {{
            background-color: #2a2a4a;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
        }}
        .step-title {{
            font-size: 14px;
            font-weight: 700;
            color: #ff6b35;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0 0 6px 0;
        }}
        .step-description {{
            font-size: 14px;
            color: #c0c0c0;
            margin: 0 0 14px 0;
        }}
        .button {{
            display: inline-block;
            padding: 10px 22px;
            background-color: #ff6b35;
            color: #ffffff;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
        }}
        .signoff {{
            margin-top: 36px;
            padding-top: 24px;
            border-top: 1px solid #2a2a4a;
            text-align: center;
        }}
        .signoff-motto {{
            font-style: italic;
            color: #ff6b35;
            font-size: 15px;
            margin-bottom: 8px;
        }}
        .signoff-team {{
            color: #888888;
            font-size: 13px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #2a2a4a;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to RivaFlow</h1>
        </div>

        <p class="greeting">{greeting}</p>
        <p class="welcome-text">Welcome to RivaFlow &mdash; your training OS for the mat.</p>

        <div class="step">
            <p class="step-title">1. Set Up Your Profile</p>
            <p class="step-description">Add your belt rank, gym, and photo.</p>
            <a href="{base_url}/profile" class="button">Set Up Profile</a>
        </div>

        <div class="step">
            <p class="step-title">2. Log Your First Session</p>
            <p class="step-description">It takes less than 30 seconds.</p>
            <a href="{base_url}/log" class="button">Log Session</a>
        </div>

        <div class="step">
            <p class="step-title">3. Find Your Training Partners</p>
            <p class="step-description">Connect with your gym crew.</p>
            <a href="{base_url}/find-friends" class="button">Find Partners</a>
        </div>

        <div class="step">
            <p class="step-title">4. Track Your Progress</p>
            <p class="step-description">Analytics and insights build over time.</p>
        </div>

        <div class="signoff">
            <p class="signoff-motto">Train with intent. Flow to mastery.</p>
            <p class="signoff-team">&mdash; The RivaFlow Team</p>
        </div>

        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
Welcome to RivaFlow
====================

{greeting}

Welcome to RivaFlow -- your training OS for the mat.

Here's how to get started:

1. SET UP YOUR PROFILE
   Add your belt rank, gym, and photo.
   {base_url}/profile

2. LOG YOUR FIRST SESSION
   It takes less than 30 seconds.
   {base_url}/log

3. FIND YOUR TRAINING PARTNERS
   Connect with your gym crew.
   {base_url}/find-friends

4. TRACK YOUR PROGRESS
   Analytics and insights build over time.

---
Train with intent. Flow to mastery.
-- The RivaFlow Team

---
RivaFlow - Training OS for the Mat
"""

        return self.send_email(
            to_email=email,
            subject="Welcome to RivaFlow \u2014 Let's Get You Started",
            html_content=html_content,
            text_content=text_content,
        )

    def send_waitlist_invite_email(
        self,
        email: str,
        first_name: str | None = None,
        invite_token: str = "",
    ) -> bool:
        """
        Send waitlist invite email with registration link.

        Args:
            email: Recipient email address
            first_name: Recipient's first name (optional)
            invite_token: Secure invite token for registration

        Returns:
            True if sent successfully, False otherwise
        """
        base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
        register_link = f"{base_url}/register?invite={invite_token}"

        greeting = f"Hi {first_name}," if first_name else "Hi,"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{
            display: inline-block;
            padding: 14px 28px;
            background-color: #4F46E5;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: bold;
            font-size: 16px;
        }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
        .highlight {{ background: #f0f0ff; padding: 16px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>You're In &mdash; Your RivaFlow Access is Ready</h2>
        <p>{greeting}</p>
        <p>Great news! Your spot on the RivaFlow waitlist has come through. You've been selected to join the platform.</p>
        <p>RivaFlow is the training OS for the mat &mdash; built to help you track sessions, measure progress, and train with intent.</p>

        <a href="{register_link}" class="button">Create Your Account</a>

        <p>Or copy and paste this link into your browser:</p>
        <p><a href="{register_link}">{register_link}</a></p>

        <div class="highlight">
            <strong>Important:</strong> This invite link expires in 7 days. Make sure to register before then to claim your spot.
        </div>

        <p>Once you're in, you can:</p>
        <ul>
            <li>Log training sessions in seconds</li>
            <li>Track techniques, rolls, and progress</li>
            <li>Connect with your training partners</li>
            <li>Get insights into your training patterns</li>
        </ul>

        <p>See you on the mat.</p>
        <p><strong>&mdash; The RivaFlow Team</strong></p>

        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""

        text_content = f"""
You're In -- Your RivaFlow Access is Ready

{greeting}

Great news! Your spot on the RivaFlow waitlist has come through. You've been
selected to join the platform.

RivaFlow is the training OS for the mat -- built to help you track sessions,
measure progress, and train with intent.

Create your account here:
{register_link}

IMPORTANT: This invite link expires in 7 days. Make sure to register before
then to claim your spot.

Once you're in, you can:
- Log training sessions in seconds
- Track techniques, rolls, and progress
- Connect with your training partners
- Get insights into your training patterns

See you on the mat.
-- The RivaFlow Team

---
RivaFlow - Training OS for the Mat
"""

        return self.send_email(
            to_email=email,
            subject="You're In \u2014 Your RivaFlow Access is Ready",
            html_content=html_content,
            text_content=text_content,
        )

    def send_drip_day1(self, email: str, first_name: str | None = None) -> bool:
        """Drip email Day 1: Get Started — profile setup, belt, gym."""
        base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
        greeting = f"Hey {first_name}," if first_name else "Hey there,"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #e0e0e0; background-color: #1a1a2e; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 30px 20px; }}
        .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #2a2a4a; margin-bottom: 30px; }}
        .header h1 {{ color: #ffffff; font-size: 24px; margin: 0; }}
        .greeting {{ font-size: 18px; color: #ffffff; margin-bottom: 10px; }}
        .text {{ font-size: 15px; color: #c0c0c0; margin-bottom: 20px; }}
        .step {{ background-color: #2a2a4a; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
        .step-title {{ font-size: 14px; font-weight: 700; color: #ff6b35; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 6px 0; }}
        .step-description {{ font-size: 14px; color: #c0c0c0; margin: 0 0 14px 0; }}
        .button {{ display: inline-block; padding: 10px 22px; background-color: #ff6b35; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #2a2a4a; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>Get Started with RivaFlow</h1></div>
        <p class="greeting">{greeting}</p>
        <p class="text">Welcome to Day 1! Let's get your profile set up so RivaFlow can personalise your experience.</p>
        <div class="step">
            <p class="step-title">Set Up Your Profile</p>
            <p class="step-description">Add your belt rank, gym, and a profile photo. This helps Grapple AI coach you at the right level.</p>
            <a href="{base_url}/profile" class="button">Set Up Profile</a>
        </div>
        <div class="step">
            <p class="step-title">Log Your Belt</p>
            <p class="step-description">Record your current belt and any stripes. Your belt progression is tracked over time.</p>
            <a href="{base_url}/profile" class="button">Log Your Belt</a>
        </div>
        <div class="footer">
            <p>RivaFlow &mdash; Training OS for the Mat</p>
        </div>
    </div>
</body>
</html>"""

        text_content = f"""Get Started with RivaFlow

{greeting}

Welcome to Day 1! Let's get your profile set up.

1. SET UP YOUR PROFILE
   Add your belt rank, gym, and photo.
   {base_url}/profile

2. LOG YOUR BELT
   Record your current belt and stripes.
   {base_url}/profile

---
RivaFlow - Training OS for the Mat"""

        return self.send_email(
            to_email=email,
            subject="Day 1: Get Your Profile Set Up",
            html_content=html_content,
            text_content=text_content,
        )

    def send_drip_day3(self, email: str, first_name: str | None = None) -> bool:
        """Drip email Day 3: Track Your Training."""
        base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
        greeting = f"Hey {first_name}," if first_name else "Hey there,"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #e0e0e0; background-color: #1a1a2e; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 30px 20px; }}
        .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #2a2a4a; margin-bottom: 30px; }}
        .header h1 {{ color: #ffffff; font-size: 24px; margin: 0; }}
        .greeting {{ font-size: 18px; color: #ffffff; margin-bottom: 10px; }}
        .text {{ font-size: 15px; color: #c0c0c0; margin-bottom: 20px; }}
        .step {{ background-color: #2a2a4a; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
        .step-title {{ font-size: 14px; font-weight: 700; color: #ff6b35; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 6px 0; }}
        .step-description {{ font-size: 14px; color: #c0c0c0; margin: 0 0 14px 0; }}
        .button {{ display: inline-block; padding: 10px 22px; background-color: #ff6b35; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #2a2a4a; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>Track Your Training</h1></div>
        <p class="greeting">{greeting}</p>
        <p class="text">Ready to start logging? Quick Log takes less than 30 seconds. The more you log, the smarter your analytics become.</p>
        <div class="step">
            <p class="step-title">Log a Session</p>
            <p class="step-description">Use Quick Log for speed or Full Log for detail. Track techniques, rolls, partners, and more.</p>
            <a href="{base_url}/log" class="button">Log a Session</a>
        </div>
        <div class="step">
            <p class="step-title">Check Your Readiness</p>
            <p class="step-description">Rate your sleep, stress, soreness, and energy daily. RivaFlow gives personalised training suggestions.</p>
            <a href="{base_url}/readiness" class="button">Check Readiness</a>
        </div>
        <div class="footer">
            <p>RivaFlow &mdash; Training OS for the Mat</p>
        </div>
    </div>
</body>
</html>"""

        text_content = f"""Track Your Training

{greeting}

Ready to start logging? Quick Log takes less than 30 seconds.

1. LOG A SESSION
   Use Quick Log for speed or Full Log for detail.
   {base_url}/log

2. CHECK YOUR READINESS
   Rate sleep, stress, soreness, and energy daily.
   {base_url}/readiness

---
RivaFlow - Training OS for the Mat"""

        return self.send_email(
            to_email=email,
            subject="Day 3: Start Tracking Your Training",
            html_content=html_content,
            text_content=text_content,
        )

    def send_drip_day5(self, email: str, first_name: str | None = None) -> bool:
        """Drip email Day 5: Level Up — partners, Grapple AI, game plans."""
        base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
        greeting = f"Hey {first_name}," if first_name else "Hey there,"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #e0e0e0; background-color: #1a1a2e; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 30px 20px; }}
        .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #2a2a4a; margin-bottom: 30px; }}
        .header h1 {{ color: #ffffff; font-size: 24px; margin: 0; }}
        .greeting {{ font-size: 18px; color: #ffffff; margin-bottom: 10px; }}
        .text {{ font-size: 15px; color: #c0c0c0; margin-bottom: 20px; }}
        .step {{ background-color: #2a2a4a; border-radius: 8px; padding: 20px; margin-bottom: 16px; }}
        .step-title {{ font-size: 14px; font-weight: 700; color: #ff6b35; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 6px 0; }}
        .step-description {{ font-size: 14px; color: #c0c0c0; margin: 0 0 14px 0; }}
        .button {{ display: inline-block; padding: 10px 22px; background-color: #ff6b35; color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #2a2a4a; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>Level Up Your Training</h1></div>
        <p class="greeting">{greeting}</p>
        <p class="text">You're all set up. Now let's unlock the full power of RivaFlow &mdash; connect with partners and get AI coaching.</p>
        <div class="step">
            <p class="step-title">Find Training Partners</p>
            <p class="step-description">Connect with your gym crew. See each other's sessions, give likes, and track who you roll with most.</p>
            <a href="{base_url}/find-friends" class="button">Find Partners</a>
        </div>
        <div class="step">
            <p class="step-title">Try Grapple AI Coach</p>
            <p class="step-description">Your personal BJJ advisor. Ask technique questions, get training insights, and build game plans &mdash; all powered by your data.</p>
            <a href="{base_url}/grapple" class="button">Try Grapple AI</a>
        </div>
        <div class="footer">
            <p>RivaFlow &mdash; Training OS for the Mat</p>
        </div>
    </div>
</body>
</html>"""

        text_content = f"""Level Up Your Training

{greeting}

You're all set up. Now let's unlock the full power of RivaFlow.

1. FIND TRAINING PARTNERS
   Connect with your gym crew.
   {base_url}/find-friends

2. TRY GRAPPLE AI COACH
   Your personal BJJ advisor.
   {base_url}/grapple

---
RivaFlow - Training OS for the Mat"""

        return self.send_email(
            to_email=email,
            subject="Day 5: Level Up with Partners & AI Coaching",
            html_content=html_content,
            text_content=text_content,
        )

    def send_feedback_notification(
        self,
        feedback_id: int,
        category: str,
        subject: str,
        message: str,
        user_email: str,
        user_name: str,
        platform: str = "web",
        url: str | None = None,
    ) -> bool:
        """
        Send notification email to admins about new feedback submission.

        Args:
            feedback_id: Feedback ID
            category: Feedback category (bug, feature, etc.)
            subject: Feedback subject
            message: Feedback message
            user_email: Email of user who submitted feedback
            user_name: Name of user who submitted feedback
            platform: Platform feedback was submitted from
            url: Optional URL where feedback was submitted

        Returns:
            True if email was sent successfully, False otherwise
        """
        # Get admin emails from environment
        admin_emails_str = os.getenv("ADMIN_EMAILS", "")
        if not admin_emails_str:
            logger.warning(
                "No admin emails configured. Set ADMIN_EMAILS to receive feedback notifications."
            )
            return False

        admin_emails = [email.strip() for email in admin_emails_str.split(",")]

        # Get base URL for admin panel link
        base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
        admin_url = f"{base_url}/admin/feedback"

        # Build HTML email
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .badge-bug {{ background: #fee2e2; color: #991b1b; }}
        .badge-feature {{ background: #dbeafe; color: #1e40af; }}
        .badge-improvement {{ background: #d1fae5; color: #065f46; }}
        .badge-question {{ background: #fef3c7; color: #92400e; }}
        .badge-other {{ background: #e5e7eb; color: #374151; }}
        .content {{ background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 20px; }}
        .meta {{ color: #6b7280; font-size: 14px; margin-bottom: 12px; }}
        .subject {{ font-size: 18px; font-weight: 600; margin-bottom: 12px; }}
        .message {{ background: #f9fafb; padding: 16px; border-left: 3px solid #6366f1; border-radius: 4px; white-space: pre-wrap; }}
        .button {{ display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">New Feedback Submission</h2>
        </div>

        <div class="content">
            <div class="meta">
                <strong>Feedback ID:</strong> #{feedback_id}<br>
                <strong>Category:</strong> <span class="badge badge-{category}">{category.upper()}</span><br>
                <strong>Platform:</strong> {platform}<br>
                <strong>User:</strong> {user_name} ({user_email})<br>
                {f'<strong>URL:</strong> {url}<br>' if url else ''}
            </div>

            <div class="subject">{subject}</div>

            <div class="message">{message}</div>

            <a href="{admin_url}" class="button">View in Admin Panel</a>
        </div>

        <div class="footer">
            <p>RivaFlow - Training OS for the Mat</p>
            <p>This is an automated email. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
        """.strip()

        # Build text email
        text_content = f"""
New Feedback Submission on RivaFlow

Feedback ID: #{feedback_id}
Category: {category.upper()}
Platform: {platform}
User: {user_name} ({user_email})
{f'URL: {url}' if url else ''}

Subject:
{subject}

Message:
{message}

---
View and manage this feedback in the admin panel:
{admin_url}

---
RivaFlow - Training OS for the Mat
        """.strip()

        # Send to all admin emails
        success = True
        for admin_email in admin_emails:
            result = self.send_email(
                to_email=admin_email,
                subject=f"[RivaFlow Feedback] New {category.upper()} - {subject}",
                html_content=html_content,
                text_content=text_content,
            )
            if not result:
                success = False

        return success
