"""Integration tests for chat routes (Ollama LLM proxy)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from rivaflow.api.main import app
from rivaflow.api.routes.chat import router as chat_router


@pytest.fixture(autouse=True)
def _mount_chat_router():
    """Temporarily mount chat router for tests.

    The chat router is not mounted in the main app by default,
    so we add it for the duration of each test and remove it
    after.
    """
    app.include_router(chat_router, prefix="/api/v1")
    yield
    # Remove the last-added route (the chat router)
    app.routes[:] = [
        r for r in app.routes if not getattr(r, "path", "").startswith("/api/v1/chat")
    ]


@pytest.fixture
def chat_client(temp_db):
    """TestClient that includes the chat router."""
    return TestClient(app)


@pytest.fixture
def authed_chat_client(chat_client, auth_headers):
    """Chat TestClient with authentication headers."""
    chat_client.headers.update(auth_headers)
    return chat_client


class TestChatEndpoint:
    """Tests for POST /api/v1/chat/."""

    def test_chat_requires_auth(self, chat_client, temp_db):
        """Unauthenticated request returns 401."""
        resp = chat_client.post(
            "/api/v1/chat/",
            json={"messages": [{"role": "user", "content": "What is a kimura?"}]},
        )
        assert resp.status_code == 401

    def test_chat_returns_503_when_disabled(self, authed_chat_client, test_user):
        """Returns 503 when CHAT_ENABLED is false."""
        with patch("rivaflow.api.routes.chat.CHAT_ENABLED", False):
            resp = authed_chat_client.post(
                "/api/v1/chat/",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello",
                        }
                    ]
                },
            )
            assert resp.status_code == 503
            body = resp.json()
            # Custom exception handler nests under "error"
            err = body.get("error", body)
            msg = err.get("message") or body.get("detail", "")
            assert "unavailable" in msg.lower()

    def test_chat_returns_503_when_ollama_unreachable(
        self, authed_chat_client, test_user
    ):
        """Returns 503 when Ollama service is not running."""
        # Default Ollama URL (localhost:11434) is not running in test
        resp = authed_chat_client.post(
            "/api/v1/chat/",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
        # Should get 503 (ConnectError) or 504 (timeout)
        assert resp.status_code in (502, 503, 504)

    def test_chat_with_mocked_ollama_success(self, authed_chat_client, test_user):
        """Returns LLM reply when Ollama responds successfully."""
        # Use MagicMock for response so .json() is synchronous
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "A kimura is a shoulder lock."}
        }

        with patch("rivaflow.api.routes.chat.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            resp = authed_chat_client.post(
                "/api/v1/chat/",
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": "What is a kimura?",
                        }
                    ]
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "reply" in data
            assert "kimura" in data["reply"].lower()

    def test_chat_empty_messages_rejected(self, authed_chat_client, test_user):
        """Empty messages list is handled gracefully."""
        # The endpoint should still work (Ollama handles it)
        # but we expect connection error since no Ollama
        resp = authed_chat_client.post(
            "/api/v1/chat/",
            json={"messages": []},
        )
        # Either validation error or Ollama connection error
        assert resp.status_code in (400, 422, 502, 503, 504)

    def test_chat_invalid_body_returns_422(self, authed_chat_client, test_user):
        """Missing required fields returns 422."""
        resp = authed_chat_client.post(
            "/api/v1/chat/",
            json={"invalid": "body"},
        )
        assert resp.status_code == 422

    def test_chat_message_requires_role_and_content(
        self, authed_chat_client, test_user
    ):
        """Message without role or content returns 422."""
        resp = authed_chat_client.post(
            "/api/v1/chat/",
            json={"messages": [{"content": "Hello"}]},
        )
        assert resp.status_code == 422
