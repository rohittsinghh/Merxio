from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.dependencies.user import get_user_service
from app.main import create_app
from app.models.address import Address
from app.models.user import User


def make_user() -> User:
    return User(
        id=uuid4(),
        email="ada@example.com",
        password_hash="not-used",
        first_name="Ada",
        last_name="Lovelace",
        is_active=True,
        is_verified=False,
        created_at=datetime.now(UTC),
    )


class FakeUserService:
    def __init__(self) -> None:
        self.user = make_user()
        self.address = Address(
            id=uuid4(),
            user_id=self.user.id,
            address_type="shipping",
            full_name="Ada Lovelace",
            phone_number="1234567890",
            line1="1 Algorithm Ave",
            line2=None,
            city="London",
            state="London",
            postal_code="SW1A 1AA",
            country="GB",
            is_default=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def update_profile(self, user, payload):
        user.first_name = payload.first_name
        user.last_name = payload.last_name
        return user

    async def list_addresses(self, user):
        return [self.address]

    async def create_address(self, user, payload):
        return self.address

    async def update_address(self, *, user, address_id, payload):
        return self.address

    async def delete_address(self, *, user, address_id):
        return None


def build_client() -> TestClient:
    app = create_app()
    current_user = make_user()
    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_user_service] = lambda: FakeUserService()
    return TestClient(app)


def test_update_me_returns_updated_profile() -> None:
    """The profile route should delegate update behavior to the user service."""

    client = build_client()

    response = client.patch(
        "/api/v1/users/me",
        json={"first_name": "Grace", "last_name": "Hopper"},
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Grace"


def test_list_addresses_returns_current_user_addresses() -> None:
    """Address listing should expose the current user's address collection."""

    client = build_client()

    response = client.get("/api/v1/users/me/addresses")

    assert response.status_code == 200
    assert response.json()[0]["address_type"] == "shipping"


def test_create_address_returns_created_address() -> None:
    """Address creation should return a public address response."""

    client = build_client()

    response = client.post(
        "/api/v1/users/me/addresses",
        json={
            "address_type": "shipping",
            "full_name": "Ada Lovelace",
            "phone_number": "1234567890",
            "line1": "1 Algorithm Ave",
            "city": "London",
            "state": "London",
            "postal_code": "SW1A 1AA",
            "country": "GB",
            "is_default": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["is_default"] is True


def test_delete_address_returns_no_content() -> None:
    """Address deletion should return 204 when the service succeeds."""

    client = build_client()

    response = client.delete(f"/api/v1/users/me/addresses/{uuid4()}")

    assert response.status_code == 204
