"""Tests for the GET /health liveness and readiness endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

try:
    from src.api import app as _real_app

    _HAS_APP = True
except ImportError:  # pragma: no cover - depends on optional langchain-ollama
    _HAS_APP = False

_SKIP_REASON = "Requires langchain-ollama (not installed in this environment)"


@pytest.mark.skipif(not _HAS_APP, reason=_SKIP_REASON)
class TestHealthEndpoint:
    """GET /health reports service and LLM readiness."""

    def test_health_returns_ok(self):
        client = TestClient(_real_app)
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert data["healthy"] is True
        assert data["graph_loaded"] is True
        assert data["version"]
        # ollama is the default local backend and needs no credentials
        assert data["llm"]["configured"]["ollama"] is True
        # Without a probe no network I/O happens, so the field is absent.
        assert "ollama_reachable" not in data["llm"]

    def test_health_reports_configured_providers(self):
        client = TestClient(_real_app)
        configured = client.get("/health").json()["llm"]["configured"]
        assert "openrouter" in configured
        assert "openai" in configured
        assert isinstance(configured["openrouter"], bool)

    def test_health_probe_never_raises_without_model_server(self):
        """?probe=true must return a bool even when Ollama is down/absent."""
        client = TestClient(_real_app)
        response = client.get("/health", params={"probe": "true"})
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["llm"]["ollama_reachable"], bool)
        # Health is about the service itself: an unreachable LLM degrades the
        # status but must not make the endpoint error out.
        assert data["status"] in ("ok", "degraded")

    def test_health_is_a_get_route(self):
        client = TestClient(_real_app)
        assert client.post("/health").status_code == 405

    def test_unready_instance_answers_503(self):
        """A probe that only checks the status code must see the failure."""
        client = TestClient(_real_app)
        original = _real_app.state.graph
        _real_app.state.graph = None
        try:
            response = client.get("/health")
        finally:
            _real_app.state.graph = original

        assert response.status_code == 503
        assert response.json()["status"] == "degraded"
        assert response.json()["healthy"] is False

    def test_health_reports_the_release_version(self):
        """The probe must not advertise a stale version."""
        client = TestClient(_real_app)
        response = client.get("/health")

        assert response.json()["version"] == _real_app.version
        assert _real_app.version not in ("0.1.0", "0.2.0", "0.3.0")
