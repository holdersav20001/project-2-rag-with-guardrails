"""FastAPI dependencies — API key auth, DB session, settings."""
import secrets
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from rag_guardrails.core.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    """
    Validate the X-API-Key header.
    - No key → 401
    - Empty key → 401
    - Wrong key → 401 (constant-time comparison to prevent timing attacks)
    - Query-string fallback intentionally not supported.
    """
    settings = get_settings()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Constant-time comparison prevents timing attacks (AUTH-007).
    # settings.api_key is already stripped at load time (see config.py validator).
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key
