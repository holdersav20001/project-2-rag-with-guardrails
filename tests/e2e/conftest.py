"""
E2E conftest — tests run against the live docker-compose stack on port 8000.

Start the stack before running:
    docker compose up -d
    pytest tests/e2e/ -v --no-cov
"""
import time

import httpx
import pytest

E2E_BASE_URL = "http://localhost:8000"
E2E_API_KEY = "c8IqNNh5xM-bURKCDy1FbHto_dHkJqkufSe0K5WRrqc"


@pytest.fixture(scope="session")
def e2e_headers():
    return {"X-API-Key": E2E_API_KEY}


@pytest.fixture(scope="session")
def e2e_client():
    """Unauthenticated client — pass e2e_headers explicitly when auth is required."""
    with httpx.Client(base_url=E2E_BASE_URL, timeout=60.0) as client:
        yield client


@pytest.fixture(scope="session")
def sample_txt() -> bytes:
    return (
        b"GDPR Data Protection Policy\n\n"
        b"Personal data must be retained for a maximum of 90 days after the purpose of "
        b"collection has been fulfilled, in compliance with GDPR Article 5(1)(e).\n"
        b"Organizations must notify the supervisory authority within 72 hours of a breach.\n"
        b"Data subjects have the right to erasure under Article 17.\n"
    )


def wait_for_ready(client: httpx.Client, doc_id: int, timeout: int = 30) -> str:
    """Poll document status until not processing. Returns final status."""
    deadline = time.time() + timeout
    status = "processing"
    while status == "processing" and time.time() < deadline:
        time.sleep(1)
        r = client.get(f"/api/documents/{doc_id}")
        if r.status_code == 200:
            status = r.json()["status"]
    return status
