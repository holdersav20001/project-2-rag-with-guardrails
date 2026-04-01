"""Document ingestion pipeline — parse, chunk, scan for injection, embed, store."""
from __future__ import annotations

import asyncio
import io
import re
import unicodedata

import numpy as np
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from rag_guardrails.core.config import get_settings
from rag_guardrails.core.logging import get_logger
from rag_guardrails.models.document import Document

logger = get_logger(__name__)

# Injection patterns reused from input guards (DRY via import)
from rag_guardrails.guardrails.input_guards import _INJECTION_PATTERNS, _normalise


async def ingest_document(
    doc_id: int,
    filename: str,
    content: bytes,
    db: AsyncSession,
) -> None:
    """Full ingestion pipeline for one document."""
    settings = get_settings()
    injection_risk = False

    try:
        # Parse
        text = await asyncio.to_thread(_parse_document, filename, content)
        # Chunk
        chunks = await asyncio.to_thread(_chunk_text, text, settings.chunk_size, settings.chunk_overlap)
        # Scan each chunk for indirect injection (IPI attack surface)
        clean_chunks = []
        for chunk in chunks:
            if _chunk_has_injection_risk(chunk):
                injection_risk = True
                logger.warning(
                    "indirect_injection_detected",
                    doc_id=doc_id,
                    chunk_preview=chunk[:80],
                )
            else:
                clean_chunks.append(chunk)

        # Embed and store only clean chunks
        chunk_count = await _embed_and_store(doc_id, clean_chunks, settings)

        await db.execute(
            update(Document)
            .where(Document.id == doc_id)
            .values(
                status="ready",
                chunk_count=chunk_count,
                injection_risk=injection_risk,
            )
        )
        await db.commit()
        logger.info("document_ingested", doc_id=doc_id, chunks=chunk_count, injection_risk=injection_risk)

    except Exception as exc:
        logger.error("ingestion_failed", doc_id=doc_id, error=str(exc))
        await db.execute(
            update(Document).where(Document.id == doc_id).values(status="error")
        )
        await db.commit()
        raise


def _parse_document(filename: str, content: bytes) -> str:
    """Extract plain text from the document bytes."""
    import pathlib
    ext = pathlib.Path(filename).suffix.lower()

    if ext == ".pdf":
        import fitz  # PyMuPDF
        doc = fitz.open(stream=content, filetype="pdf")
        return "\n\n".join(page.get_text() for page in doc)
    elif ext in (".md", ".txt", ".html"):
        return content.decode("utf-8", errors="replace")
    else:
        return content.decode("utf-8", errors="replace")


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Sentence-aware chunking using LlamaIndex SentenceSplitter."""
    from llama_index.core.node_parser import SentenceSplitter
    splitter = SentenceSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        paragraph_separator="\n\n",
    )
    from llama_index.core import Document as LIDocument
    nodes = splitter.get_nodes_from_documents([LIDocument(text=text)])
    return [node.get_content() for node in nodes]


def _chunk_has_injection_risk(chunk: str) -> bool:
    """Return True if the chunk contains embedded LLM instructions."""
    normalised = _normalise(chunk)
    return any(p.search(normalised) for p in _INJECTION_PATTERNS)


async def _embed_and_store(doc_id: int, chunks: list[str], settings) -> int:
    """Generate embeddings and store in pgvector."""
    if not chunks:
        return 0

    from rag_guardrails.retrieval.embeddings import get_embed_model
    from rag_guardrails.models.document_chunk import DocumentChunk
    from rag_guardrails.core.database import AsyncSessionLocal

    model = get_embed_model()
    embeddings = await asyncio.to_thread(
        lambda: [model.get_text_embedding(c) for c in chunks]
    )

    async with AsyncSessionLocal() as db:
        for idx, (text, emb) in enumerate(zip(chunks, embeddings)):
            db.add(DocumentChunk(
                doc_id=doc_id,
                chunk_index=idx,
                text=text,
                embedding=emb,
            ))
        await db.commit()

    logger.info("embeddings_stored", doc_id=doc_id, count=len(embeddings))
    return len(chunks)
