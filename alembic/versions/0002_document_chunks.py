"""Add document_chunks table with pgvector embeddings.

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),  # stored as vector type below
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doc_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Convert embedding column to vector(384)
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)")
    op.create_index("ix_document_chunks_doc_id", "document_chunks", ["doc_id"])
    # IVFFlat index for approximate nearest-neighbour search
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding ON document_chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)"
    )


def downgrade() -> None:
    op.drop_table("document_chunks")
