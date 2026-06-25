from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.address import Address
from app.models.user import User
from app.repositories.address import AddressRepository
from app.repositories.user import UserProfileRepository
from app.schemas.address import AddressCreateRequest, AddressUpdateRequest
from app.schemas.user import UserUpdateRequest


class UserService:
    """Business logic for user profile and address management."""

    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserProfileRepository,
        address_repository: AddressRepository,
    ) -> None:
        self.session = session
        self.user_repository = user_repository
        self.address_repository = address_repository

    async def update_profile(self, user: User, payload: UserUpdateRequest) -> User:
        updated_user = await self.user_repository.update_profile(
            user,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        await self.session.commit()
        return updated_user

    async def list_addresses(self, user: User) -> list[Address]:
        return await self.address_repository.list_for_user(user.id)

    async def create_address(self, user: User, payload: AddressCreateRequest) -> Address:
        values = payload.model_dump()
        if payload.is_default:
            await self.address_repository.unset_default_for_type(
                user_id=user.id,
                address_type=payload.address_type,
            )

        address = await self.address_repository.create(user_id=user.id, values=values)
        await self.session.commit()
        return address

    async def update_address(
        self,
        *,
        user: User,
        address_id: UUID,
        payload: AddressUpdateRequest,
    ) -> Address:
        address = await self._get_owned_address(user=user, address_id=address_id)
        values = payload.model_dump()

        if payload.is_default:
            await self.address_repository.unset_default_for_type(
                user_id=user.id,
                address_type=payload.address_type,
            )

        updated_address = await self.address_repository.update(address, values)
        await self.session.commit()
        return updated_address

    async def delete_address(self, *, user: User, address_id: UUID) -> None:
        address = await self._get_owned_address(user=user, address_id=address_id)
        await self.address_repository.delete(address)
        await self.session.commit()

    async def _get_owned_address(self, *, user: User, address_id: UUID) -> Address:
        address = await self.address_repository.get_for_user(address_id=address_id, user_id=user.id)
        if address is None:
            raise AppException(
                "Address was not found.",
                status_code=404,
                error_code="address_not_found",
            )
        return address
