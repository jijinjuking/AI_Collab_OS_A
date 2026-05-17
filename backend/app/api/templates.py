"""Workflow template routes."""

from fastapi import APIRouter

from app.engine.templates import get_template, list_templates

router = APIRouter()


@router.get("/")
async def get_all_templates():
    """List all available workflow templates."""
    return {"templates": list_templates()}


@router.get("/{template_key}")
async def get_template_detail(template_key: str):
    """Get a specific workflow template by key."""
    template = get_template(template_key)
    if not template:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Template", detail=f"模板不存在: {template_key}")
    return template
