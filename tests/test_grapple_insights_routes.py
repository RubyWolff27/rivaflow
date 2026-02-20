"""Tests for grapple insights routes (/api/v1/grapple/ insight endpoints)."""

from datetime import date
from unittest.mock import AsyncMock, patch

from rivaflow.core.auth import create_access_token, hash_password
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.user_repo import UserRepository


def _make_premium_user(temp_db):
    """Create a premium-tier user for grapple access."""
    user_repo = UserRepository()
    user = user_repo.create(
        email="premium@example.com",
        hashed_password=hash_password("TestPass123!secure"),
        first_name="Premium",
        last_name="User",
        subscription_tier="premium",
        is_beta_user=True,
    )
    return user


def _make_premium_headers(user):
    """Create auth headers for a premium user."""
    token = create_access_token(data={"sub": str(user["id"])})
    return {"Authorization": f"Bearer {token}"}


def _upgrade_user_to_premium(user_id):
    """Upgrade an existing user to premium tier via DB."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "UPDATE users SET subscription_tier = ?,"
                " is_beta_user = ? WHERE id = ?"
            ),
            ("premium", True, user_id),
        )
        conn.commit()


# ====================================================================
# Authentication & Authorization Tests
# ====================================================================


class TestGrappleInsightsAuth:
    """Auth and tier-gating tests for grapple insight endpoints."""

    def test_extract_session_unauthenticated(self, client, temp_db):
        """POST /extract-session without auth returns 401."""
        resp = client.post(
            "/api/v1/grapple/extract-session",
            json={"text": "Rolled 3 rounds today"},
        )
        assert resp.status_code == 401

    def test_save_extracted_session_unauthenticated(self, client, temp_db):
        """POST /save-extracted-session without auth returns 401."""
        resp = client.post(
            "/api/v1/grapple/save-extracted-session",
            json={"session_date": "2025-01-20"},
        )
        assert resp.status_code == 401

    def test_list_insights_unauthenticated(self, client, temp_db):
        """GET /insights without auth returns 401."""
        resp = client.get("/api/v1/grapple/insights")
        assert resp.status_code == 401

    def test_generate_insight_unauthenticated(self, client, temp_db):
        """POST /insights/generate without auth returns 401."""
        resp = client.post(
            "/api/v1/grapple/insights/generate",
            json={"insight_type": "weekly"},
        )
        assert resp.status_code == 401

    def test_insight_chat_unauthenticated(self, client, temp_db):
        """POST /insights/1/chat without auth returns 401."""
        resp = client.post("/api/v1/grapple/insights/1/chat")
        assert resp.status_code == 401

    def test_technique_qa_unauthenticated(self, client, temp_db):
        """POST /technique-qa without auth returns 401."""
        resp = client.post(
            "/api/v1/grapple/technique-qa",
            json={"question": "What is a kimura?"},
        )
        assert resp.status_code == 401

    def test_extract_session_free_user_denied(self, client, test_user, auth_headers):
        """Free-tier user gets 403 on extract-session."""
        resp = client.post(
            "/api/v1/grapple/extract-session",
            json={"text": "Rolled 3 rounds today"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_save_extracted_session_free_user_denied(
        self, client, test_user, auth_headers
    ):
        """Free-tier user gets 403 on save-extracted-session."""
        resp = client.post(
            "/api/v1/grapple/save-extracted-session",
            json={"session_date": "2025-01-20"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_list_insights_free_user_denied(self, client, test_user, auth_headers):
        """Free-tier user gets 403 on insights list."""
        resp = client.get(
            "/api/v1/grapple/insights",
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_generate_insight_free_user_denied(self, client, test_user, auth_headers):
        """Free-tier user gets 403 on insight generation."""
        resp = client.post(
            "/api/v1/grapple/insights/generate",
            json={"insight_type": "weekly"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_technique_qa_free_user_denied(self, client, test_user, auth_headers):
        """Free-tier user gets 403 on technique-qa."""
        resp = client.post(
            "/api/v1/grapple/technique-qa",
            json={"question": "What is a kimura?"},
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ====================================================================
# Extract Session Endpoint
# ====================================================================


class TestExtractSession:
    """Tests for POST /api/v1/grapple/extract-session."""

    def test_extract_session_premium_success(self, client, temp_db):
        """Premium user can extract a session from text."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_result = {
            "session_date": "2025-01-20",
            "class_type": "gi",
            "gym_name": "Alliance HQ",
            "duration_mins": 90,
            "intensity": 4,
            "rolls": 5,
            "events": [
                {
                    "event_type": "submission",
                    "technique_name": "armbar",
                    "outcome": "success",
                }
            ],
            "_llm_tokens": 150,
            "_llm_cost": 0.001,
        }

        with patch(
            "rivaflow.core.services.grapple"
            ".session_extraction_service"
            ".extract_session_from_text",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/v1/grapple/extract-session",
                json={
                    "text": (
                        "Did 5 rolls at Alliance HQ today, " "got an armbar submission"
                    )
                },
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["class_type"] == "gi"
        assert data["gym_name"] == "Alliance HQ"
        assert data["rolls"] == 5
        assert len(data["events"]) == 1

    def test_extract_session_empty_text(self, client, temp_db):
        """Extract session with empty text still calls service."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_result = {
            "session_date": date.today().isoformat(),
            "class_type": "gi",
            "duration_mins": 60,
            "events": [],
        }

        with patch(
            "rivaflow.core.services.grapple"
            ".session_extraction_service"
            ".extract_session_from_text",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/v1/grapple/extract-session",
                json={"text": "trained today"},
                headers=headers,
            )

        assert resp.status_code == 200

    def test_extract_session_llm_unavailable(self, client, temp_db):
        """503 when LLM service is unavailable."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        with patch(
            "rivaflow.core.services.grapple"
            ".session_extraction_service"
            ".extract_session_from_text",
            new_callable=AsyncMock,
            side_effect=RuntimeError("No LLM providers available"),
        ):
            resp = client.post(
                "/api/v1/grapple/extract-session",
                json={"text": "Some session text"},
                headers=headers,
            )

        assert resp.status_code == 503

    def test_extract_session_upgraded_user(self, client, test_user, auth_headers):
        """User upgraded to premium can access extract-session."""
        _upgrade_user_to_premium(test_user["id"])

        mock_result = {
            "session_date": "2025-01-20",
            "class_type": "no-gi",
            "events": [],
        }

        with patch(
            "rivaflow.core.services.grapple"
            ".session_extraction_service"
            ".extract_session_from_text",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/v1/grapple/extract-session",
                json={"text": "No-gi session today"},
                headers=auth_headers,
            )

        assert resp.status_code == 200
        assert resp.json()["class_type"] == "no-gi"


