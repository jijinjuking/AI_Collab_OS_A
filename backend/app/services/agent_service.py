"""Agent service: manages agent instances and handles chat interactions."""

from collections.abc import AsyncGenerator

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.agent_message import AgentMessage
from app.db.models.project_agent import ProjectAgent
from app.db.models.role_template import RoleTemplate
from app.schemas.agent import AgentChatRequest
from app.services.llm_service import LLMConfig, LLMMessage, LLMResponse, llm_service


class AgentService:
    """Handles agent chat and lifecycle."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_agent(self, agent_id: str) -> ProjectAgent:
        """Fetch an agent instance by ID."""
        stmt = select(ProjectAgent).where(ProjectAgent.id == agent_id)
        result = await self.session.execute(stmt)
        agent = result.scalar_one_or_none()
        if not agent:
            raise NotFoundError("Agent")
        return agent

    async def get_role_template(self, template_id: str) -> RoleTemplate:
        """Fetch a role template by ID."""
        stmt = select(RoleTemplate).where(RoleTemplate.id == template_id)
        result = await self.session.execute(stmt)
        template = result.scalar_one_or_none()
        if not template:
            raise NotFoundError("RoleTemplate")
        return template

    async def build_messages(
        self, agent: ProjectAgent, user_message: str
    ) -> list[LLMMessage]:
        """Build the message list for an LLM call: system prompt + history + new message.

        Uses ContextManager for sliding window + summarization when history is long.
        """
        from app.services.context_manager import ContextConfig, ContextManager

        # Get role template for system prompt
        template = await self.get_role_template(agent.role_template_id)
        system_prompt = agent.system_prompt_override or template.system_prompt

        # Fetch conversation history (last 40 messages for context manager to process)
        stmt = (
            select(AgentMessage)
            .where(
                (AgentMessage.from_agent_id == agent.id)
                | (AgentMessage.to_agent_id == agent.id)
            )
            .order_by(AgentMessage.created_at.desc())
            .limit(40)
        )
        result = await self.session.execute(stmt)
        history_rows = list(reversed(result.scalars().all()))

        # Convert to dict format for context manager
        history = [
            {"role": msg.role, "content": msg.content, "token_count": msg.token_count}
            for msg in history_rows
        ]

        # Use context manager for intelligent context building
        ctx_manager = ContextManager(ContextConfig(
            window_size=10,
            enable_summarization=len(history) > 15,
        ))

        # Build LLM config for potential summarization
        config = agent.config or {}
        llm_config = LLMConfig(
            model=agent.model or "",
            provider=agent.provider or "",
            api_key="",
            base_url=agent.base_url or "",
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 4096),
        )

        messages = await ctx_manager.build_context(
            system_prompt=system_prompt,
            messages=history,
            llm_config=llm_config if len(history) > 15 else None,
        )

        # Append the new user message
        messages.append(LLMMessage(role="user", content=user_message))
        return messages

    def build_config(self, agent: ProjectAgent, request: AgentChatRequest) -> LLMConfig:
        """Build LLM config from agent settings + request overrides."""
        config = agent.config or {}
        return LLMConfig(
            model=request.model or agent.model or "",
            provider=request.provider or agent.provider or "",
            api_key="",  # Will be resolved from api_key_id in M2
            base_url=agent.base_url or "",
            temperature=request.temperature or config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 4096),
        )

    async def chat(
        self, agent: ProjectAgent, request: AgentChatRequest
    ) -> LLMResponse:
        """Non-streaming chat: send message, get full response."""
        messages = await self.build_messages(agent, request.message)
        config = self.build_config(agent, request)

        # Save user message
        user_msg = await self._save_message(
            agent=agent,
            role="user",
            content=request.message,
            message_type="chat",
        )

        # Call LLM
        response = await llm_service.complete(messages, config)

        # Save assistant response
        assistant_msg = await self._save_message(
            agent=agent,
            role="assistant",
            content=response.content,
            message_type="chat",
            token_count=response.total_tokens,
            model_used=response.model,
        )

        # Update agent token usage
        agent.token_used += response.total_tokens
        self.session.add(agent)

        return response

    async def chat_stream(
        self, agent: ProjectAgent, request: AgentChatRequest
    ) -> AsyncGenerator[str, None]:
        """Streaming chat: yields content chunks, persists after completion."""
        messages = await self.build_messages(agent, request.message)
        config = self.build_config(agent, request)

        # Save user message
        await self._save_message(
            agent=agent,
            role="user",
            content=request.message,
            message_type="chat",
        )

        # Stream LLM response
        full_content = ""
        total_tokens = 0

        async for item in llm_service.stream_with_usage(messages, config):
            if isinstance(item, str):
                full_content += item
                yield item
            elif isinstance(item, LLMResponse):
                total_tokens = item.total_tokens

        # Save assistant response after stream completes
        await self._save_message(
            agent=agent,
            role="assistant",
            content=full_content,
            message_type="chat",
            token_count=total_tokens,
            model_used=config.litellm_model,
        )

        # Update agent token usage
        agent.token_used += total_tokens
        self.session.add(agent)
        await self.session.commit()

    async def _save_message(
        self,
        agent: ProjectAgent,
        role: str,
        content: str,
        message_type: str,
        token_count: int | None = None,
        model_used: str | None = None,
    ) -> AgentMessage:
        """Persist a message to the database."""
        msg = AgentMessage(
            project_id=agent.project_id,
            from_agent_id=agent.id if role == "assistant" else None,
            to_agent_id=agent.id if role == "user" else None,
            message_type=message_type,
            role=role,
            content=content,
            token_count=token_count,
            model_used=model_used,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg
