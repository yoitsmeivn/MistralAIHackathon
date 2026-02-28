# pyright: reportMissingImports=false
from typing import cast

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok_with_timestamp() -> None:
    response = client.get("/health")

    assert response.status_code == 200

    payload = cast(dict[str, str], response.json())
    assert payload["status"] == "ok"
    assert "timestamp" in payload
    assert isinstance(payload["timestamp"], str)
    assert payload["timestamp"]
