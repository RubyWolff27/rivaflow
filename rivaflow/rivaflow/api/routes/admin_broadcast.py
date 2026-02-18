"""Admin routes for email broadcast."""

import logging
import re
import time

from fastapi import APIRouter, BackgroundTasks, Body, Depends, Request
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import ValidationError
from rivaflow.core.services.audit_service import AuditService

from .admin import get_client_ip, require_admin

logger = logging.getLogger(__name__)

_DANGEROUS_HTML_RE = re.compile(
    r"<\s*(script|iframe|object|embed|form|base|meta|link|svg)\b" r"|on\w+\s*=",
    re.IGNORECASE,
)

router = APIRouter(tags=["admin"])


# Email broadcast
class BroadcastEmailRequest(BaseModel):
    """Request model for admin email broadcast."""

    subject: str = Field(..., min_length=1, max_length=200)
    html_body: str = Field(..., min_length=1, max_length=500_000)
    text_body: str | None = Field(None, max_length=500_000)


def _send_broadcast_background(
    users: list[dict],
    subject: str,
    html_body: str,
    text_body: str | None,
) -> None:
    """Send broadcast emails in a background thread."""
    from rivaflow.core.services.email_service import EmailService

    email_service = EmailService()
    sent = 0
    failed = 0
    for user in users:
        try:
            first_name = user.get("first_name") or ""
            html = html_body.replace("{{first_name}}", first_name)
            text = (
                text_body.replace("{{first_name}}", first_name) if text_body else None
            )
            ok = email_service.send_email(
                to_email=user["email"],
                subject=subject,
                html_content=html,
                text_content=text,
            )
            if ok:
                sent += 1
            else:
                failed += 1
        except Exception:
            failed += 1
            logger.debug(
                "Broadcast email failed for user %s",
                user.get("email"),
                exc_info=True,
            )
        time.sleep(0.1)
    logger.info(
        "Broadcast complete: %d sent, %d failed out of %d",
        sent,
        failed,
        len(users),
    )


@router.post("/email/broadcast")
@limiter.limit("5/hour")
@route_error_handler("broadcast_email", detail="Failed to send broadcast email")
def broadcast_email(
    request: Request,
    background_tasks: BackgroundTasks,
    body: BroadcastEmailRequest = Body(...),
    current_user: dict = Depends(require_admin),
):
    """Send a broadcast email to all active users (admin only)."""
    # Sanitize: reject HTML with dangerous tags/attributes (XSS protection)
    if _DANGEROUS_HTML_RE.search(body.html_body):
        raise ValidationError(
            message="HTML body contains disallowed content",
            action="Remove any script tags, iframes, event handlers, or other dangerous HTML from the email body.",
        )

    from rivaflow.core.services.admin_service import AdminService

    users = AdminService.get_broadcast_users()
    recipient_count = len(users)

    # Audit log
    AuditService.log(
        actor_id=current_user["id"],
        action="email.broadcast",
        target_type="email",
        target_id=None,
        details={
            "subject": body.subject,
            "recipient_count": recipient_count,
        },
        ip_address=get_client_ip(request),
    )

    # Send in background task
    background_tasks.add_task(
        _send_broadcast_background,
        users,
        body.subject,
        body.html_body,
        body.text_body,
    )

    return {
        "message": f"Broadcast queued for {recipient_count} recipients",
        "recipient_count": recipient_count,
    }
