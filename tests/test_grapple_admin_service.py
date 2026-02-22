"""Tests for GrappleAdminService — admin monitoring and feedback."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from rivaflow.core.exceptions import NotFoundError
from rivaflow.core.services.chat_service import ChatService
from rivaflow.core.services.grapple_admin_service import (
    GrappleAdminService,
)
from rivaflow.db.database import convert_query, get_connection

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _insert_token_usage_log(
    user_id,
    session_id=None,
    provider="anthropic",
    model="claude-3",
    input_tokens=100,
    output_tokens=50,
    cost_usd=0.01,
):
    """Insert a token_usage_logs row for testing."""
    log_id = str(uuid4())
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "INSERT INTO token_usage_logs "
                "(id, user_id, session_id, provider, model, "
                "input_tokens, output_tokens, total_tokens, cost_usd) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            (
                log_id,
                user_id,
                session_id,
                provider,
                model,
                input_tokens,
                output_tokens,
                input_tokens + output_tokens,
                cost_usd,
            ),
        )
    return log_id


def _set_subscription_tier(user_id, tier):
    """Set a user's subscription tier."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("UPDATE users SET subscription_tier = ? WHERE id = ?"),
            (tier, user_id),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# submit_feedback
# ---------------------------------------------------------------------------


def test_submit_feedback(temp_db, test_user):
    """submit_feedback stores and returns feedback with id and message."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])
    msg = svc.create_message(session["id"], "assistant", "Here is some advice.")

    result = GrappleAdminService.submit_feedback(
        user_id=test_user["id"],
        message_id=msg["id"],
        rating="positive",
        category="helpful",
        comment="Great answer!",
    )

    assert "feedback_id" in result
    assert result["message"] == "Thank you for your feedback!"


def test_submit_feedback_nonexistent_message(temp_db, test_user):
    """submit_feedback raises NotFoundError for missing message."""
    with pytest.raises(NotFoundError):
        GrappleAdminService.submit_feedback(
            user_id=test_user["id"],
            message_id="00000000-0000-0000-0000-000000000000",
            rating="negative",
        )


def test_submit_feedback_wrong_user(temp_db, test_user, test_user2):
    """submit_feedback denies access for non-owner."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])
    msg = svc.create_message(session["id"], "assistant", "Some advice.")

    with pytest.raises(NotFoundError):
        GrappleAdminService.submit_feedback(
            user_id=test_user2["id"],
            message_id=msg["id"],
            rating="positive",
        )


def test_submit_feedback_user_message_rejected(temp_db, test_user):
    """submit_feedback rejects feedback on user (non-assistant) messages."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])
    msg = svc.create_message(session["id"], "user", "My question")

    with pytest.raises(NotFoundError):
        GrappleAdminService.submit_feedback(
            user_id=test_user["id"],
            message_id=msg["id"],
            rating="positive",
        )


# ---------------------------------------------------------------------------
# get_feedback
# ---------------------------------------------------------------------------


def test_get_feedback(temp_db, test_user):
    """get_feedback lists stored feedback entries."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])
    msg1 = svc.create_message(session["id"], "assistant", "Advice 1")
    msg2 = svc.create_message(session["id"], "assistant", "Advice 2")

    GrappleAdminService.submit_feedback(
        user_id=test_user["id"],
        message_id=msg1["id"],
        rating="positive",
    )
    GrappleAdminService.submit_feedback(
        user_id=test_user["id"],
        message_id=msg2["id"],
        rating="negative",
        comment="Not helpful",
    )

    result = GrappleAdminService.get_feedback()

    assert result["total_returned"] == 2
    assert len(result["feedback"]) == 2
    ratings = {f["rating"] for f in result["feedback"]}
    assert ratings == {"positive", "negative"}


def test_get_feedback_filtered_by_rating(temp_db, test_user):
    """get_feedback with rating filter returns only matching entries."""
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])
    msg1 = svc.create_message(session["id"], "assistant", "Good")
    msg2 = svc.create_message(session["id"], "assistant", "Bad")

    GrappleAdminService.submit_feedback(
        user_id=test_user["id"],
        message_id=msg1["id"],
        rating="positive",
    )
    GrappleAdminService.submit_feedback(
        user_id=test_user["id"],
        message_id=msg2["id"],
        rating="negative",
    )

    result = GrappleAdminService.get_feedback(rating="positive")

    assert result["total_returned"] == 1
    assert result["feedback"][0]["rating"] == "positive"


# ---------------------------------------------------------------------------
# get_global_stats (mocked token monitor)
# ---------------------------------------------------------------------------


@patch("rivaflow.core.services.grapple.token_monitor.GrappleTokenMonitor")
def test_get_global_stats(MockMonitorCls, temp_db, test_user):
    """get_global_stats combines token monitor + repo data."""
    # Create some chat data
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])
    svc.create_message(session["id"], "user", "Hello")
    svc.create_message(session["id"], "assistant", "Hi there")

    # Mock the token monitor instance
    mock_monitor = MagicMock()
    mock_monitor.get_global_usage_stats.return_value = {
        "totals": {
            "unique_users": 5,
            "total_tokens": 10000,
            "total_cost_usd": 1.50,
        },
        "by_provider": {"anthropic": {"tokens": 10000}},
    }
    MockMonitorCls.return_value = mock_monitor

    result = GrappleAdminService.get_global_stats(days=30)

    assert result["total_users"] == 5
    assert result["total_tokens"] == 10000
    assert result["total_cost_usd"] == 1.50
    assert result["total_sessions"] >= 1
    assert result["total_messages"] >= 2
    assert "by_provider" in result
    assert "by_tier" in result


# ---------------------------------------------------------------------------
# get_projections (mocked repo data)
# ---------------------------------------------------------------------------


def test_get_projections(temp_db, test_user, monkeypatch):
    """get_projections returns cost projection structure."""
    # Insert token usage to give the repo something to aggregate
    _set_subscription_tier(test_user["id"], "beta")
    svc = ChatService()
    session = svc.create_session(user_id=test_user["id"])
    _insert_token_usage_log(
        user_id=test_user["id"],
        session_id=session["id"],
        cost_usd=0.05,
    )

    result = GrappleAdminService.get_projections()

    assert "current_month" in result
    assert "daily_average" in result
    assert "calculated_at" in result
    cm = result["current_month"]
    assert "cost_so_far" in cm
    assert "projected_total" in cm
    assert "days_elapsed" in cm
    assert "days_remaining" in cm


# ---------------------------------------------------------------------------
# check_health (mocked LLM client)
# ---------------------------------------------------------------------------


@patch("rivaflow.core.services.grapple.llm_client.GrappleLLMClient")
def test_check_health_healthy(MockLLMCls, temp_db):
    """check_health returns healthy when LLM and DB are fine."""
    mock_llm = MagicMock()
    mock_llm.get_provider_status.return_value = {"anthropic": "available"}
    MockLLMCls.return_value = mock_llm

    result = GrappleAdminService.check_health()

    assert result["overall_status"] == "healthy"
    assert result["llm_client"]["status"] == "healthy"
    assert result["database"]["status"] == "healthy"
    assert "checked_at" in result


@patch("rivaflow.core.services.grapple.llm_client.GrappleLLMClient")
def test_check_health_degraded_llm(MockLLMCls, temp_db):
    """check_health returns degraded when LLM client fails."""
    MockLLMCls.side_effect = RuntimeError("LLM unavailable")

    result = GrappleAdminService.check_health()

    assert result["overall_status"] == "degraded"
    assert result["llm_client"]["status"] == "error"
