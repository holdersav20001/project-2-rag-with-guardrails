"""Unit test conftest — fixtures that require no external services."""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def async_client():
    """FastAPI test client — no real DB or models required for unit tests."""
    # Import is deferred so env vars are set before app is initialised
    from rag_guardrails.api.app import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
