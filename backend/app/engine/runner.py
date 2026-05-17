"""Workflow runner: orchestrates graph execution with lifecycle management."""

from typing import Any

from loguru import logger

from app.core.events import event_bus
from app.engine.graph_builder import GraphBuilder
from app.engine.state import WorkflowState


class WorkflowRunner:
    """Executes a compiled LangGraph workflow with event broadcasting."""

    def __init__(self, project_id: str, workflow_id: str):
        self.project_id = project_id
        self.workflow_id = workflow_id

    async def run(
        self,
        dag_config: dict[str, Any],
        task_description: str,
        max_review_rounds: int = 3,
    ) -> WorkflowState:
        """Build graph from DAG config and execute it.

        Returns the final workflow state.
        """
        # Build initial state
        initial_state: WorkflowState = {
            "project_id": self.project_id,
            "workflow_id": self.workflow_id,
            "task_description": task_description,
            "current_step_id": "",
            "current_step_type": "",
            "outputs": [],
            "files_produced": [],
            "review_round": 0,
            "max_review_rounds": max_review_rounds,
            "review_verdict": "",
            "review_feedback": "",
            "status": "running",
            "error": None,
            "metadata": {},
        }

        # Notify workflow started
        await event_bus.publish_workflow_event(
            self.project_id, self.workflow_id, "started"
        )

        try:
            # Build and compile graph
            builder = GraphBuilder(dag_config)
            compiled_graph = builder.build()

            # Execute the graph
            logger.info(
                f"Workflow {self.workflow_id} starting: "
                f"{len(dag_config.get('nodes', []))} nodes"
            )

            final_state = await compiled_graph.ainvoke(initial_state)

            # Mark completed
            final_state["status"] = "completed"

            await event_bus.publish_workflow_event(
                self.project_id,
                self.workflow_id,
                "completed",
                outputs_count=len(final_state.get("outputs", [])),
            )

            logger.info(
                f"Workflow {self.workflow_id} completed: "
                f"{len(final_state.get('outputs', []))} outputs"
            )

            return final_state

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Workflow {self.workflow_id} failed: {error_msg}")

            await event_bus.publish_workflow_event(
                self.project_id,
                self.workflow_id,
                "failed",
                error=error_msg,
            )

            initial_state["status"] = "failed"
            initial_state["error"] = error_msg
            return initial_state
