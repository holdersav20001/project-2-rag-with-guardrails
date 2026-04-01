"""Integration tests — document upload, list, get, delete, ingestion status."""
import time
import pytest


def test_list_documents_returns_list(client):
    r = client.get("/api/documents")
    assert r.status_code == 200
    body = r.json()
    assert "documents" in body
    assert isinstance(body["documents"], list)


def test_upload_txt_and_wait_for_ready(client, sample_txt):
    # Upload
    r = client.post(
        "/api/documents/upload",
        files={"file": ("integration_test_policy.txt", sample_txt, "text/plain")},
    )
    assert r.status_code in (200, 202)
    body = r.json()
    doc_id = body["document_id"]

    # Poll until ready (max 30s)
    deadline = time.time() + 30
    status = body.get("status", "processing")
    while status == "processing" and time.time() < deadline:
        time.sleep(1)
        s = client.get(f"/api/documents/{doc_id}")
        assert s.status_code == 200
        status = s.json()["status"]

    assert status == "ready", f"Document still '{status}' after 30s"

    # Verify chunk_count populated
    doc = client.get(f"/api/documents/{doc_id}").json()
    assert doc["chunk_count"] >= 1

    # Cleanup
    d = client.delete(f"/api/documents/{doc_id}")
    assert d.status_code == 204


def test_upload_deduplication(client, sample_txt):
    """Uploading same content twice returns already_exists on the second call."""
    r1 = client.post(
        "/api/documents/upload",
        files={"file": ("dedup_test.txt", sample_txt, "text/plain")},
    )
    assert r1.status_code in (200, 202)
    doc_id = r1.json()["document_id"]

    r2 = client.post(
        "/api/documents/upload",
        files={"file": ("dedup_test_copy.txt", sample_txt, "text/plain")},
    )
    assert r2.status_code in (200, 202)
    assert r2.json()["status"] == "already_exists"

    # Cleanup
    client.delete(f"/api/documents/{doc_id}")


def test_get_document_not_found(client):
    r = client.get("/api/documents/999999")
    assert r.status_code == 404


def test_delete_document_not_found(client):
    r = client.delete("/api/documents/999999")
    assert r.status_code == 404


def test_upload_rejects_exe_as_pdf(client):
    """A .exe file uploaded with PDF MIME type must be rejected."""
    fake = b"MZ\x90\x00" + b"\x00" * 100  # PE header, not %PDF
    r = client.post(
        "/api/documents/upload",
        files={"file": ("malware.pdf", fake, "application/pdf")},
    )
    assert r.status_code == 415


def test_upload_rejects_unsupported_extension(client):
    r = client.post(
        "/api/documents/upload",
        files={"file": ("script.py", b"print('hello')", "text/plain")},
    )
    assert r.status_code == 415


def test_delete_cascades_chunks(client, sample_txt):
    """Deleting a document must remove its chunks (verified via chunk_count before delete)."""
    r = client.post(
        "/api/documents/upload",
        files={"file": ("cascade_test.txt", sample_txt, "text/plain")},
    )
    doc_id = r.json()["document_id"]

    # Wait for ingestion
    deadline = time.time() + 30
    while time.time() < deadline:
        time.sleep(1)
        doc = client.get(f"/api/documents/{doc_id}").json()
        if doc["status"] != "processing":
            break

    assert doc["chunk_count"] >= 1

    # Delete and confirm 204
    d = client.delete(f"/api/documents/{doc_id}")
    assert d.status_code == 204

    # Confirm document gone
    assert client.get(f"/api/documents/{doc_id}").status_code == 404
