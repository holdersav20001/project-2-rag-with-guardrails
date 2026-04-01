"""Initial schema — pgvector extension and all tables.

Revision ID: 0001
Revises:
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pgvector extension (must exist before any vector column)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("chunk_count", sa.Integer(), default=0),
        sa.Column("injection_risk", sa.Boolean(), default=False, nullable=False),
        sa.Column("status", sa.String(32), default="processing", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"], unique=True)

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("guardrail_name", sa.String(64), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(256), nullable=True),
        sa.Column("query_hash", sa.String(16), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_log_guardrail_name", "audit_log", ["guardrail_name"])
    op.create_index("ix_audit_log_session_id", "audit_log", ["session_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), default="pending", nullable=False),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("scores_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluation_runs_run_id", "evaluation_runs", ["run_id"], unique=True)

    op.create_table(
        "session_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_history_session_id", "session_history", ["session_id"])


def downgrade() -> None:
    op.drop_table("session_history")
    op.drop_table("evaluation_runs")
    op.drop_table("audit_log")
    op.drop_table("documents")
