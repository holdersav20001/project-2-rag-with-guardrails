"""Integration tests — health endpoint."""
import pytest


def test_health_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["models"] == "ok"


def test_health_no_auth_required(client):
    """Health check must be publicly accessible (no API key)."""
    import httpx
    with httpx.Client(base_url="http://localhost:8000", timeout=10.0) as anon:
        r = anon.get("/api/health")
    assert r.status_code == 200


def test_protected_route_requires_key():
    """All non-health routes must reject missing API key with 401."""
    import httpx
    with httpx.Client(base_url="http://localhost:8000", timeout=10.0) as anon:
        r = anon.get("/api/documents")
    assert r.status_code == 401
