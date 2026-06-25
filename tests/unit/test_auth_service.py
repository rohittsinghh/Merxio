from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import UserLoginRequest, UserRegisterRequest
from app.security.passwords import hash_password
from app.security.tokens import hash_refresh_token
from app.services.auth import AuthService


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeUserRepository:
    def __init__(self) -> None:
        self.users_by_email: dict[str, User] = {}
        self.users_by_id: dict[object, User] = {}
        self.refresh_tokens: dict[str, RefreshToken] = {}
        self.permissions: set[str] = set()

    async def get_by_id(self, user_id):
        return self.users_by_id.get(user_id)

    async def get_by_email(self, email: str):
        return self.users_by_email.get(email.lower())

    async def create_user(self, *, email: str, password_hash: str, first_name: str, last_name: str):
        user = User(
            id=uuid4(),
            email=email.lower(),
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            is_verified=False,
            created_at=datetime.now(UTC),
        )
        self.users_by_email[user.email] = user
        self.users_by_id[user.id] = user
        return user

    async def create_refresh_token(self, *, user_id, token_hash: str, expires_at):
        refresh_token = RefreshToken(
            id=uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_active=True,
            user=self.users_by_id[user_id],
        )
        self.refresh_tokens[token_hash] = refresh_token
        return refresh_token

    async def get_refresh_token(self, token_hash: str):
        return self.refresh_tokens.get(token_hash)

    async def revoke_refresh_token(self, refresh_token, *, revoked_at, replaced_by_token_hash=None):
        refresh_token.is_active = False
        refresh_token.revoked_at = revoked_at
        refresh_token.replaced_by_token_hash = replaced_by_token_hash

    async def get_user_permissions(self, user_id):
        return self.permissions


def build_service() -> tuple[AuthService, FakeUserRepository, FakeSession]:
    session = FakeSession()
    repository = FakeUserRepository()
    return AuthService(session=session, user_repository=repository), repository, session


@pytest.mark.asyncio
async def test_register_creates_user_with_hashed_password() -> None:
    """Registration should hash passwords and issue tokens in one transaction."""

    service, repository, session = build_service()

    response = await service.register(
        UserRegisterRequest(
            email="User@Example.com",
            password="very-secure-password",
            first_name="Ada",
            last_name="Lovelace",
        )
    )

    user = repository.users_by_email["user@example.com"]
    assert user.password_hash != "very-secure-password"
    assert response.access_token
    assert response.refresh_token
    assert session.commits == 1


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email() -> None:
    """Email uniqueness is a business rule, not only a database constraint."""

    service, _, _ = build_service()
    payload = UserRegisterRequest(
        email="ada@example.com",
        password="very-secure-password",
        first_name="Ada",
        last_name="Lovelace",
    )

    await service.register(payload)

    with pytest.raises(AppException) as exc_info:
        await service.register(payload)

    assert exc_info.value.error_code == "email_already_registered"


@pytest.mark.asyncio
async def test_login_succeeds_with_correct_credentials() -> None:
    """A valid email and password should return a token pair."""

    service, repository, _ = build_service()
    user = await repository.create_user(
        email="ada@example.com",
        password_hash=hash_password("very-secure-password"),
        first_name="Ada",
        last_name="Lovelace",
    )

    response = await service.login(
        UserLoginRequest(email=user.email, password="very-secure-password")
    )

    assert response.user.id == user.id
    assert response.access_token
    assert response.refresh_token


@pytest.mark.asyncio
async def test_login_fails_with_wrong_password() -> None:
    """Invalid credentials should not reveal whether the email exists."""

    service, repository, _ = build_service()
    await repository.create_user(
        email="ada@example.com",
        password_hash=hash_password("very-secure-password"),
        first_name="Ada",
        last_name="Lovelace",
    )

    with pytest.raises(AppException) as exc_info:
        await service.login(UserLoginRequest(email="ada@example.com", password="wrong"))

    assert exc_info.value.error_code == "invalid_credentials"


@pytest.mark.asyncio
async def test_refresh_token_rotation_revokes_old_token() -> None:
    """Refresh should rotate tokens so replaying the old token becomes invalid."""

    service, repository, _ = build_service()
    user = await repository.create_user(
        email="ada@example.com",
        password_hash=hash_password("very-secure-password"),
        first_name="Ada",
        last_name="Lovelace",
    )
    raw_refresh_token = "raw-refresh-token"
    token_hash = hash_refresh_token(raw_refresh_token)
    stored_token = RefreshToken(
        id=uuid4(),
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=1),
        is_active=True,
        user=user,
    )
    repository.refresh_tokens[token_hash] = stored_token

    response = await service.refresh(raw_refresh_token)

    assert response.refresh_token != raw_refresh_token
    assert stored_token.is_active is False
    assert stored_token.replaced_by_token_hash is not None


@pytest.mark.asyncio
async def test_user_has_permission_reads_rbac_permissions() -> None:
    """RBAC decisions should be delegated to repository permission lookup."""

    service, repository, _ = build_service()
    repository.permissions = {"orders:read"}

    assert await service.user_has_permission(uuid4(), "orders:read")
    assert not await service.user_has_permission(uuid4(), "orders:write")
