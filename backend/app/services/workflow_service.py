"""Workflow service: CRUD + execution lifecycle."""

import asyncio
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.base import utcnow
from app.db.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowService:
    """Manages workflow lifecycle and execution."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, project_id: str, data: WorkflowCreate) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            project_id=project_id,
            name=data.name,
            type=data.type,
            dag_config=data.dag_config,
            mode=data.mode,
            max_review_rounds=data.max_review_rounds,
        )
        self.session.add(workflow)
        await self.session.flush()
        return workflow

    async def list_by_project(self, project_id: str) -> list[Workflow]:
        """List all workflows for a project."""
        stmt = (
            select(Workflow)
            .where(Workflow.project_id == project_id)
            .order_by(Workflow.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, workflow_id: str) -> Workflow:
        """Get a workflow by ID."""
        stmt = select(Workflow).where(Workflow.id == workflow_id)
        result = await self.session.execute(stmt)
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise NotFoundError("Workflow")
        return workflow

    async def update(self, workflow_id: str, data: WorkflowUpdate) -> Workflow:
        """Update workflow fields (name, dag_config, mode)."""
        workflow = await self.get(workflow_id)
        if data.name is not None:
            workflow.name = data.name
        if data.dag_config is not None:
            workflow.dag_config = data.dag_config
        if data.mode is not None:
            workflow.mode = data.mode
        workflow.updated_at = utcnow()
        self.session.add(workflow)
        await self.session.flush()
        return workflow

    async def start(self, workflow_id: str, task_description: str) -> Workflow:
        """Start workflow execution (launches async runner)."""
        workflow = await self.get(workflow_id)

        if workflow.status not in ("pending", "paused", "failed"):
            raise ConflictError(detail=f"工作流状态为 {workflow.status}，无法启动")

        workflow.status = "running"
        workflow.started_at = utcnow()
        self.session.add(workflow)
        await self.session.flush()

        # Launch execution in background (non-blocking)
        asyncio.create_task(
            self._execute_workflow(
                workflow.project_id,
                workflow.id,
                workflow.dag_config,
                task_description,
                workflow.max_review_rounds,
            )
        )

        return workflow

    async def pause(self, workflow_id: str) -> Workflow:
        """Pause a running workflow."""
        workflow = await self.get(workflow_id)
        if workflow.status != "running":
            raise ConflictError(detail="只能暂停运行中的工作流")
        workflow.status = "paused"
        self.session.add(workflow)
        return workflow

    async def _execute_workflow(
        self,
        project_id: str,
        workflow_id: str,
        dag_config: dict,
        task_description: str,
        max_review_rounds: int,
    ) -> None:
        """Background task: run the workflow via LangGraph engine."""
        from app.db.session import async_session_factory
        from app.engine.runner import WorkflowRunner

        runner = WorkflowRunner(project_id, workflow_id)

        try:
            final_state = await runner.run(
                dag_config=dag_config,
                task_description=task_description,
                max_review_rounds=max_review_rounds,
            )

            # Update workflow status in DB
            async with async_session_factory() as session:
                stmt = select(Workflow).where(Workflow.id == workflow_id)
                result = await session.execute(stmt)
                workflow = result.scalar_one_or_none()
                if workflow:
                    workflow.status = final_state.get("status", "completed")
                    workflow.completed_at = utcnow()
                    session.add(workflow)
                    await session.commit()

        except Exception as e:
            logger.error(f"Workflow {workflow_id} execution error: {e}")
            async with async_session_factory() as session:
                stmt = select(Workflow).where(Workflow.id == workflow_id)
                result = await session.execute(stmt)
                workflow = result.scalar_one_or_none()
                if workflow:
                    workflow.status = "failed"
                    session.add(workflow)
                    await session.commit()
