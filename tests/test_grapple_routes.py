"""API route tests for the grapple endpoints."""

from datetime import date
from unittest.mock import AsyncMock, patch

from rivaflow.core.auth import create_access_token, hash_password
from rivaflow.db.repositories.user_repo import UserRepository


def _make_beta_user(temp_db):
    """Create a beta-tier user for grapple access."""
    user_repo = UserRepository()
    user = user_repo.create(
        email="beta@example.com",
        hashed_password=hash_password("TestPass123!secure"),
        first_name="Beta",
        last_name="User",
        subscription_tier="beta",
        is_beta_user=True,
    )
    return user


def _make_beta_headers(user):
    """Create auth headers for a beta user."""
    token = create_access_token(data={"sub": str(user["id"])})
    return {"Authorization": f"Bearer {token}"}


class TestGrappleExtractSession:
    """Tests for POST /api/v1/grapple/extract-session."""

    def test_extract_session_success(self, client, temp_db):
        """Test extracting session data from text."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        mock_result = {
            "class_type": "gi",
            "gym_name": "Test Gym",
            "duration_mins": 60,
            "intensity": 4,
            "rolls": 3,
            "events": [],
            "_llm_tokens": 100,
            "_llm_cost": 0.0,
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
                json={"text": "Did 3 rolls at Test Gym today"},
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["class_type"] == "gi"
        assert data["gym_name"] == "Test Gym"

    def test_extract_session_llm_unavailable(self, client, temp_db):
        """Test 503 when LLM service is unavailable."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        with patch(
            "rivaflow.core.services.grapple"
            ".session_extraction_service"
            ".extract_session_from_text",
            new_callable=AsyncMock,
            side_effect=RuntimeError("No LLM providers"),
        ):
            resp = client.post(
                "/api/v1/grapple/extract-session",
                json={"text": "Some session text"},
                headers=headers,
            )

        assert resp.status_code == 503

    def test_extract_session_free_user_denied(self, client, test_user, auth_headers):
        """Test free-tier user is denied grapple access."""
        resp = client.post(
            "/api/v1/grapple/extract-session",
            json={"text": "Some session text"},
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestGrappleSaveExtractedSession:
    """Tests for POST /api/v1/grapple/save-extracted-session."""

    def test_save_extracted_session(self, client, temp_db):
        """Test saving an extracted session."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        resp = client.post(
            "/api/v1/grapple/save-extracted-session",
            json={
                "session_date": date.today().isoformat(),
                "class_type": "gi",
                "gym_name": "Test Gym",
                "duration_mins": 60,
                "intensity": 4,
                "rolls": 3,
                "submissions_for": 1,
                "submissions_against": 0,
                "partners": ["Alice"],
                "techniques": ["armbar"],
                "notes": "Good session",
                "events": [
                    {
                        "event_type": "submission",
                        "technique_name": "armbar",
                        "outcome": "success",
                    }
                ],
            },
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["session_id"] > 0

    def test_save_extracted_session_no_events(self, client, temp_db):
        """Test saving an extracted session without events."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        resp = client.post(
            "/api/v1/grapple/save-extracted-session",
            json={
                "session_date": date.today().isoformat(),
                "class_type": "no-gi",
                "gym_name": "Local Gym",
            },
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] > 0


class TestGrappleInsights:
    """Tests for /api/v1/grapple/insights endpoints."""

    def test_list_insights_empty(self, client, temp_db):
        """Test listing insights when none exist."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        resp = client.get(
            "/api/v1/grapple/insights",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["insights"] == []
        assert data["count"] == 0

    def test_generate_insight_post_session(self, client, temp_db):
        """Test generating a post-session insight."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        mock_insight = {
            "id": 1,
            "user_id": user["id"],
            "insight_type": "post_session",
            "title": "Great Progress",
            "content": "Your guard work is improving.",
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
        assert data["title"] == "Great Progress"

    def test_generate_weekly_insight(self, client, temp_db):
        """Test generating a weekly insight."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        mock_insight = {
            "id": 2,
            "user_id": user["id"],
            "insight_type": "weekly",
            "title": "Weekly Summary",
            "content": "Consistent training pattern.",
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

    def test_generate_insight_invalid_type(self, client, temp_db):
        """Test invalid insight_type returns 400."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        resp = client.post(
            "/api/v1/grapple/insights/generate",
            json={"insight_type": "invalid_type"},
            headers=headers,
        )

        assert resp.status_code == 400

    def test_generate_insight_not_found(self, client, temp_db):
        """Test 404 when insight generation returns None."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

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


class TestGrappleTechniqueQA:
    """Tests for POST /api/v1/grapple/technique-qa."""

    def test_technique_qa_success(self, client, temp_db):
        """Test technique Q&A endpoint."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

        mock_result = {
            "answer": "The armbar is a joint lock...",
            "sources": [
                {
                    "id": 1,
                    "name": "Armbar",
                    "category": "submission",
                }
            ],
            "tokens_used": 200,
            "cost_usd": 0.0,
        }

        with patch(
            "rivaflow.core.services.grapple" ".glossary_rag_service.technique_qa",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/v1/grapple/technique-qa",
                json={"question": "How do I do an armbar?"},
                headers=headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "sources" in data

    def test_technique_qa_llm_unavailable(self, client, temp_db):
        """Test 503 when LLM is unavailable for Q&A."""
        user = _make_beta_user(temp_db)
        headers = _make_beta_headers(user)

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


class TestGrappleTeaser:
    """Tests for public grapple info endpoints."""

    def test_grapple_teaser(self, authenticated_client, test_user):
        """Test GET /api/v1/grapple/teaser for free user."""
        resp = authenticated_client.get("/api/v1/grapple/teaser")
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_access"] is False
        assert data["current_tier"] == "free"
        assert "grapple_features" in data

    def test_grapple_info(self, authenticated_client, test_user):
        """Test GET /api/v1/grapple/info."""
        resp = authenticated_client.get("/api/v1/grapple/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "tier" in data
        assert "features" in data
        assert "limits" in data
