"""Transactional email sending functions.

Each function builds content from templates and dispatches via an
EmailService instance.  They are mixed back into ``EmailService``
so existing callers (``EmailService().send_welcome_email(...)``)
continue to work unchanged.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from rivaflow.core.services.email_drip_templates import (
    coach_settings_reminder_template,
    drip_day1_template,
    drip_day3_template,
    drip_day5_template,
    feedback_notification_template,
)
from rivaflow.core.services.email_templates import (
    password_changed_template,
    password_reset_template,
    waitlist_invite_template,
    welcome_template,
)

if TYPE_CHECKING:
    from rivaflow.core.services.email_service import EmailService

logger = logging.getLogger(__name__)


def send_password_reset_email(
    self: EmailService,
    to_email: str,
    reset_token: str,
    user_name: str | None = None,
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
    base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
    reset_link = f"{base_url}/reset-password?token={reset_token}"
    greeting = f"Hi {user_name}," if user_name else "Hi,"

    html_content, text_content = password_reset_template(reset_link, greeting)

    return self.send_email(
        to_email=to_email,
        subject="Reset Your RivaFlow Password",
        html_content=html_content,
        text_content=text_content,
    )


def send_password_changed_confirmation(
    self: EmailService,
    to_email: str,
    user_name: str | None = None,
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

    html_content, text_content = password_changed_template(greeting)

    return self.send_email(
        to_email=to_email,
        subject="Your RivaFlow Password Was Changed",
        html_content=html_content,
        text_content=text_content,
    )


def send_welcome_email(
    self: EmailService,
    email: str,
    first_name: str | None = None,
) -> bool:
    """
    Send welcome email to a newly registered user.

    Args:
        email: User's email address
        first_name: User's first name (optional)

    Returns:
        True if sent successfully, False otherwise
    """
    base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
    greeting = f"Hey {first_name}," if first_name else "Hey there,"

    html_content, text_content = welcome_template(greeting, base_url)

    return self.send_email(
        to_email=email,
        subject="Welcome to RivaFlow \u2014 Let's Get You Started",
        html_content=html_content,
        text_content=text_content,
    )


def send_waitlist_invite_email(
    self: EmailService,
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

    html_content, text_content = waitlist_invite_template(register_link, greeting)

    return self.send_email(
        to_email=email,
        subject="You're In \u2014 Your RivaFlow Access is Ready",
        html_content=html_content,
        text_content=text_content,
    )


def send_drip_day1(
    self: EmailService,
    email: str,
    first_name: str | None = None,
) -> bool:
    """Drip email Day 1: Get Started -- profile setup, belt, gym."""
    base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
    greeting = f"Hey {first_name}," if first_name else "Hey there,"

    html_content, text_content = drip_day1_template(greeting, base_url)

    return self.send_email(
        to_email=email,
        subject="Day 1: Get Your Profile Set Up",
        html_content=html_content,
        text_content=text_content,
    )


def send_drip_day3(
    self: EmailService,
    email: str,
    first_name: str | None = None,
) -> bool:
    """Drip email Day 3: Track Your Training."""
    base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
    greeting = f"Hey {first_name}," if first_name else "Hey there,"

    html_content, text_content = drip_day3_template(greeting, base_url)

    return self.send_email(
        to_email=email,
        subject="Day 3: Start Tracking Your Training",
        html_content=html_content,
        text_content=text_content,
    )


def send_drip_day5(
    self: EmailService,
    email: str,
    first_name: str | None = None,
) -> bool:
    """Drip email Day 5: Level Up -- partners, Grapple AI, game plans."""
    base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
    greeting = f"Hey {first_name}," if first_name else "Hey there,"

    html_content, text_content = drip_day5_template(greeting, base_url)

    return self.send_email(
        to_email=email,
        subject="Day 5: Level Up with Partners & AI Coaching",
        html_content=html_content,
        text_content=text_content,
    )


def send_feedback_notification(
    self: EmailService,
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
    admin_emails_str = os.getenv("ADMIN_EMAILS", "")
    if not admin_emails_str:
        logger.warning(
            "No admin emails configured. Set ADMIN_EMAILS to "
            "receive feedback notifications."
        )
        return False

    admin_emails = [email.strip() for email in admin_emails_str.split(",")]

    base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
    admin_url = f"{base_url}/admin/feedback"

    html_content, text_content = feedback_notification_template(
        feedback_id=feedback_id,
        category=category,
        subject=subject,
        message=message,
        user_email=user_email,
        user_name=user_name,
        platform=platform,
        url=url,
        admin_url=admin_url,
    )

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


def send_coach_settings_reminder(
    self: EmailService,
    email: str,
    first_name: str | None = None,
) -> bool:
    """Send a reminder to review Coach Settings (every ~10 weeks)."""
    base_url = os.getenv("APP_BASE_URL", "https://rivaflow.app")
    greeting = f"Hey {first_name}," if first_name else "Hey there,"

    html_content, text_content = coach_settings_reminder_template(greeting, base_url)

    return self.send_email(
        to_email=email,
        subject="Time to Review Your Coach Settings",
        html_content=html_content,
        text_content=text_content,
    )
