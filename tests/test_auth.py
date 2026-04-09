from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_quest_no_key_configured_returns_503(client):
    """When KTRT_API_KEY is not set, deny all requests with 503."""
    with patch("app.api.deps.settings") as mock_settings:
        mock_settings.ktrt_api_key = ""
        resp = client.post("/v1/quests", json={"query": "test"})
    assert resp.status_code == 503


def test_quest_wrong_key_returns_401(client):
    """Wrong API key must return 401."""
    with patch("app.api.deps.settings") as mock_settings:
        mock_settings.ktrt_api_key = "correct-key"
        resp = client.post(
            "/v1/quests",
            json={"query": "test"},
            headers={"X-API-Key": "wrong-key"},
        )
    assert resp.status_code == 401


def test_quest_missing_key_header_returns_401(client):
    """Missing X-API-Key header must return 401 when a key is configured."""
    with patch("app.api.deps.settings") as mock_settings:
        mock_settings.ktrt_api_key = "correct-key"
        resp = client.post("/v1/quests", json={"query": "test"})
    assert resp.status_code == 401


def test_healthz_requires_no_key(client):
    """Health check must be publicly accessible regardless of auth config."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
