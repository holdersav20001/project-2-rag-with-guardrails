"""
E2E full-pipeline tests — covers gaps not addressed by test_adversarial.py:
  - Evaluation API (POST /evaluations, GET /evaluations/{run_id})
  - Session history (multi-turn queries with session_id)
  - Query routing (structured metadata queries return numeric answers)
  - Output guardrails (response contains grounded flag)
  - Ingestion status polling (upload → processing → ready)

Requires docker compose stack:
    docker compose up -d
    pytest tests/e2e/ -v --no-cov
"""
import time

import pytest

pytestmark = [pytest.mark.e2e]


# ---------------------------------------------------------------------------
# Evaluation API
# ---------------------------------------------------------------------------

class TestEvaluationAPI:
    """Verify the async evaluation pipeline endpoints."""

    def test_start_evaluation_returns_run_id(self, e2e_client, e2e_headers):
        """POST /evaluations returns 202 with a run_id."""
        payload = {
            "questions": ["What is the GDPR data retention limit?"],
            "ground_truths": ["Personal data must not be kept longer than necessary."],
        }
        r = e2e_client.post("/api/evaluations", json=payload, headers=e2e_headers)
        assert r.status_code == 202
        body = r.json()
        assert "run_id" in body
        assert body["status"] in ("pending", "running")

    def test_get_evaluation_status(self, e2e_client, e2e_headers):
        """GET /evaluations/{run_id} returns the run status."""
        payload = {
            "questions": ["What rights do data subjects have under GDPR?"],
            "ground_truths": ["Data subjects have the right of access, erasure, and portability."],
        }
        r = e2e_client.post("/api/evaluations", json=payload, headers=e2e_headers)
        assert r.status_code == 202
        run_id = r.json()["run_id"]

        status_r = e2e_client.get(f"/api/evaluations/{run_id}", headers=e2e_headers)
        assert status_r.status_code == 200
        body = status_r.json()
        assert body["run_id"] == run_id
        assert body["status"] in ("pending", "running", "complete", "failed")

    def test_results_returns_409_while_pending(self, e2e_client, e2e_headers):
        """GET /evaluations/{run_id}/results returns 409 before evaluation completes."""
        payload = {
            "questions": ["What is a subject access request?"],
            "ground_truths": ["A SAR is a request by an individual to access their personal data."],
        }
        r = e2e_client.post("/api/evaluations", json=payload, headers=e2e_headers)
        assert r.status_code == 202
        run_id = r.json()["run_id"]

        # Immediately check results — should be pending/running, not complete
        results_r = e2e_client.get(f"/api/evaluations/{run_id}/results", headers=e2e_headers)
        # Either 409 (not complete yet) or 200 (completed very fast — unlikely but valid)
        assert results_r.status_code in (200, 409)
        if results_r.status_code == 409:
            assert "not complete" in results_r.json()["detail"].lower()

    def test_evaluation_invalid_input_lengths(self, e2e_client, e2e_headers):
        """POST /evaluations with mismatched list lengths returns 422."""
        payload = {
            "questions": ["Question one", "Question two"],
            "ground_truths": ["Only one truth"],
        }
        r = e2e_client.post("/api/evaluations", json=payload, headers=e2e_headers)
        assert r.status_code == 422

    def test_evaluation_not_found(self, e2e_client, e2e_headers):
        """GET /evaluations/{run_id} with unknown ID returns 404."""
        r = e2e_client.get("/api/evaluations/00000000-0000-0000-0000-000000000000", headers=e2e_headers)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Session history (multi-turn)
# ---------------------------------------------------------------------------

