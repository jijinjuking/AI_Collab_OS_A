"""Graph builder: converts a DAG config into a LangGraph StateGraph.

The DAG config (stored in workflows.dag_config) defines nodes and edges.
This module dynamically builds a LangGraph state graph from that config.
"""

from typing import Any

from loguru import logger

from app.engine.state import WorkflowState


class GraphBuilder:
    """Builds a LangGraph StateGraph from a DAG configuration.

    DAG config format (from DATABASE_DESIGN.md):
    {
        "nodes": [
            {"id": "node_1", "agent_id": "uuid", "step_type": "execute", "label": "..."},
            {"id": "node_2", "agent_id": "uuid", "step_type": "review", "label": "..."},
        ],
        "edges": [
            {"from": "node_1", "to": "node_2"},
        ]
    }
    """

    def __init__(self, dag_config: dict[str, Any]):
        self.dag_config = dag_config
        self.nodes: list[dict] = dag_config.get("nodes", [])
        self.edges: list[dict] = dag_config.get("edges", [])

    def build(self):
        """Build and compile the LangGraph StateGraph.

        Returns a compiled graph ready for invocation.
        """
        from langgraph.graph import END, StateGraph

        graph = StateGraph(WorkflowState)

        # Register nodes
        for node_cfg in self.nodes:
            node_id = node_cfg["id"]
            step_type = node_cfg["step_type"]
            agent_id = node_cfg.get("agent_id", "")

            # Create node function based on step_type
            node_fn = self._create_node_function(node_id, step_type, agent_id, node_cfg)
            graph.add_node(node_id, node_fn)

        # Determine entry point (nodes with no incoming edges)
        targets = {e["to"] for e in self.edges}
        sources = {e["from"] for e in self.edges}
        entry_nodes = [n["id"] for n in self.nodes if n["id"] not in targets]

        if not entry_nodes:
            entry_nodes = [self.nodes[0]["id"]] if self.nodes else []

        # Set entry point
        if len(entry_nodes) == 1:
            graph.set_entry_point(entry_nodes[0])
        else:
            # Multiple entry points: add a virtual start node
            async def start_node(state: WorkflowState) -> WorkflowState:
                return state

            graph.add_node("__start__", start_node)
            graph.set_entry_point("__start__")
            for entry in entry_nodes:
                graph.add_edge("__start__", entry)

        # Add edges
        for edge in self.edges:
            from_node = edge["from"]
            to_node = edge["to"]
            graph.add_edge(from_node, to_node)

        # Determine terminal nodes (nodes with no outgoing edges)
        terminal_nodes = [n["id"] for n in self.nodes if n["id"] not in sources]
        for terminal in terminal_nodes:
            graph.add_edge(terminal, END)

        # Handle review loops (conditional edges)
        self._add_review_conditionals(graph)

        logger.info(
            f"Graph built: {len(self.nodes)} nodes, {len(self.edges)} edges, "
            f"entry={entry_nodes}, terminal={terminal_nodes}"
        )

        return graph.compile()

    def _create_node_function(
        self, node_id: str, step_type: str, agent_id: str, config: dict
    ):
        """Create an async node function for the given step type."""

        async def execute_node(state: WorkflowState) -> dict:
            """Execute node: agent performs a task."""
            from app.engine.nodes.execute import run_execute_node
            return await run_execute_node(state, node_id, agent_id, config)

        async def review_node(state: WorkflowState) -> dict:
            """Review node: agent reviews previous outputs."""
            from app.engine.nodes.review import run_review_node
            return await run_review_node(state, node_id, agent_id, config)

        async def discuss_node(state: WorkflowState) -> dict:
            """Discuss node: two agents exchange ideas."""
            from app.engine.nodes.discuss import run_discuss_node
            return await run_discuss_node(state, node_id, agent_id, config)

        async def assign_node(state: WorkflowState) -> dict:
            """Assign node: architect distributes tasks."""
            from app.engine.nodes.assign import run_assign_node
            return await run_assign_node(state, node_id, agent_id, config)

        node_map = {
            "execute": execute_node,
            "review": review_node,
            "discuss": discuss_node,
            "assign": assign_node,
        }

        return node_map.get(step_type, execute_node)

    def _add_review_conditionals(self, graph) -> None:
        """Add conditional edges for review nodes (pass → next, revise → loop back)."""
        from langgraph.graph import END

        for node_cfg in self.nodes:
            if node_cfg["step_type"] != "review":
                continue

            node_id = node_cfg["id"]
            review_targets = node_cfg.get("review_targets", [])

            # Find the edge going out of this review node
            outgoing = [e for e in self.edges if e["from"] == node_id]

            if review_targets and outgoing:
                # Remove the static edge (we'll replace with conditional)
                for e in outgoing:
                    self.edges.remove(e)

                # Add conditional: pass → next node, revise → first review target
                next_node = outgoing[0]["to"] if outgoing else END
                loop_target = review_targets[0]

                def make_router(next_n, loop_t):
                    def route_review(state: WorkflowState) -> str:
                        if state.get("review_verdict") == "pass":
                            return next_n
                        if state.get("review_round", 0) >= state.get("max_review_rounds", 3):
                            return next_n  # Force pass after max rounds
                        return loop_t
                    return route_review

                graph.add_conditional_edges(
                    node_id,
                    make_router(next_node, loop_target),
                    {next_node: next_node, loop_target: loop_target},
                )
