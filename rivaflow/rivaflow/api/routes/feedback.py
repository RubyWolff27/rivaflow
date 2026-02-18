"""Feedback API endpoints."""

import logging

from fastapi import APIRouter, Depends, Path, Query, Request, status
from pydantic import BaseModel, Field

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.exceptions import NotFoundError, ValidationError
from rivaflow.core.services.email_service import EmailService
from rivaflow.core.services.feedback_service import FeedbackService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    """Feedback creation model."""

    category: str = Field(..., pattern="^(bug|feature|improvement|question|other)$")
    subject: str | None = Field(None, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)
    platform: str | None = Field(None, pattern="^(web|cli|api)$")
    version: str | None = Field(None, max_length=20)
    url: str | None = Field(None, max_length=500)


class FeedbackUpdateStatus(BaseModel):
    """Admin model for updating feedback status."""

    status: str = Field(..., pattern="^(new|reviewing|resolved|closed)$")
    admin_notes: str | None = Field(None, max_length=1000)


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
@route_error_handler("submit_feedback", detail="Failed to submit feedback")
def submit_feedback(
    request: Request,
    feedback: FeedbackCreate,
    current_user: dict = Depends(get_current_user),
):
    """
    Submit feedback about the app.

    Categories:
    - bug: Report a bug or issue
    - feature: Request a new feature
    - improvement: Suggest an improvement
    - question: Ask a question
    - other: Other feedback

    Returns:
        Created feedback submission
    """
    repo = FeedbackService()

    try:
        feedback_id = repo.create(
            user_id=current_user["id"],
            category=feedback.category,
            message=feedback.message,
            subject=feedback.subject,
            platform=feedback.platform,
            version=feedback.version,
            url=feedback.url,
        )

        created = repo.get_by_id(feedback_id)

        # Send email notification to admins (async, don't block on failure)
        try:
            email_service = EmailService()
            user_name = (
                f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip()
                or "Unknown User"
            )
            email_service.send_feedback_notification(
                feedback_id=feedback_id,
                category=feedback.category,
                subject=feedback.subject or "No subject",
                message=feedback.message,
                user_email=current_user.get("email", "unknown@example.com"),
                user_name=user_name,
                platform=feedback.platform or "web",
                url=feedback.url,
            )
        except (ConnectionError, OSError, RuntimeError) as e:
            # Log but don't fail the request if email fails
            logger.warning(f"Failed to send feedback notification email: {str(e)}")

        return created
    except (ConnectionError, OSError, ValueError) as e:
        raise ValidationError(f"Failed to submit feedback: {str(e)}")


@router.get("/my")
@limiter.limit("30/minute")
@route_error_handler("get_my_feedback", detail="Failed to get feedback")
def get_my_feedback(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all feedback submissions from the current user.

    Returns:
        List of user's feedback submissions
    """
    repo = FeedbackService()
    feedback_list = repo.list_by_user(current_user["id"], limit=limit)

    return {
        "feedback": feedback_list,
        "count": len(feedback_list),
    }


@router.get("/{feedback_id}")
@limiter.limit("30/minute")
@route_error_handler("get_feedback_item", detail="Failed to get feedback")
def get_feedback(
    request: Request,
    feedback_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific feedback submission.

    Users can only view their own feedback unless they're an admin.

    Returns:
        Feedback submission
    """
    repo = FeedbackService()
    feedback = repo.get_by_id(feedback_id)

    if not feedback:
        raise NotFoundError("Feedback not found")

    # Check ownership (users can only view their own feedback unless admin)
    is_admin = current_user.get("is_admin", False)
    if feedback["user_id"] != current_user["id"] and not is_admin:
        raise NotFoundError("Feedback not found")

    return feedback
