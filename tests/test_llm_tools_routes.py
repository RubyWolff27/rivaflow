"""Integration tests for LLM tool contract routes.

Note: These endpoints are beta placeholders returning mock data.
The router uses prefix="/llm-tools" but is NOT currently registered
in main.py. We create a minimal FastAPI app to test the handlers
directly, verifying the API contract for when they are enabled.
"""

from datetime import date, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from rivaflow.api.routes.llm_tools import router as llm_tools_router


@pytest.fixture()
def llm_app(temp_db):
    """Minimal FastAPI app with just the llm-tools router mounted."""
    app = FastAPI()
    app.include_router(llm_tools_router, prefix="/api/v1")
    return app


@pytest.fixture()
def llm_client(llm_app):
    """TestClient for the llm-tools app."""
    return TestClient(llm_app)


@pytest.fixture()
def llm_auth_client(llm_app, auth_headers):
    """LLM test client with auth headers."""
    c = TestClient(llm_app)
    c.headers.update(auth_headers)
    return c


class TestWeekReport:
    """Tests for GET /api/v1/llm-tools/report/week."""

    def test_week_report_placeholder(self, llm_auth_client, test_user):
        """Test week report returns placeholder data."""
        week_start = date.today().isoformat()
        response = llm_auth_client.get(
            f"/api/v1/llm-tools/report/week?week_start={week_start}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    def test_week_report_missing_param(self, llm_auth_client, test_user):
        """Test week report requires week_start parameter."""
        response = llm_auth_client.get("/api/v1/llm-tools/report/week")
        assert response.status_code == 422

    def test_week_report_requires_auth(self, llm_client, temp_db):
        """Test week report requires authentication."""
        week_start = date.today().isoformat()
        response = llm_client.get(
            f"/api/v1/llm-tools/report/week?week_start={week_start}"
        )
        assert response.status_code in (401, 403)

    def test_week_report_invalid_date(self, llm_auth_client, test_user):
        """Test week report with invalid date format."""
        response = llm_auth_client.get(
            "/api/v1/llm-tools/report/week?week_start=not-a-date"
        )
        assert response.status_code == 422

    def test_week_report_summary_contains_date(self, llm_auth_client, test_user):
        """Test placeholder summary references the requested week."""
        week_start = date.today().isoformat()
        response = llm_auth_client.get(
            f"/api/v1/llm-tools/report/week?week_start={week_start}"
        )
        assert response.status_code == 200
        data = response.json()
        assert week_start in data["summary"]


class TestPartnersSummary:
    """Tests for GET /api/v1/llm-tools/partners/summary."""

    def test_partners_summary_placeholder(self, llm_auth_client, test_user):
        """Test partners summary returns placeholder data."""
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = llm_auth_client.get(
            f"/api/v1/llm-tools/partners/summary?start={start}&end={end}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "partners" in data
        assert isinstance(data["partners"], list)

    def test_partners_summary_missing_params(self, llm_auth_client, test_user):
        """Test partners summary requires start and end parameters."""
        response = llm_auth_client.get("/api/v1/llm-tools/partners/summary")
        assert response.status_code == 422

    def test_partners_summary_requires_auth(self, llm_client, temp_db):
        """Test partners summary requires authentication."""
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = llm_client.get(
            f"/api/v1/llm-tools/partners/summary?start={start}&end={end}"
        )
        assert response.status_code in (401, 403)

    def test_partners_summary_has_partner_entries(self, llm_auth_client, test_user):
        """Test placeholder partners list contains at least one entry."""
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        response = llm_auth_client.get(
            f"/api/v1/llm-tools/partners/summary?start={start}&end={end}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["partners"]) >= 1
