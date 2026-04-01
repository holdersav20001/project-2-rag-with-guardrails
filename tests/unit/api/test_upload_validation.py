"""
Adversarial attack matrix — UPL series.
Tests written BEFORE implementation (TDD red phase).
Uses FastAPI TestClient — no Docker required.
"""
import io
import pytest
from httpx import AsyncClient


@pytest.fixture
def pdf_bytes() -> bytes:
    # Minimal valid PDF header
    return b"%PDF-1.4\n%EOF"


@pytest.fixture
def exe_bytes() -> bytes:
    return b"MZ\x90\x00" + b"\x00" * 100  # PE/COFF magic bytes


class TestUploadValidation:
    """UPL-001 through UPL-012 from the attack matrix."""

    @pytest.mark.asyncio
    async def test_upl_001_file_at_size_limit(self, async_client: AsyncClient, pdf_bytes: bytes):
        """UPL-001: Exactly 50MB should be accepted."""
        # 50MB of null bytes, valid PDF MIME
        big_pdf = b"%PDF-1.4\n" + b"\x00" * (50 * 1024 * 1024 - 9)
        response = await async_client.post(
            "/api/documents/upload",
            files={"file": ("big.pdf", io.BytesIO(big_pdf), "application/pdf")},
            headers={"X-API-Key": "test-api-key-do-not-use-in-production"},
        )
        assert response.status_code in (200, 201, 202)

    @pytest.mark.asyncio
    async def test_upl_002_file_over_size_limit(self, async_client: AsyncClient):
        """UPL-002: 50MB + 1 byte must be rejected with 413."""
        oversized = b"%PDF-1.4\n" + b"\x00" * (50 * 1024 * 1024 - 9 + 1)
        response = await async_client.post(
            "/api/documents/upload",
            files={"file": ("big.pdf", io.BytesIO(oversized), "application/pdf")},
            headers={"X-API-Key": "test-api-key-do-not-use-in-production"},
        )
        assert response.status_code == 413

    @pytest.mark.asyncio
    async def test_upl_003_exe_with_pdf_mime(self, async_client: AsyncClient, exe_bytes: bytes):
        """UPL-003: .exe bytes with PDF MIME type — rejected."""
        response = await async_client.post(
            "/api/documents/upload",
            files={"file": ("evil.pdf", io.BytesIO(exe_bytes), "application/pdf")},
            headers={"X-API-Key": "test-api-key-do-not-use-in-production"},
        )
        assert response.status_code in (415, 422)

    @pytest.mark.asyncio
    async def test_upl_004_pdf_bytes_with_exe_extension(self, async_client: AsyncClient, pdf_bytes):
        """UPL-004: Valid PDF bytes but .exe extension — rejected."""
        response = await async_client.post(
            "/api/documents/upload",
            files={"file": ("document.exe", io.BytesIO(pdf_bytes), "application/pdf")},
            headers={"X-API-Key": "test-api-key-do-not-use-in-production"},
        )
        assert response.status_code in (415, 422)

    @pytest.mark.asyncio
    async def test_upl_005_path_traversal_filename(self, async_client: AsyncClient, pdf_bytes):
        """UPL-005: Path traversal in filename — rejected."""
        response = await async_client.post(
            "/api/documents/upload",
            files={"file": ("../../etc/passwd.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers={"X-API-Key": "test-api-key-do-not-use-in-production"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upl_008_empty_file(self, async_client: AsyncClient):
        """UPL-008: 0-byte file — rejected."""
        response = await async_client.post(
            "/api/documents/upload",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
            headers={"X-API-Key": "test-api-key-do-not-use-in-production"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upl_012_unsupported_format(self, async_client: AsyncClient):
        """UPL-012: .docx file — rejected with supported formats listed."""
        docx_bytes = b"PK\x03\x04" + b"\x00" * 20  # ZIP magic (DOCX is a ZIP)
        response = await async_client.post(
            "/api/documents/upload",
            files={"file": ("report.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers={"X-API-Key": "test-api-key-do-not-use-in-production"},
        )
        assert response.status_code in (415, 422)
        body = response.json()
        assert "detail" in body


class TestAuthentication:
    """AUTH-001 through AUTH-008 from the attack matrix."""

    @pytest.mark.asyncio
    async def test_auth_001_no_api_key(self, async_client: AsyncClient):
        """AUTH-001: No API key header → 401."""
        response = await async_client.post("/api/query", json={"query": "test"})
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_002_empty_string_key(self, async_client: AsyncClient):
        """AUTH-002: Empty string API key → 401."""
        response = await async_client.post(
            "/api/query",
            json={"query": "test"},
            headers={"X-API-Key": ""},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_003_wrong_key(self, async_client: AsyncClient):
        """AUTH-003: Invalid API key → 401."""
        response = await async_client.post(
            "/api/query",
            json={"query": "test"},
            headers={"X-API-Key": "completely-wrong-key"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_005_valid_key(self, async_client: AsyncClient):
        """AUTH-005: Valid API key → not 401."""
        response = await async_client.post(
            "/api/query",
            json={"query": "What is our data retention policy?"},
            headers={"X-API-Key": "test-api-key-do-not-use-in-production"},
        )
        assert response.status_code != 401

    @pytest.mark.asyncio
    async def test_auth_006_health_check_public(self, async_client: AsyncClient):
        """AUTH-006: Health check must return 200 with no API key."""
        response = await async_client.get("/api/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_auth_008_key_in_querystring_rejected(self, async_client: AsyncClient):
        """AUTH-008: Key in query string must not be accepted."""
        response = await async_client.post(
            "/api/query?api_key=test-api-key-do-not-use-in-production",
            json={"query": "test"},
        )
        assert response.status_code == 401
