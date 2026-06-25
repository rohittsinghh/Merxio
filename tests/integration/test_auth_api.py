from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies.auth import get_auth_service, get_current_user
from app.main import create_app
from app.models.user import User
from app.schemas.auth import AuthTokenResponse, UserPublicResponse


def make_user() -> User:
    return User(
        id=uuid4(),
        email="ada@example.com",
        password_hash="not-used-in-api-test",
        first_name="Ada",
        last_name="Lovelace",
        is_active=True,
        is_verified=False,
        created_at=datetime.now(UTC),
    )


class FakeAuthService:
    def __init__(self) -> None:
        self.user = make_user()

    async def register(self, payload):
        return self._token_response()

    async def login(self, payload):
        return self._token_response()

    async def refresh(self, refresh_token: str):
        return self._token_response(refresh_token="new-refresh-token")

    async def logout(self, refresh_token: str) -> None:
        return None

    def _token_response(self, refresh_token: str = "refresh-token") -> AuthTokenResponse:
        return AuthTokenResponse(
            access_token="access-token",
            refresh_token=refresh_token,
            user=UserPublicResponse.model_validate(self.user),
        )


def test_register_endpoint_returns_token_pair() -> None:
    """The route should expose the auth service result without DB logic."""

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "ada@example.com",
            "password": "very-secure-password",
            "first_name": "Ada",
            "last_name": "Lovelace",
        },
    )

    assert response.status_code == 201
    assert response.json()["access_token"] == "access-token"


def test_login_endpoint_returns_token_pair() -> None:
    """Login should return tokens through the public API contract."""

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ada@example.com", "password": "very-secure-password"},
    )

    assert response.status_code == 200
    assert response.json()["refresh_token"] == "refresh-token"


def test_refresh_endpoint_rotates_token() -> None:
    """Refresh should return a replacement refresh token."""

    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: FakeAuthService()
    client = TestClient(app)

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "old-refresh-token"})

    assert response.status_code == 200
    assert response.json()["refresh_token"] == "new-refresh-token"


def test_protected_endpoint_rejects_unauthenticated_requests() -> None:
    """Protected routes should fail when no bearer token is supplied."""

    client = TestClient(create_app())

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_protected_endpoint_returns_current_user() -> None:
    """Dependency overrides let API tests verify route behavior without a real JWT."""

    app = create_app()
    current_user = make_user()
    app.dependency_overrides[get_current_user] = lambda: current_user
    client = TestClient(app)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == current_user.email
