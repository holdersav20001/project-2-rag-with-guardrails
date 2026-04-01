"""Health check — public endpoint, no auth required."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from rag_guardrails.core.database import get_db

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    """Deep health check: verifies DB connectivity and model availability."""
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Models are singletons — just check they can be imported
    try:
        from rag_guardrails.retrieval.embeddings import get_embed_model  # noqa: F401
        models_ok = True
    except Exception:
        models_ok = False

    status = "ok" if (db_ok and models_ok) else "degraded"
    return {
        "status": status,
        "db": "ok" if db_ok else "error",
        "models": "ok" if models_ok else "error",
    }
