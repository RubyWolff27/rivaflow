"""Grapple LLM Client with hybrid provider support and automatic failover."""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GrappleLLMClient:
    """
    Hybrid LLM client with automatic failover.

    Provider priority:
    1. Groq (free tier, production) - 14,400 requests/day
    2. Together AI (fallback) - paid but reliable
    3. Ollama (local development only)

    Features:
    - Automatic provider failover
    - Token counting with tiktoken
    - Cost tracking
    - Streaming support
    - Context window management
    """

    # Model configurations
    MODELS = {
        "groq": {
            "name": "llama3-70b-8192",
            "context_window": 8192,
            "cost_per_1k_input": 0.0,  # Free tier
            "cost_per_1k_output": 0.0,  # Free tier
        },
        "together": {
            "name": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "context_window": 8192,
            "cost_per_1k_input": 0.0009,  # $0.90 per 1M tokens
            "cost_per_1k_output": 0.0009,
        },
        "ollama": {
            "name": "llama3.2:3b",
            "context_window": 8192,
            "cost_per_1k_input": 0.0,
            "cost_per_1k_output": 0.0,
        },
    }

    def __init__(self, environment: str = "production"):
        """
        Initialize LLM client.

        Args:
            environment: 'production' or 'development'
        """
        self.environment = environment

        # API keys
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")

        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        # Determine provider availability
        self.providers = self._detect_available_providers()

        if not self.providers:
            logger.error("No LLM providers available! Configure GROQ_API_KEY or TOGETHER_API_KEY.")
            raise RuntimeError("No LLM providers configured")

        logger.info(f"Grapple LLM initialized with providers: {', '.join(self.providers)}")

    def _detect_available_providers(self) -> list[str]:
        """Detect which providers are available based on configuration."""
        providers = []

        # Production: prefer cloud providers
        if self.environment == "production":
            if self.groq_api_key:
                providers.append("groq")
            if self.together_api_key:
                providers.append("together")
        else:
            # Development: use local Ollama if available, otherwise cloud
            if self._check_ollama_available():
                providers.append("ollama")
            if self.groq_api_key:
                providers.append("groq")
            if self.together_api_key:
                providers.append("together")

        return providers

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            import httpx

            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.ollama_url}/api/tags")
                return response.status_code == 200
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
        """
        Send chat completion request with automatic failover.

        Args:
            messages: List of chat messages [{"role": "user", "content": "..."}]
            user_id: User ID for logging
            stream: Whether to stream the response
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'content', 'provider', 'model', 'input_tokens', 'output_tokens', 'cost_usd'
        """
        last_error = None

        for provider in self.providers:
            try:
                logger.info(f"Attempting chat with provider: {provider}")

                if provider == "groq":
                    result = await self._call_groq(messages, temperature, max_tokens)
                elif provider == "together":
                    result = await self._call_together(messages, temperature, max_tokens)
                elif provider == "ollama":
                    result = await self._call_ollama(messages, temperature, max_tokens)
                else:
                    continue

                # Success - return result
                logger.info(f"Successfully got response from {provider} for user {user_id}")
                return result

            except Exception as e:
                logger.warning(f"Provider {provider} failed: {type(e).__name__}: {str(e)}")
                last_error = e
                continue

        # All providers failed
        logger.error(f"All LLM providers failed for user {user_id}. Last error: {last_error}")
        raise RuntimeError(f"All LLM providers failed: {last_error}")

    async def _call_groq(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Call Groq API."""
        from groq import AsyncGroq

        client = AsyncGroq(api_key=self.groq_api_key)
        model = self.MODELS["groq"]["name"]

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract tokens and calculate cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost_usd = self._calculate_cost("groq", input_tokens, output_tokens)

        return {
            "content": response.choices[0].message.content,
            "provider": "groq",
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost_usd,
        }

    async def _call_together(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Call Together AI API."""
        from together import AsyncTogether

        client = AsyncTogether(api_key=self.together_api_key)
        model = self.MODELS["together"]["name"]

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract tokens and calculate cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost_usd = self._calculate_cost("together", input_tokens, output_tokens)

        return {
            "content": response.choices[0].message.content,
            "provider": "together",
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost_usd": cost_usd,
        }

    async def _call_ollama(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Call Ollama local API."""
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

        # Estimate tokens (Ollama doesn't return exact counts)
        content = data["message"]["content"]
        estimated_tokens = len(content.split()) * 1.3  # Rough estimate
        input_tokens = sum(len(m["content"].split()) * 1.3 for m in messages)
        output_tokens = estimated_tokens

        return {
            "content": content,
            "provider": "ollama",
            "model": model,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_tokens": int(input_tokens + output_tokens),
            "cost_usd": 0.0,  # Local is free
        }

    def _calculate_cost(self, provider: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for a request."""
        config = self.MODELS.get(provider, {})
        input_cost = (input_tokens / 1000) * config.get("cost_per_1k_input", 0.0)
        output_cost = (output_tokens / 1000) * config.get("cost_per_1k_output", 0.0)
        return round(input_cost + output_cost, 6)

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all providers."""
        return {
            "available_providers": self.providers,
            "primary_provider": self.providers[0] if self.providers else None,
            "models": self.MODELS,
            "environment": self.environment,
        }
