"""Context management: sliding window + summarization for long conversations.

Strategies:
1. Sliding window: keep last N messages in full
2. Summarize: compress older messages into a summary
3. Token budget: ensure total context stays within model limits
"""

from dataclasses import dataclass

from loguru import logger

from app.services.llm_service import LLMConfig, LLMMessage, LLMResponse, llm_service


@dataclass
class ContextConfig:
    """Configuration for context management."""

    max_context_tokens: int = 8000  # Token budget for conversation history
    window_size: int = 10  # Number of recent messages to keep in full
    summary_max_tokens: int = 500  # Max tokens for the summary
    enable_summarization: bool = True


SUMMARIZE_PROMPT = """请将以下对话历史压缩为一段简洁的摘要，保留关键信息、决策和结论。
摘要应包含：
1. 讨论的主要话题
2. 做出的关键决策
3. 未解决的问题
4. 重要的技术细节

对话历史:
{history}

请用中文输出摘要，控制在300字以内。"""


class ContextManager:
    """Manages conversation context with sliding window and summarization."""

    def __init__(self, config: ContextConfig | None = None):
        self.config = config or ContextConfig()

    async def build_context(
        self,
        system_prompt: str,
        messages: list[dict],
        llm_config: LLMConfig | None = None,
    ) -> list[LLMMessage]:
        """Build optimized context from message history.

        Args:
            system_prompt: The agent's system prompt
            messages: All messages ordered by time (oldest first)
                      Each dict has: role, content, token_count (optional)
            llm_config: LLM config for summarization calls

        Returns:
            Optimized list of LLMMessages ready for LLM call
        """
        result: list[LLMMessage] = [LLMMessage(role="system", content=system_prompt)]

        if not messages:
            return result

        total_messages = len(messages)
        window_size = self.config.window_size

        # If messages fit within window, return all
        if total_messages <= window_size:
            for msg in messages:
                result.append(LLMMessage(role=msg["role"], content=msg["content"]))
            return result

        # Split: older messages (to summarize) + recent window (keep full)
        older_messages = messages[:-window_size]
        recent_messages = messages[-window_size:]

        # Summarize older messages if enabled
        if self.config.enable_summarization and llm_config:
            summary = await self._summarize(older_messages, llm_config)
            if summary:
                result.append(LLMMessage(
                    role="system",
                    content=f"[对话历史摘要 ({len(older_messages)} 条消息)]\n{summary}",
                ))
        else:
            # Fallback: just take last few from older messages
            keep_count = min(3, len(older_messages))
            for msg in older_messages[-keep_count:]:
                result.append(LLMMessage(role=msg["role"], content=msg["content"]))

        # Add recent messages in full
        for msg in recent_messages:
            result.append(LLMMessage(role=msg["role"], content=msg["content"]))

        logger.debug(
            f"Context built: {total_messages} messages → "
            f"summary({len(older_messages)}) + window({len(recent_messages)})"
        )

        return result

    async def _summarize(
        self, messages: list[dict], llm_config: LLMConfig
    ) -> str | None:
        """Summarize a list of messages into a compact summary."""
        try:
            # Build history text
            history_parts = []
            for msg in messages:
                role_label = "用户" if msg["role"] == "user" else "助手"
                content = msg["content"][:500]  # Truncate long messages
                history_parts.append(f"[{role_label}]: {content}")

            history_text = "\n".join(history_parts)

            # Limit input to avoid excessive token usage
            if len(history_text) > 6000:
                history_text = history_text[:6000] + "\n...(已截断)"

            prompt = SUMMARIZE_PROMPT.format(history=history_text)

            summary_messages = [
                LLMMessage(role="system", content="你是一个对话摘要助手。"),
                LLMMessage(role="user", content=prompt),
            ]

            # Use a smaller/cheaper model for summarization
            summary_config = LLMConfig(
                model=llm_config.model,
                provider=llm_config.provider,
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
                temperature=0.3,
                max_tokens=self.config.summary_max_tokens,
            )

            response = await llm_service.complete(summary_messages, summary_config)
            logger.info(
                f"Summarized {len(messages)} messages → {len(response.content)} chars"
            )
            return response.content

        except Exception as e:
            logger.warning(f"Summarization failed: {e}, falling back to truncation")
            return None

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token for Chinese/English mix)."""
        return len(text) // 3
