from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.database.session import get_db_session
from app.models.user import User
from app.repositories.users import UserRepository
from app.security.tokens import decode_access_token
from app.services.auth import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_auth_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthService:
    """Build the auth service with its repository dependency."""

    return AuthService(session=session, user_repository=UserRepository(session))


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """Resolve the authenticated user from a bearer access token."""

    if credentials is None:
        raise AppException(
            "Authentication is required.",
            status_code=401,
            error_code="not_authenticated",
        )

    user_id = decode_access_token(credentials.credentials)
    return await auth_service.get_user(user_id)


def require_permission(permission: str):
    """Create a dependency that enforces one named RBAC permission."""

    async def permission_dependency(
        current_user: Annotated[User, Depends(get_current_user)],
        auth_service: Annotated[AuthService, Depends(get_auth_service)],
    ) -> User:
        has_permission = await auth_service.user_has_permission(current_user.id, permission)
        if not has_permission:
            raise AppException(
                "Permission denied.",
                status_code=403,
                error_code="permission_denied",
            )
        return current_user

    return permission_dependency
