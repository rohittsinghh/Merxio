from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_user
from app.dependencies.user import get_user_service
from app.models.user import User
from app.schemas.address import AddressCreateRequest, AddressResponse, AddressUpdateRequest
from app.schemas.user import UserProfileResponse, UserUpdateRequest
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    payload: UserUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserProfileResponse:
    """Update the authenticated user's profile."""

    user = await user_service.update_profile(current_user, payload)
    return UserProfileResponse.model_validate(user)


@router.get("/me/addresses", response_model=list[AddressResponse])
async def list_addresses(
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> list[AddressResponse]:
    """List addresses owned by the authenticated user."""

    addresses = await user_service.list_addresses(current_user)
    return [AddressResponse.model_validate(address) for address in addresses]


@router.post(
    "/me/addresses",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_address(
    payload: AddressCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> AddressResponse:
    """Create an address for the authenticated user."""

    address = await user_service.create_address(current_user, payload)
    return AddressResponse.model_validate(address)


@router.put("/me/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: UUID,
    payload: AddressUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> AddressResponse:
    """Replace an address owned by the authenticated user."""

    address = await user_service.update_address(
        user=current_user,
        address_id=address_id,
        payload=payload,
    )
    return AddressResponse.model_validate(address)


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> None:
    """Delete an address owned by the authenticated user."""

    await user_service.delete_address(user=current_user, address_id=address_id)
