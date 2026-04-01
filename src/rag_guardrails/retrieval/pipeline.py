"""Retrieval pipeline — vector search, re-ranking, session history."""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_guardrails.core.logging import get_logger

logger = get_logger(__name__)


async def retrieve_and_rerank(query: str, top_k: int = 5) -> list[dict]:
    """Vector search with timeout + cross-encoder re-ranking."""
    try:
        raw_results = await asyncio.wait_for(
            _async_search(query, top_k * 2),
            timeout=5.0,
        )
    except asyncio.TimeoutError:
        from fastapi import HTTPException
        raise HTTPException(503, "Vector search timed out after 5s")

    if not raw_results:
        return []

    # Re-rank
    reranked = await asyncio.to_thread(_rerank, query, raw_results, top_k)
    return reranked


async def _async_search(query: str, top_k: int) -> list[dict]:
    """Async pgvector cosine similarity search."""
    from rag_guardrails.retrieval.embeddings import get_embed_model
    from rag_guardrails.models.document_chunk import DocumentChunk
    from rag_guardrails.core.database import AsyncSessionLocal

    model = get_embed_model()
    q_emb = await asyncio.to_thread(model.get_text_embedding, query)

    async with AsyncSessionLocal() as db:
        distance = DocumentChunk.embedding.cosine_distance(q_emb)
        result = await db.execute(
            select(
                DocumentChunk.text,
                DocumentChunk.doc_id,
                DocumentChunk.chunk_index,
                (1 - distance).label("score"),
            )
            .order_by(distance)
            .limit(top_k)
        )
        rows = result.all()

    return [
        {"text": r.text, "doc_id": r.doc_id, "chunk": r.chunk_index, "score": float(r.score)}
        for r in rows
    ]


def _rerank(query: str, chunks: list[dict], top_k: int) -> list[dict]:
    """Re-rank chunks using cross-encoder and return top_k."""
    from rag_guardrails.retrieval.reranker import get_reranker
    reranker = get_reranker()
    pairs = [(query, c["text"]) for c in chunks]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    result = []
    for score, chunk in ranked[:top_k]:
        chunk = dict(chunk)
        chunk["score"] = float(score)
        result.append(chunk)
    return result


async def load_session_history(session_id: str, db: AsyncSession, limit: int = 10) -> list[dict]:
    """Load last N turns for a session."""
    from rag_guardrails.models.session_history import SessionHistory
    result = await db.execute(
        select(SessionHistory)
        .where(SessionHistory.session_id == session_id)
        .order_by(SessionHistory.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


async def save_session_turn(
    session_id: str,
    user_query: str,
    assistant_answer: str,
    db: AsyncSession,
) -> None:
    """Persist a user/assistant turn pair."""
    from rag_guardrails.models.session_history import SessionHistory
    db.add(SessionHistory(session_id=session_id, role="user", content=user_query))
    db.add(SessionHistory(session_id=session_id, role="assistant", content=assistant_answer))
