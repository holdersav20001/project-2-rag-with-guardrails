"""Document management endpoints — upload, list, delete."""
from __future__ import annotations

import asyncio
import pathlib
import re
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_guardrails.api.app import limiter
from rag_guardrails.api.dependencies import require_api_key
from rag_guardrails.core.config import get_settings
from rag_guardrails.core.database import AsyncSessionLocal, get_db
from rag_guardrails.core.logging import get_logger
from rag_guardrails.models.document import Document

logger = get_logger(__name__)
router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/markdown",
    "text/plain",
    "text/html",
}
ALLOWED_EXTENSIONS = {".pdf", ".md", ".txt", ".html"}

# Semaphore — max 3 concurrent ingestions (back-pressure cap)
_ingestion_semaphore = asyncio.Semaphore(3)


def _validate_filename(filename: str) -> str:
    """
    Sanitise filename — reject path traversal, null bytes, excessive length.
    Returns safe basename.
    """
    if "\x00" in filename:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid filename: null byte")

    # Strip any directory components (UPL-005)
    safe = pathlib.Path(filename).name
    if safe != filename and (".." in filename or "/" in filename or "\\" in filename):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Invalid filename: path traversal detected",
        )

    if len(safe) > 255:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Filename too long")

    # Keep only safe characters
    safe = re.sub(r"[^\w\-_. ]", "_", safe)
    return safe


@dataclass
class _ValidatedUpload:
    content: bytes
    safe_name: str


async def _validate_upload(file: UploadFile, settings) -> _ValidatedUpload:
    """
    Read and validate uploaded file. Returns a _ValidatedUpload dataclass so
    callers get a single authoritative (content, safe_name) pair — avoiding the
    TOCTOU risk of calling _validate_filename twice with independent results.
    Raises HTTPException on any violation.
    """
    content = await file.read()

    # UPL-008: empty file
    if len(content) == 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "File is empty")

    # UPL-002: size check
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds maximum size of {settings.max_upload_size_mb}MB",
        )

    # Filename sanitisation + extension check (UPL-004, UPL-005)
    safe_name = _validate_filename(file.filename or "upload")
    ext = pathlib.Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # MIME type check (UPL-003) — absent content-type is also rejected
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if not content_type or content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Missing or unsupported MIME type '{content_type}'. Allowed: {sorted(ALLOWED_MIME_TYPES)}",
        )

    # Content-level validation
    if ext == ".pdf":
        # PDF must start with %PDF magic bytes
        if not content.startswith(b"%PDF"):
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                "File does not appear to be a valid PDF",
            )
    else:
        # Text-based formats (.txt, .md, .html) must be valid UTF-8
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                f"File is not valid UTF-8 text (ext='{ext}')",
            )

    return _ValidatedUpload(content=content, safe_name=safe_name)


@router.post("/documents/upload", status_code=202)
@limiter.limit(lambda: get_settings().upload_rate_limit)
async def upload_document(
    request: Request,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(require_api_key),
):
    settings = get_settings()
    validated = await _validate_upload(file, settings)
    content, safe_name = validated.content, validated.safe_name
    content_hash = Document.compute_hash(content)

    # Deduplication — skip if already ingested (UPL-009)
    existing = await db.execute(
        select(Document).where(Document.content_hash == content_hash)
    )
    if doc := existing.scalar_one_or_none():
        logger.info("document_deduplicated", filename=safe_name, document_id=doc.id)
        return {
            "document_id": doc.id,
            "filename": doc.filename,
            "status": "already_exists",
            "message": "Document with identical content already ingested",
        }

    # Create document record
    doc = Document(
        filename=safe_name,
        content_hash=content_hash,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        status="processing",
    )
    db.add(doc)
    await db.flush()
    doc_id = doc.id

    # Trigger async ingestion — task opens its own session so it is not
    # bound to this request's session lifetime (fix for session-scope bug).
    asyncio.create_task(_ingest(doc_id, safe_name, content))

    return {"document_id": doc_id, "filename": safe_name, "status": "processing"}


async def _ingest(doc_id: int, filename: str, content: bytes) -> None:
    """Run ingestion in a fresh session independent of the request lifecycle."""
    async with _ingestion_semaphore:
        async with AsyncSessionLocal() as db:
            from rag_guardrails.ingestion.pipeline import ingest_document
            await ingest_document(doc_id, filename, content, db)


@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(require_api_key),
):
    result = await db.execute(
        select(Document).order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "file_size": d.file_size,
                "chunk_count": d.chunk_count,
                "injection_risk": d.injection_risk,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ]
    }


@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(require_api_key),
):
    """Return a single document's metadata including current ingestion status."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_size": doc.file_size,
        "chunk_count": doc.chunk_count,
        "injection_risk": doc.injection_risk,
        "status": doc.status,
        "created_at": doc.created_at.isoformat(),
    }


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    _key: str = Depends(require_api_key),
):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")

    # Chunks are deleted automatically via ON DELETE CASCADE on document_chunks.doc_id
    await db.delete(doc)
    logger.info("document_deleted", document_id=document_id, filename=doc.filename)
