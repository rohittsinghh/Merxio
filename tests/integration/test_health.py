from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_response_shape() -> None:
    """The health route should keep a stable contract for ops tooling."""
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert set(response.json()) == {"status", "database"}
