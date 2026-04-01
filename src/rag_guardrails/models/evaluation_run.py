"""Evaluation run — tracks async Ragas evaluation jobs."""
from datetime import datetime, UTC
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from rag_guardrails.core.database import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    # "pending" | "running" | "complete" | "error"
    config_json: Mapped[str] = mapped_column(Text, nullable=True)   # serialised EvalRequest
    scores_json: Mapped[str] = mapped_column(Text, nullable=True)   # serialised results dict
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
