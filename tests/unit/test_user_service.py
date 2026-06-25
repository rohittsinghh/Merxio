from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreateRequest, AddressUpdateRequest
from app.schemas.user import UserUpdateRequest
from app.services.user import UserService


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeUserProfileRepository:
    async def update_profile(self, user: User, *, first_name: str, last_name: str) -> User:
        user.first_name = first_name
        user.last_name = last_name
        return user


class FakeAddressRepository:
    def __init__(self) -> None:
        self.addresses: dict[object, Address] = {}
        self.unset_calls: list[tuple[object, str]] = []

    async def list_for_user(self, user_id):
        return [address for address in self.addresses.values() if address.user_id == user_id]

    async def get_for_user(self, *, address_id, user_id):
        address = self.addresses.get(address_id)
        if address is None or address.user_id != user_id:
            return None
        return address

    async def create(self, *, user_id, values: dict):
        address = Address(
            id=uuid4(),
            user_id=user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            **values,
        )
        self.addresses[address.id] = address
        return address

    async def update(self, address: Address, values: dict):
        for field, value in values.items():
            setattr(address, field, value)
        return address

    async def delete(self, address: Address):
        self.addresses.pop(address.id, None)

    async def unset_default_for_type(self, *, user_id, address_type: str):
        self.unset_calls.append((user_id, address_type))
        for address in self.addresses.values():
            if address.user_id == user_id and address.address_type == address_type:
                address.is_default = False


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


def build_service() -> tuple[UserService, FakeAddressRepository, FakeSession]:
    session = FakeSession()
    address_repository = FakeAddressRepository()
    service = UserService(
        session=session,
        user_repository=FakeUserProfileRepository(),
        address_repository=address_repository,
    )
    return service, address_repository, session


@pytest.mark.asyncio
async def test_update_profile_changes_current_user() -> None:
    """Profile updates should only mutate the authenticated user object."""

    service, _, session = build_service()
    user = make_user()

    updated_user = await service.update_profile(
        user,
        UserUpdateRequest(first_name="Grace", last_name="Hopper"),
    )

    assert updated_user.first_name == "Grace"
    assert updated_user.last_name == "Hopper"
    assert session.commits == 1


@pytest.mark.asyncio
async def test_create_default_address_unsets_existing_default_for_type() -> None:
    """Only one default shipping or billing address should exist per user."""

    service, address_repository, _ = build_service()
    user = make_user()

    address = await service.create_address(
        user,
        AddressCreateRequest(
            address_type="shipping",
            full_name="Ada Lovelace",
            phone_number="1234567890",
            line1="1 Algorithm Ave",
            city="London",
            state="London",
            postal_code="SW1A 1AA",
            country="GB",
            is_default=True,
        ),
    )

    assert address.is_default is True
    assert address_repository.unset_calls == [(user.id, "shipping")]


@pytest.mark.asyncio
async def test_update_address_rejects_address_owned_by_another_user() -> None:
    """Ownership checks belong in the service layer, not the router."""

    service, address_repository, _ = build_service()
    owner = make_user()
    other_user = make_user()
    address = await address_repository.create(
        user_id=owner.id,
        values={
            "address_type": "shipping",
            "full_name": "Ada Lovelace",
            "phone_number": "1234567890",
            "line1": "1 Algorithm Ave",
            "line2": None,
            "city": "London",
            "state": "London",
            "postal_code": "SW1A 1AA",
            "country": "GB",
            "is_default": False,
        },
    )

    with pytest.raises(AppException) as exc_info:
        await service.update_address(
            user=other_user,
            address_id=address.id,
            payload=AddressUpdateRequest(
                address_type="shipping",
                full_name="Other User",
                phone_number="1234567890",
                line1="2 Different St",
                city="London",
                state="London",
                postal_code="SW1A 1AA",
                country="GB",
                is_default=False,
            ),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "address_not_found"
