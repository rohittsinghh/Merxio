from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole


class UserRepository:
    """Database queries for users, roles, permissions, and refresh tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> User:
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def create_refresh_token(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(refresh_token)
        await self.session.flush()
        return refresh_token

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        statement = (
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(RefreshToken.token_hash == token_hash)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def revoke_refresh_token(
        self,
        refresh_token: RefreshToken,
        *,
        revoked_at,
        replaced_by_token_hash: str | None = None,
    ) -> None:
        refresh_token.is_active = False
        refresh_token.revoked_at = revoked_at
        refresh_token.replaced_by_token_hash = replaced_by_token_hash
        await self.session.flush()

    async def get_user_permissions(self, user_id: UUID) -> set[str]:
        statement = (
            select(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
        )
        result = await self.session.execute(statement)
        return set(result.scalars().all())
