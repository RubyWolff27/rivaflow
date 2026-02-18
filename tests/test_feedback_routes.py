"""Integration tests for feedback routes."""


class TestSubmitFeedback:
    """Tests for POST /api/v1/feedback/."""

    def test_submit_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.post(
            "/api/v1/feedback/",
            json={
                "category": "bug",
                "message": "Something is broken in the app.",
            },
        )
        assert resp.status_code == 401

    def test_submit_bug_report(self, authenticated_client, test_user):
        """Can submit a bug report."""
        resp = authenticated_client.post(
            "/api/v1/feedback/",
            json={
                "category": "bug",
                "subject": "Login issue",
                "message": "Cannot log in after password reset attempt.",
                "platform": "web",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "bug"

    def test_submit_feature_request(self, authenticated_client, test_user):
        """Can submit a feature request."""
        resp = authenticated_client.post(
            "/api/v1/feedback/",
            json={
                "category": "feature",
                "message": "Please add a dark mode option to the app.",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["category"] == "feature"

    def test_submit_invalid_category(self, authenticated_client, test_user):
        """Invalid category returns 422 validation error."""
        resp = authenticated_client.post(
            "/api/v1/feedback/",
            json={
                "category": "invalid_cat",
                "message": "This should fail validation.",
            },
        )
        assert resp.status_code == 422

    def test_submit_message_too_short(self, authenticated_client, test_user):
        """Message under 10 characters returns 422."""
        resp = authenticated_client.post(
            "/api/v1/feedback/",
            json={
                "category": "bug",
                "message": "Short",
            },
        )
        assert resp.status_code == 422

    def test_submit_with_all_optional_fields(self, authenticated_client, test_user):
        """Can submit feedback with all optional fields."""
        resp = authenticated_client.post(
            "/api/v1/feedback/",
            json={
                "category": "improvement",
                "subject": "Better charts",
                "message": "The analytics charts could use more detail and filters.",
                "platform": "web",
                "version": "1.2.3",
                "url": "https://app.rivaflow.app/analytics",
            },
        )
        assert resp.status_code == 201
        fb = resp.json()
        assert fb["subject"] == "Better charts"
        assert fb["platform"] == "web"


class TestGetMyFeedback:
    """Tests for GET /api/v1/feedback/my."""

    def test_my_feedback_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/feedback/my")
        assert resp.status_code == 401

    def test_my_feedback_empty(self, authenticated_client, test_user):
        """Returns empty list when no feedback submitted."""
        resp = authenticated_client.get("/api/v1/feedback/my")
        assert resp.status_code == 200
        data = resp.json()
        assert "feedback" in data
        assert data["count"] == 0

    def test_my_feedback_after_submit(self, authenticated_client, test_user):
        """Returns submitted feedback in user list."""
        authenticated_client.post(
            "/api/v1/feedback/",
            json={
                "category": "question",
                "message": "How do I connect my WHOOP device?",
            },
        )
        resp = authenticated_client.get("/api/v1/feedback/my")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert data["feedback"][0]["category"] == "question"


class TestGetFeedbackById:
    """Tests for GET /api/v1/feedback/{feedback_id}."""

    def test_get_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/feedback/1")
        assert resp.status_code == 401

    def test_get_nonexistent_returns_404(self, authenticated_client, test_user):
        """Returns 404 for feedback that doesn't exist."""
        resp = authenticated_client.get("/api/v1/feedback/999999")
        assert resp.status_code == 404

    def test_get_own_feedback(self, authenticated_client, test_user):
        """Can retrieve own feedback by ID."""
        create_resp = authenticated_client.post(
            "/api/v1/feedback/",
            json={
                "category": "other",
                "message": "Just wanted to say the app is great!",
            },
        )
        feedback_id = create_resp.json()["id"]
        resp = authenticated_client.get(f"/api/v1/feedback/{feedback_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == feedback_id
        assert resp.json()["category"] == "other"
