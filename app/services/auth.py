from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import (
    AuthTokenResponse,
    UserLoginRequest,
    UserPublicResponse,
    UserRegisterRequest,
)
from app.security.passwords import hash_password, verify_password
from app.security.tokens import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    refresh_token_expires_at,
)


class AuthService:
    """Business logic for registration, login, logout, and token rotation."""

    def __init__(self, session: AsyncSession, user_repository: UserRepository) -> None:
        self.session = session
        self.user_repository = user_repository

    async def register(self, payload: UserRegisterRequest) -> AuthTokenResponse:
        existing_user = await self.user_repository.get_by_email(payload.email)
        if existing_user is not None:
            raise AppException(
                "A user with this email already exists.",
                status_code=409,
                error_code="email_already_registered",
            )

        user = await self.user_repository.create_user(
            email=payload.email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        tokens = await self._issue_token_pair(user)
        await self.session.commit()
        return tokens

    async def login(self, payload: UserLoginRequest) -> AuthTokenResponse:
        user = await self.user_repository.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise AppException(
                "Invalid email or password.",
                status_code=401,
                error_code="invalid_credentials",
            )

        if not user.is_active:
            raise AppException(
                "User account is inactive.",
                status_code=403,
                error_code="inactive_user",
            )

        tokens = await self._issue_token_pair(user)
        await self.session.commit()
        return tokens

    async def refresh(self, refresh_token: str) -> AuthTokenResponse:
        token_hash = hash_refresh_token(refresh_token)
        stored_token = await self.user_repository.get_refresh_token(token_hash)
        now = datetime.now(UTC)

        if (
            stored_token is None
            or not stored_token.is_active
            or stored_token.revoked_at is not None
            or stored_token.expires_at <= now
        ):
            raise AppException(
                "Invalid refresh token.",
                status_code=401,
                error_code="invalid_refresh_token",
            )

        user = stored_token.user
        if user is None or not user.is_active:
            raise AppException(
                "User account is inactive.",
                status_code=403,
                error_code="inactive_user",
            )

        new_refresh_token = create_refresh_token()
        new_refresh_token_hash = hash_refresh_token(new_refresh_token)
        await self.user_repository.revoke_refresh_token(
            stored_token,
            revoked_at=now,
            replaced_by_token_hash=new_refresh_token_hash,
        )
        await self.user_repository.create_refresh_token(
            user_id=user.id,
            token_hash=new_refresh_token_hash,
            expires_at=refresh_token_expires_at(),
        )
        await self.session.commit()

        return AuthTokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=new_refresh_token,
            user=UserPublicResponse.model_validate(user),
        )

    async def logout(self, refresh_token: str) -> None:
        token_hash = hash_refresh_token(refresh_token)
        stored_token = await self.user_repository.get_refresh_token(token_hash)
        if stored_token is None:
            return

        await self.user_repository.revoke_refresh_token(stored_token, revoked_at=datetime.now(UTC))
        await self.session.commit()

    async def get_user(self, user_id: UUID) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AppException(
                "Authenticated user was not found.",
                status_code=401,
                error_code="user_not_found",
            )
        return user

    async def user_has_permission(self, user_id: UUID, permission: str) -> bool:
        permissions = await self.user_repository.get_user_permissions(user_id)
        return permission in permissions

    async def _issue_token_pair(self, user: User) -> AuthTokenResponse:
        refresh_token = create_refresh_token()
        await self.user_repository.create_refresh_token(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_token_expires_at(),
        )
        return AuthTokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=refresh_token,
            user=UserPublicResponse.model_validate(user),
        )
