from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthTokenResponse,
    LogoutRequest,
    TokenRefreshRequest,
    UserLoginRequest,
    UserPublicResponse,
    UserRegisterRequest,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthTokenResponse:
    """Register a new user and return the first token pair."""

    return await auth_service.register(payload)


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    payload: UserLoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthTokenResponse:
    """Authenticate a user and return a new token pair."""

    return await auth_service.login(payload)


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_token(
    payload: TokenRefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthTokenResponse:
    """Rotate a refresh token and issue a new access token."""

    return await auth_service.refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> None:
    """Revoke a refresh token."""

    await auth_service.logout(payload.refresh_token)


@router.get("/me", response_model=UserPublicResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublicResponse:
    """Return the currently authenticated user."""

    return UserPublicResponse.model_validate(current_user)
