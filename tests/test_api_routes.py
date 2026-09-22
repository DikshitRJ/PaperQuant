import pytest


app_module = pytest.importorskip("api.app")
pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


def test_app_exposes_documented_http_routes():
    app = app_module.create_app()
    paths = {route.path for route in app.routes}

    expected = {
        "/api/health",
        "/api/session/start",
        "/api/session/stop",
        "/api/session/reset",
        "/api/session/status",
        "/api/positions",
        "/api/positions/history",
        "/api/stats",
        "/api/stats/chart",
        "/api/algorithms",
        "/api/settings",
        "/api/logs",
        "/api/market/prices",
        "/ws",
    }
    assert expected <= paths


def test_health_route_returns_contract_shape():
    client = TestClient(app_module.create_app())
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert {"version", "uptime_seconds", "adapters"} <= body
