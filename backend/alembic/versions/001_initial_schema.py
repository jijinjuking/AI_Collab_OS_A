"""Initial schema — all M1-M5 tables.

Revision ID: 001_initial
Revises: None
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(100), unique=True, nullable=True, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("settings", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- projects ---
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("plan", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft", index=True),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("workspace_path", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- role_templates ---
    op.create_table(
        "role_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("key", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("system_prompt", sa.Text, nullable=False),
        sa.Column("skills", sa.JSON, nullable=True),
        sa.Column("default_model", sa.String(100), nullable=True),
        sa.Column("is_system", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "key", name="uq_role_user_key"),
    )

    # --- project_agents ---
    op.create_table(
        "project_agents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "role_template_id",
            sa.String(36),
            sa.ForeignKey("role_templates.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("instance_name", sa.String(100), nullable=False),
        sa.Column("instance_index", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="idle", index=True),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("api_key_id", sa.String(36), nullable=True),
        sa.Column("system_prompt_override", sa.Text, nullable=True),
        sa.Column("config", sa.JSON, nullable=True),
        sa.Column("token_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "project_id", "role_template_id", "instance_index",
            name="uq_agent_project_role_index",
        ),
    )

    # --- workflows ---
    op.create_table(
        "workflows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(100), nullable=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("dag_config", sa.JSON, nullable=False),
        sa.Column("current_step_id", sa.String(36), nullable=True),
        sa.Column("mode", sa.String(10), nullable=False, server_default="manual"),
        sa.Column("max_review_rounds", sa.Integer, nullable=False, server_default="3"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- workflow_steps ---
    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "workflow_id",
            sa.String(36),
            sa.ForeignKey("workflows.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "agent_id",
            sa.String(36),
            sa.ForeignKey("project_agents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("step_type", sa.String(30), nullable=False),
        sa.Column("step_order", sa.Integer, nullable=False),
        sa.Column("depends_on", sa.JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("input_data", sa.JSON, nullable=True),
        sa.Column("output_data", sa.JSON, nullable=True),
        sa.Column("review_round", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    # --- agent_messages ---
    op.create_table(
        "agent_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("workflow_id", sa.String(36), nullable=True),
        sa.Column(
            "from_agent_id",
            sa.String(36),
            sa.ForeignKey("project_agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "to_agent_id",
            sa.String(36),
            sa.ForeignKey("project_agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("message_type", sa.String(20), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("summary", sa.String(500), nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # Composite indexes for agent_messages
    op.create_index("ix_msg_project_created", "agent_messages", ["project_id", "created_at"])
    op.create_index("ix_msg_workflow", "agent_messages", ["workflow_id"])
    op.create_index("ix_msg_from_agent", "agent_messages", ["from_agent_id"])
    op.create_index("ix_msg_to_agent", "agent_messages", ["to_agent_id"])


def downgrade() -> None:
    op.drop_index("ix_msg_to_agent", table_name="agent_messages")
    op.drop_index("ix_msg_from_agent", table_name="agent_messages")
    op.drop_index("ix_msg_workflow", table_name="agent_messages")
    op.drop_index("ix_msg_project_created", table_name="agent_messages")
    op.drop_table("agent_messages")
    op.drop_table("workflow_steps")
    op.drop_table("workflows")
    op.drop_table("project_agents")
    op.drop_table("role_templates")
    op.drop_table("projects")
    op.drop_table("users")
