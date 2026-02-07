"""Tests for the httpx-based GrappleLLMClient."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from rivaflow.core.services.grapple.llm_client import (
    GrappleLLMClient,
)


class TestProviderDetection:
    """Tests for provider detection logic."""

    def test_no_providers_when_no_keys(self):
        """Test that no providers are available without API keys."""
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "",
                "TOGETHER_API_KEY": "",
            },
            clear=False,
        ):
            # Remove any existing keys
            env = os.environ.copy()
            env.pop("GROQ_API_KEY", None)
            env.pop("TOGETHER_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                client = GrappleLLMClient(environment="production")
                assert client.providers == []

    def test_groq_detected_in_production(self):
        """Test groq provider is detected in production."""
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "test-key"},
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")
            assert "groq" in client.providers

    def test_together_detected_in_production(self):
        """Test together provider is detected in production."""
        with patch.dict(
            os.environ,
            {"TOGETHER_API_KEY": "test-key"},
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")
            assert "together" in client.providers

    def test_ollama_checked_in_development(self):
        """Test ollama is checked in development mode."""
        with patch.dict(
            os.environ,
            {},
            clear=False,
        ):
            env = os.environ.copy()
            env.pop("GROQ_API_KEY", None)
            env.pop("TOGETHER_API_KEY", None)
            with patch.dict(os.environ, env, clear=True):
                with patch.object(
                    GrappleLLMClient,
                    "_check_ollama_available",
                    return_value=False,
                ):
                    client = GrappleLLMClient(environment="development")
                    assert client.providers == []

    def test_ollama_added_when_available(self):
        """Test ollama is added when running locally."""
        env = os.environ.copy()
        env.pop("GROQ_API_KEY", None)
        env.pop("TOGETHER_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            with patch.object(
                GrappleLLMClient,
                "_check_ollama_available",
                return_value=True,
            ):
                client = GrappleLLMClient(environment="development")
                assert "ollama" in client.providers


class TestCostCalculation:
    """Tests for cost calculation."""

    def test_groq_cost_is_free(self):
        """Groq free tier should return 0 cost."""
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "test-key"},
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")
            cost = client._calculate_cost("groq", 1000, 1000)
            assert cost == 0.0

    def test_together_cost_calculation(self):
        """Test together cost calculation."""
        with patch.dict(
            os.environ,
            {"TOGETHER_API_KEY": "test-key"},
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")
            cost = client._calculate_cost("together", 1000, 1000)
            # 0.0009 * 1 + 0.0009 * 1 = 0.0018
            assert cost == 0.0018

    def test_unknown_provider_cost(self):
        """Test unknown provider returns 0 cost."""
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "test-key"},
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")
            cost = client._calculate_cost("unknown_provider", 1000, 1000)
            assert cost == 0.0


class TestProviderStatus:
    """Tests for get_provider_status."""

    def test_provider_status_structure(self):
        """Test provider status returns correct structure."""
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "test-key"},
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")
            status = client.get_provider_status()
            assert "available_providers" in status
            assert "primary_provider" in status
            assert "models" in status
            assert "environment" in status
            assert status["primary_provider"] == "groq"

    def test_provider_status_no_providers(self):
        """Test provider status when none configured."""
        env = os.environ.copy()
        env.pop("GROQ_API_KEY", None)
        env.pop("TOGETHER_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            client = GrappleLLMClient(environment="production")
            status = client.get_provider_status()
            assert status["primary_provider"] is None


class TestChatFallback:
    """Tests for chat with provider fallback."""

    @pytest.mark.asyncio
    async def test_chat_no_providers_raises(self):
        """Test chat raises when no providers available."""
        env = os.environ.copy()
        env.pop("GROQ_API_KEY", None)
        env.pop("TOGETHER_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            client = GrappleLLMClient(environment="production")
            with pytest.raises(RuntimeError, match="No LLM"):
                await client.chat(
                    messages=[{"role": "user", "content": "Hi"}],
                    user_id=1,
                )

    @pytest.mark.asyncio
    async def test_chat_groq_success(self):
        """Test successful chat via groq provider."""
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "test-key"},
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Hello from groq!"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                },
            }

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await client.chat(
                    messages=[{"role": "user", "content": "Hi"}],
                    user_id=1,
                )

            assert result["content"] == "Hello from groq!"
            assert result["provider"] == "groq"
            assert result["input_tokens"] == 10
            assert result["output_tokens"] == 5
            assert result["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_chat_falls_back_to_together(self):
        """Test fallback from groq to together on failure."""
        with patch.dict(
            os.environ,
            {
                "GROQ_API_KEY": "groq-key",
                "TOGETHER_API_KEY": "together-key",
            },
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")

            mock_success = MagicMock()
            mock_success.status_code = 200
            mock_success.raise_for_status = MagicMock()
            mock_success.json.return_value = {
                "choices": [{"message": {"content": "Hello from together!"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                },
            }

            call_count = 0

            async def mock_post(url, **kwargs):
                nonlocal call_count
                call_count += 1
                if "groq" in url:
                    raise httpx.HTTPStatusError(
                        "Server error",
                        request=MagicMock(),
                        response=MagicMock(status_code=500),
                    )
                return mock_success

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = mock_post

            with patch("httpx.AsyncClient", return_value=mock_client):
                result = await client.chat(
                    messages=[{"role": "user", "content": "Hi"}],
                    user_id=1,
                )

            assert result["content"] == "Hello from together!"
            assert result["provider"] == "together"

    @pytest.mark.asyncio
    async def test_chat_all_providers_fail(self):
        """Test error when all providers fail."""
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "groq-key"},
            clear=False,
        ):
            client = GrappleLLMClient(environment="production")

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Server error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500),
                )
            )

            with patch("httpx.AsyncClient", return_value=mock_client):
                with pytest.raises(RuntimeError, match="All LLM providers"):
                    await client.chat(
                        messages=[{"role": "user", "content": "Hi"}],
                        user_id=1,
                    )
