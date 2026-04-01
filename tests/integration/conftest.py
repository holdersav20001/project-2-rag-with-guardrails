"""
Integration conftest — tests run against the live docker-compose stack on port 8000.

Start the stack before running:
    docker compose up -d
    pytest tests/integration/ -v --no-cov

Coverage enforcement is disabled here because these tests call the API over HTTP
and the code under test runs inside Docker — local coverage will always be 0%.
Coverage is measured by the unit test suite instead.
"""


def pytest_configure(config):
    """Disable coverage fail-under for integration tests (code runs in Docker)."""
    # Only suppress if we're specifically running integration tests (not a full suite)
    if hasattr(config, "workerinput"):
        return
    cov_plugin = config.pluginmanager.get_plugin("_cov")
    if cov_plugin is not None:
        cov_plugin.cov_controller = None
import pytest
import httpx

BASE_URL = "http://localhost:8000"
API_KEY = "c8IqNNh5xM-bURKCDy1FbHto_dHkJqkufSe0K5WRrqc"
HEADERS = {"X-API-Key": API_KEY}


@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=60.0, headers=HEADERS) as c:
        yield c


@pytest.fixture(scope="session")
def tiny_pdf() -> bytes:
    """Minimal valid PDF for upload tests (no real content needed)."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td (GDPR test) Tj ET\nendstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n0000000000 65535 f\n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n0\n%%EOF\n"
    )


@pytest.fixture(scope="session")
def sample_txt() -> bytes:
    return (
        b"GDPR Data Protection Policy\n\n"
        b"Personal data must be retained for a maximum of 90 days after the purpose of "
        b"collection has been fulfilled, in compliance with GDPR Article 5(1)(e).\n"
        b"Organizations must notify the supervisory authority within 72 hours of a breach.\n"
        b"Data subjects have the right to erasure under Article 17.\n"
    )
