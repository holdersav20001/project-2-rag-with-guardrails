"""Audit log — every guardrail decision is persisted here."""
from datetime import datetime, UTC
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from rag_guardrails.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    guardrail_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False)  # "blocked" | "allowed"
    reason: Mapped[str] = mapped_column(String(256), nullable=True)
    query_hash: Mapped[str] = mapped_column(String(16), nullable=True)  # first 8 chars of sha256
    session_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string for extra context
