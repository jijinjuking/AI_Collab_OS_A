"""Workflow shared state definition for LangGraph.

This defines the TypedDict that flows through the state graph.
Each node reads from and writes to this shared state.
"""

from typing import Any, TypedDict


class AgentOutput(TypedDict):
    """Output from a single agent node execution."""

    agent_id: str
    agent_name: str
    content: str
    token_count: int
    model_used: str


class WorkflowState(TypedDict):
    """Shared state that flows through the LangGraph state graph.

    All nodes read/write to this state. LangGraph handles
    state persistence and checkpointing.
    """

    # --- Identifiers ---
    project_id: str
    workflow_id: str

    # --- Task Context ---
    task_description: str  # The original task/plan from user
    current_step_id: str  # Currently executing step
    current_step_type: str  # execute/review/discuss/assign

    # --- Accumulated Outputs ---
    outputs: list[AgentOutput]  # All agent outputs in order
    files_produced: list[dict[str, str]]  # [{path, content, agent_id}]

    # --- Review State ---
    review_round: int  # Current review iteration
    max_review_rounds: int
    review_verdict: str  # pass/revise/reject
    review_feedback: str  # Reviewer's feedback

    # --- Control ---
    status: str  # running/paused/completed/failed
    error: str | None  # Error message if failed
    metadata: dict[str, Any]  # Extensible metadata
