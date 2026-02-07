"""Grapple LLM Client with httpx-based provider support."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GrappleLLMClient:
    """
    LLM client using httpx for all providers.

    Provider priority:
    1. Groq (free tier, production)
    2. Together AI (fallback)
    3. Ollama (local development only)
    """

    MODELS = {
        "groq": {
            "name": "llama-3.3-70b-versatile",
            "context_window": 8192,
            "cost_per_1k_input": 0.0,
            "cost_per_1k_output": 0.0,
        },
        "together": {
            "name": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "context_window": 8192,
            "cost_per_1k_input": 0.0009,
            "cost_per_1k_output": 0.0009,
        },
        "ollama": {
            "name": "llama3.2:3b",
            "context_window": 8192,
            "cost_per_1k_input": 0.0,
            "cost_per_1k_output": 0.0,
        },
    }

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.providers = self._detect_available_providers()

        if not self.providers:
            logger.warning(
                "No LLM providers available. "
                "Configure GROQ_API_KEY or TOGETHER_API_KEY."
            )

        if self.providers:
            logger.info(
                "Grapple LLM initialized with providers: "
                f"{', '.join(self.providers)}"
            )

    def _detect_available_providers(self) -> list[str]:
        providers = []
        if self.environment == "production":
            if self.groq_api_key:
                providers.append("groq")
            if self.together_api_key:
                providers.append("together")
        else:
            if self._check_ollama_available():
                providers.append("ollama")
            if self.groq_api_key:
                providers.append("groq")
            if self.together_api_key:
                providers.append("together")
        return providers

    def _check_ollama_available(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.ollama_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def chat(
        self,
        messages: list[dict[str, str]],
        user_id: int,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> dict[str, Any]:
        if not self.providers:
            raise RuntimeError("No LLM providers configured")

        last_error = None
        for provider in self.providers:
            try:
                logger.info(f"Attempting chat with provider: {provider}")
                if provider == "groq":
                    result = await self._call_groq(messages, temperature, max_tokens)
                elif provider == "together":
                    result = await self._call_together(
                        messages, temperature, max_tokens
                    )
                elif provider == "ollama":
                    result = await self._call_ollama(messages, temperature, max_tokens)
                else:
                    continue

                logger.info(
                    "Successfully got response from " f"{provider} for user {user_id}"
                )
                return result
            except Exception as e:
                logger.warning(
                    f"Provider {provider} failed: " f"{type(e).__name__}: {str(e)}"
                )
                last_error = e
                continue

        logger.error(
            f"All LLM providers failed for user {user_id}. " f"Last error: {last_error}"
        )
        raise RuntimeError(f"All LLM providers failed: {last_error}")

    async def _call_groq(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        model = self.MODELS["groq"]["name"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.GROQ_API_URL,
                headers={
                    "Authorization": (f"Bearer {self.groq_api_key}"),
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost = self._calculate_cost("groq", input_tokens, output_tokens)

        return {
            "content": content,
            "provider": "groq",
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost,
        }

    async def _call_together(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        model = self.MODELS["together"]["name"]
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.TOGETHER_API_URL,
                headers={
                    "Authorization": (f"Bearer {self.together_api_key}"),
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        cost = self._calculate_cost("together", input_tokens, output_tokens)

        return {
            "content": content,
            "provider": "together",
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost,
        }

    async def _call_ollama(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        model = self.MODELS["ollama"]["name"]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()

        content = data["message"]["content"]
        est_tokens = len(content.split()) * 1.3
        input_tokens = sum(len(m["content"].split()) * 1.3 for m in messages)
        output_tokens = est_tokens

        return {
            "content": content,
            "provider": "ollama",
            "model": model,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_tokens": int(input_tokens + output_tokens),
            "cost_usd": 0.0,
        }

    def _calculate_cost(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        config = self.MODELS.get(provider, {})
        input_cost = (input_tokens / 1000) * config.get("cost_per_1k_input", 0.0)
        output_cost = (output_tokens / 1000) * config.get("cost_per_1k_output", 0.0)
        return round(input_cost + output_cost, 6)

    def get_provider_status(self) -> dict[str, Any]:
        return {
            "available_providers": self.providers,
            "primary_provider": (self.providers[0] if self.providers else None),
            "models": self.MODELS,
            "environment": self.environment,
        }