class TestSessionHistory:
    """Multi-turn conversation with a shared session_id."""

    def test_session_id_accepted(self, e2e_client, e2e_headers):
        """Query accepts a session_id without error."""
        r = e2e_client.post(
            "/api/query",
            json={"query": "What is GDPR?", "session_id": "e2e-session-001"},
            headers=e2e_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("blocked") is False

    def test_second_turn_same_session(self, e2e_client, e2e_headers):
        """Two queries with the same session_id both succeed."""
        session_id = "e2e-session-002"
        first = e2e_client.post(
            "/api/query",
            json={"query": "What does GDPR stand for?", "session_id": session_id},
            headers=e2e_headers,
        )
        assert first.status_code == 200
        assert first.json().get("blocked") is False

        second = e2e_client.post(
            "/api/query",
            json={"query": "What are the key rights it grants?", "session_id": session_id},
            headers=e2e_headers,
        )
        assert second.status_code == 200
        body = second.json()
        assert body.get("blocked") is False
        assert body.get("answer") is not None


# ---------------------------------------------------------------------------
# Query routing (structured vs semantic)
# ---------------------------------------------------------------------------

class TestQueryRouting:
    """Verify the query router sends metadata queries to SQL and returns numeric answers."""

    def test_structured_document_count_returns_digit(self, e2e_client, e2e_headers):
        """'How many documents' → routed to DB, answer contains a number."""
        r = e2e_client.post(
            "/api/query",
            json={"query": "How many documents have been uploaded?"},
            headers=e2e_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("blocked") is False
        answer = body.get("answer", "")
        assert any(c.isdigit() for c in answer), f"Expected digit in answer: {answer!r}"

    def test_semantic_query_returns_sources(self, e2e_client, e2e_headers):
        """Content query → routed to vector search, sources list is present."""
        r = e2e_client.post(
            "/api/query",
            json={"query": "What are the GDPR data retention requirements?"},
            headers=e2e_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("blocked") is False
        assert "sources" in body
        assert isinstance(body["sources"], list)

    def test_structured_query_grounded_flag(self, e2e_client, e2e_headers):
        """Structured (metadata) queries must still return a grounded field."""
        r = e2e_client.post(
            "/api/query",
            json={"query": "How many documents have been uploaded?"},
            headers=e2e_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "grounded" in body
        assert isinstance(body["grounded"], bool)


# ---------------------------------------------------------------------------
# Output guardrails — grounding
# ---------------------------------------------------------------------------

class TestOutputGuardrails:
    """Verify the output grounding check is included in all non-blocked responses."""

    def test_response_includes_grounded_flag(self, e2e_client, e2e_headers):
        """Every non-blocked response includes a boolean grounded field."""
        r = e2e_client.post(
            "/api/query",
            json={"query": "What is the right of erasure under GDPR Article 17?"},
            headers=e2e_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("blocked") is False
        assert "grounded" in body
        assert isinstance(body["grounded"], bool)

    def test_response_includes_confidence(self, e2e_client, e2e_headers):
        """Every non-blocked response includes a confidence score in [0, 1]."""
        r = e2e_client.post(
            "/api/query",
            json={"query": "How long must organisations retain personal data?"},
            headers=e2e_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("blocked") is False
        confidence = body.get("confidence")
        assert confidence is not None
        assert 0.0 <= confidence <= 1.0

    def test_low_confidence_query_answered(self, e2e_client, e2e_headers):
        """Query on obscure topic may have low confidence but still returns an answer."""
        r = e2e_client.post(
            "/api/query",
            json={"query": "What specific fines did the ICO impose on our vendor in 2024?"},
            headers=e2e_headers,
        )
        assert r.status_code == 200
        body = r.json()
        # Either blocked (guardrail) or answered with possibly low confidence — both are valid
        if not body.get("blocked"):
            assert "answer" in body
            assert 0.0 <= body.get("confidence", 0.0) <= 1.0


# ---------------------------------------------------------------------------
# Ingestion status polling
# ---------------------------------------------------------------------------

class TestIngestionStatus:
    """Upload a document and verify status transitions processing → ready."""

    def test_txt_upload_reaches_ready(self, e2e_client, e2e_headers, sample_txt):
        """Upload a .txt file, poll until ready, then clean up."""
        r = e2e_client.post(
            "/api/documents/upload",
            files={"file": ("e2e_pipeline_test.txt", sample_txt, "text/plain")},
            headers=e2e_headers,
        )
        assert r.status_code in (200, 202)
        body = r.json()

        if body.get("status") == "already_exists":
            return  # Deduplication — already ingested, nothing to verify

        doc_id = body["document_id"]
        assert body["status"] in ("processing", "ready")

        # Poll until ready
        deadline = time.time() + 30
        status = body["status"]
        while status == "processing" and time.time() < deadline:
            time.sleep(1)
            s = e2e_client.get(f"/api/documents/{doc_id}", headers=e2e_headers)
            assert s.status_code == 200
            status = s.json()["status"]

        assert status == "ready", f"Document still '{status}' after 30s"

        # Verify chunk_count populated
        doc = e2e_client.get(f"/api/documents/{doc_id}", headers=e2e_headers).json()
        assert doc["chunk_count"] >= 1

        # Cleanup
        e2e_client.delete(f"/api/documents/{doc_id}", headers=e2e_headers)

    def test_get_individual_document(self, e2e_client, e2e_headers):
        """GET /documents/{id} returns 404 for a non-existent document."""
        r = e2e_client.get("/api/documents/999999", headers=e2e_headers)
        assert r.status_code == 404
