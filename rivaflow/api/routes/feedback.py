"""Feedback API endpoints."""
from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel, Field
from typing import Optional

from rivaflow.db.repositories.feedback_repo import FeedbackRepository
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.exceptions import ValidationError, NotFoundError

router = APIRouter(prefix="/feedback", tags=["feedback"])


class FeedbackCreate(BaseModel):
    """Feedback creation model."""

    category: str = Field(..., pattern="^(bug|feature|improvement|question|other)$")
    subject: Optional[str] = Field(None, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)
    platform: Optional[str] = Field(None, pattern="^(web|cli|api)$")
    version: Optional[str] = Field(None, max_length=20)
    url: Optional[str] = Field(None, max_length=500)


class FeedbackUpdateStatus(BaseModel):
    """Admin model for updating feedback status."""

    status: str = Field(..., pattern="^(new|reviewing|resolved|closed)$")
    admin_notes: Optional[str] = Field(None, max_length=1000)


@router.post("/")
async def submit_feedback(
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
    repo = FeedbackRepository()

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
        return {
            "success": True,
            "feedback": created,
        }
    except Exception as e:
        raise ValidationError(f"Failed to submit feedback: {str(e)}")


@router.get("/my")
async def get_my_feedback(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """
    Get all feedback submissions from the current user.

    Returns:
        List of user's feedback submissions
    """
    repo = FeedbackRepository()
    feedback_list = repo.list_by_user(current_user["id"], limit=limit)

    return {
        "feedback": feedback_list,
        "count": len(feedback_list),
    }


@router.get("/{feedback_id}")
async def get_feedback(
    feedback_id: int = Path(..., gt=0),
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific feedback submission.

    Users can only view their own feedback unless they're an admin.

    Returns:
        Feedback submission
    """
    repo = FeedbackRepository()
    feedback = repo.get_by_id(feedback_id)

    if not feedback:
        raise NotFoundError("Feedback not found")

    # Check ownership (unless admin - add admin check here if needed)
    if feedback["user_id"] != current_user["id"]:
        # TODO: Add admin check
        raise NotFoundError("Feedback not found")

    return feedback
