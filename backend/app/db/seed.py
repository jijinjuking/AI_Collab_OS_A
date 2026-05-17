"""Seed system preset role templates into the database."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.role_template import RoleTemplate
from app.engine.prompts.templates import SYSTEM_ROLES
from loguru import logger


async def seed_system_roles(session: AsyncSession) -> None:
    """Insert system role templates if they don't exist.

    Called during application startup. Only inserts roles
    that are not already present (by key + is_system=True).
    """
    for role_data in SYSTEM_ROLES:
        stmt = select(RoleTemplate).where(
            RoleTemplate.key == role_data["key"],
            RoleTemplate.is_system == True,
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update system prompt if changed
            if existing.system_prompt != role_data["system_prompt"]:
                existing.system_prompt = role_data["system_prompt"]
                existing.skills = role_data.get("skills")
                existing.default_model = role_data.get("default_model")
                session.add(existing)
                logger.info(f"Updated system role: {role_data['key']}")
        else:
            template = RoleTemplate(
                key=role_data["key"],
                name=role_data["name"],
                icon=role_data.get("icon"),
                system_prompt=role_data["system_prompt"],
                skills=role_data.get("skills"),
                default_model=role_data.get("default_model"),
                is_system=True,
                user_id=None,
            )
            session.add(template)
            logger.info(f"Seeded system role: {role_data['key']}")

    await session.flush()