# ====================================================================
# Save Extracted Session Endpoint
# ====================================================================


class TestSaveExtractedSession:
    """Tests for POST /api/v1/grapple/save-extracted-session."""

    def test_save_session_success(self, client, temp_db):
        """Premium user can save an extracted session."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.post(
            "/api/v1/grapple/save-extracted-session",
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Gracie Barra",
                "duration_mins": 75,
                "intensity": 4,
                "rolls": 4,
                "submissions_for": 2,
                "submissions_against": 1,
                "partners": ["Alice", "Bob"],
                "techniques": ["armbar", "triangle"],
                "notes": "Worked on guard recovery",
                "events": [
                    {
                        "event_type": "submission",
                        "technique_name": "armbar",
                        "outcome": "success",
                        "partner_name": "Alice",
                    }
                ],
            },
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["session_id"] > 0
        assert data["message"] == "Session saved successfully"

    def test_save_session_minimal_data(self, client, temp_db):
        """Save session with only required fields."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.post(
            "/api/v1/grapple/save-extracted-session",
            json={
                "session_date": "2025-02-15",
            },
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] > 0

    def test_save_session_no_events(self, client, temp_db):
        """Save session without events array."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.post(
            "/api/v1/grapple/save-extracted-session",
            json={
                "session_date": date.today().isoformat(),
                "class_type": "no-gi",
                "gym_name": "10th Planet",
                "duration_mins": 60,
                "rolls": 3,
            },
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] > 0

    def test_save_session_invalid_date_format(self, client, temp_db):
        """Invalid date format returns 422 or 500."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.post(
            "/api/v1/grapple/save-extracted-session",
            json={
                "session_date": "not-a-date",
                "class_type": "gi",
            },
            headers=headers,
        )

        # The date.fromisoformat() call will raise ValueError
        # which is caught by route_error_handler -> 500
        assert resp.status_code == 500


# ====================================================================
# List Insights Endpoint
# ====================================================================


class TestListInsights:
    """Tests for GET /api/v1/grapple/insights."""

    def test_list_insights_empty(self, client, temp_db):
        """Premium user gets empty insights list."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.get(
            "/api/v1/grapple/insights",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "insights" in data
        assert "count" in data
        assert data["insights"] == []
        assert data["count"] == 0

    def test_list_insights_response_shape(self, client, temp_db):
        """Response has the expected {insights, count} shape."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.get(
            "/api/v1/grapple/insights",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["insights"], list)
        assert isinstance(data["count"], int)

    def test_list_insights_with_limit(self, client, temp_db):
        """Query param limit is accepted."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.get(
            "/api/v1/grapple/insights?limit=5",
            headers=headers,
        )

        assert resp.status_code == 200

    def test_list_insights_with_type_filter(self, client, temp_db):
        """Query param insight_type is accepted."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.get(
            "/api/v1/grapple/insights?insight_type=weekly",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0


# ====================================================================
# Generate Insight Endpoint
# ====================================================================


