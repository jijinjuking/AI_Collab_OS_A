"""LLM service: unified interface for calling language models via LiteLLM.

Supports streaming (SSE) and non-streaming completions.
Each agent can have its own provider/model/api_key configuration.
"""

from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from app.config import settings


@dataclass
class LLMConfig:
    """Configuration for a single LLM call."""

    model: str = ""
    provider: str = ""
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.model:
            self.model = settings.default_llm_model
        if not self.provider:
            self.provider = settings.default_llm_provider

    @property
    def litellm_model(self) -> str:
        """Format model string for LiteLLM (provider/model or just model)."""
        # LiteLLM uses format like "openai/gpt-4o", "anthropic/claude-3-5-sonnet"
        # For ollama, use "ollama/model-name"
        if "/" in self.model:
            return self.model
        if self.provider and self.provider != "openai":
            return f"{self.provider}/{self.model}"
        return self.model


@dataclass
class LLMMessage:
    """A single message in the conversation."""

    role: str  # system / user / assistant
    content: str


@dataclass
class LLMResponse:
    """Response from a non-streaming LLM call."""

    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMService:
    """Unified LLM calling service backed by LiteLLM."""

    async def complete(
        self, messages: list[LLMMessage], config: LLMConfig | None = None
    ) -> LLMResponse:
        """Non-streaming completion. Returns full response at once."""
        import litellm

        cfg = config or LLMConfig()
        params = self._build_params(messages, cfg)

        logger.debug(f"LLM call: model={cfg.litellm_model}, messages={len(messages)}")

        response = await litellm.acompletion(**params)

        content = response.choices[0].message.content or ""
        usage = response.usage

        return LLMResponse(
            content=content,
            model=response.model or cfg.litellm_model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )

    async def stream(
        self, messages: list[LLMMessage], config: LLMConfig | None = None
    ) -> AsyncGenerator[str, None]:
        """Streaming completion. Yields content chunks as they arrive."""
        import litellm

        cfg = config or LLMConfig()
        params = self._build_params(messages, cfg, stream=True)

        logger.debug(f"LLM stream: model={cfg.litellm_model}, messages={len(messages)}")

        response = await litellm.acompletion(**params)

        async for chunk in response:
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content

    async def stream_with_usage(
        self, messages: list[LLMMessage], config: LLMConfig | None = None
    ) -> AsyncGenerator[str | LLMResponse, None]:
        """Streaming that yields chunks, then a final LLMResponse with usage stats.

        Usage pattern:
            full_content = ""
            async for item in service.stream_with_usage(messages, config):
                if isinstance(item, str):
                    full_content += item
                    # send SSE chunk to client
                else:
                    # item is LLMResponse with token counts
                    usage = item
        """
        import litellm

        cfg = config or LLMConfig()
        params = self._build_params(messages, cfg, stream=True)
        params["stream_options"] = {"include_usage": True}

        response = await litellm.acompletion(**params)

        full_content = ""
        prompt_tokens = 0
        completion_tokens = 0

        async for chunk in response:
            # Check for usage in the final chunk
            if hasattr(chunk, "usage") and chunk.usage:
                prompt_tokens = chunk.usage.prompt_tokens or 0
                completion_tokens = chunk.usage.completion_tokens or 0

            delta = chunk.choices[0].delta
            if delta and delta.content:
                full_content += delta.content
                yield delta.content

        # Yield final response with usage
        yield LLMResponse(
            content=full_content,
            model=cfg.litellm_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

    def _build_params(
        self, messages: list[LLMMessage], cfg: LLMConfig, stream: bool = False
    ) -> dict[str, Any]:
        """Build LiteLLM completion parameters."""
        params: dict[str, Any] = {
            "model": cfg.litellm_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "top_p": cfg.top_p,
            "stream": stream,
        }

        # API key: per-agent override > env default
        if cfg.api_key:
            params["api_key"] = cfg.api_key
        elif cfg.provider == "openai" and settings.openai_api_key:
            params["api_key"] = settings.openai_api_key
        elif cfg.provider == "anthropic" and settings.anthropic_api_key:
            params["api_key"] = settings.anthropic_api_key

        # Base URL override (for Ollama or custom endpoints)
        if cfg.base_url:
            params["api_base"] = cfg.base_url
        elif cfg.provider == "ollama":
            params["api_base"] = settings.ollama_base_url

        # Extra params (stop sequences, etc.)
        params.update(cfg.extra)

        return params


# Singleton
llm_service = LLMService()