class TestGenerateInsight:
    """Tests for POST /api/v1/grapple/insights/generate."""

    def test_generate_post_session_insight(self, client, temp_db):
        """Generate a post-session insight with monkeypatched LLM."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_insight = {
            "id": 1,
            "user_id": user["id"],
            "insight_type": "post_session",
            "title": "Strong Guard Game",
            "content": "Your closed guard is improving.",
            "category": "observation",
        }

        with patch(
            "rivaflow.core.services.grapple"
            ".ai_insight_service"
            ".generate_post_session_insight",
            new_callable=AsyncMock,
            return_value=mock_insight,
        ):
            resp = client.post(
                "/api/v1/grapple/insights/generate",
                json={
                    "insight_type": "post_session",
                    "session_id": 1,
                },
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Strong Guard Game"
        assert data["insight_type"] == "post_session"

    def test_generate_weekly_insight(self, client, temp_db):
        """Generate a weekly insight with monkeypatched LLM."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_insight = {
            "id": 2,
            "user_id": user["id"],
            "insight_type": "weekly",
            "title": "Weekly Roundup",
            "content": "You trained 4 times this week.",
            "category": "pattern",
        }

        with patch(
            "rivaflow.core.services.grapple"
            ".ai_insight_service"
            ".generate_weekly_insight",
            new_callable=AsyncMock,
            return_value=mock_insight,
        ):
            resp = client.post(
                "/api/v1/grapple/insights/generate",
                json={"insight_type": "weekly"},
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Weekly Roundup"

    def test_generate_insight_invalid_type(self, client, temp_db):
        """Invalid insight_type returns 400 (ValidationError)."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.post(
            "/api/v1/grapple/insights/generate",
            json={"insight_type": "nonexistent_type"},
            headers=headers,
        )

        assert resp.status_code == 400

    def test_generate_insight_post_session_no_session_id(self, client, temp_db):
        """post_session without session_id returns 400."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.post(
            "/api/v1/grapple/insights/generate",
            json={"insight_type": "post_session"},
            headers=headers,
        )

        assert resp.status_code == 400

    def test_generate_insight_returns_not_found(self, client, temp_db):
        """404 when generation returns None."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        with patch(
            "rivaflow.core.services.grapple"
            ".ai_insight_service"
            ".generate_post_session_insight",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = client.post(
                "/api/v1/grapple/insights/generate",
                json={
                    "insight_type": "post_session",
                    "session_id": 99999,
                },
                headers=headers,
            )

        assert resp.status_code == 404


# ====================================================================
# Insight Chat Endpoint
# ====================================================================


class TestInsightChat:
    """Tests for POST /api/v1/grapple/insights/{insight_id}/chat."""

    def test_insight_chat_not_found(self, client, temp_db):
        """Chat for nonexistent insight returns 404."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.post(
            "/api/v1/grapple/insights/99999/chat",
            headers=headers,
        )

        assert resp.status_code == 404

    def test_insight_chat_free_user_denied(self, client, test_user, auth_headers):
        """Free user gets 403 on insight chat."""
        resp = client.post(
            "/api/v1/grapple/insights/1/chat",
            headers=auth_headers,
        )
        assert resp.status_code == 403


# ====================================================================
# Technique Q&A Endpoint
# ====================================================================


class TestTechniqueQA:
    """Tests for POST /api/v1/grapple/technique-qa."""

    def test_technique_qa_success(self, client, temp_db):
        """Premium user gets a Q&A response."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        mock_result = {
            "answer": (
                "The kimura is a double-joint shoulder lock "
                "named after Masahiko Kimura."
            ),
            "sources": [
                {
                    "id": 1,
                    "name": "Kimura",
                    "category": "submission",
                }
            ],
            "tokens_used": 180,
            "cost_usd": 0.001,
        }

        with patch(
            "rivaflow.core.services.grapple" ".glossary_rag_service.technique_qa",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/v1/grapple/technique-qa",
                json={"question": "What is a kimura?"},
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "sources" in data
        assert len(data["sources"]) == 1

    def test_technique_qa_llm_unavailable(self, client, temp_db):
        """503 when LLM service is down."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        with patch(
            "rivaflow.core.services.grapple" ".glossary_rag_service.technique_qa",
            new_callable=AsyncMock,
            side_effect=RuntimeError("No LLM providers available"),
        ):
            resp = client.post(
                "/api/v1/grapple/technique-qa",
                json={"question": "What is a triangle choke?"},
                headers=headers,
            )

        assert resp.status_code == 503

    def test_technique_qa_missing_question_field(self, client, temp_db):
        """Missing question field returns 422 validation error."""
        user = _make_premium_user(temp_db)
        headers = _make_premium_headers(user)

        resp = client.post(
            "/api/v1/grapple/technique-qa",
            json={},
            headers=headers,
        )

        assert resp.status_code == 422
