from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address


class AddressRepository:
    """Database queries for user addresses."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[Address]:
        statement = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_for_user(self, *, address_id: UUID, user_id: UUID) -> Address | None:
        statement = select(Address).where(Address.id == address_id, Address.user_id == user_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, *, user_id: UUID, values: dict) -> Address:
        address = Address(user_id=user_id, **values)
        self.session.add(address)
        await self.session.flush()
        await self.session.refresh(address)
        return address

    async def update(self, address: Address, values: dict) -> Address:
        for field, value in values.items():
            setattr(address, field, value)
        await self.session.flush()
        await self.session.refresh(address)
        return address

    async def delete(self, address: Address) -> None:
        await self.session.delete(address)
        await self.session.flush()

    async def unset_default_for_type(self, *, user_id: UUID, address_type: str) -> None:
        statement = (
            update(Address)
            .where(Address.user_id == user_id, Address.address_type == address_type)
            .values(is_default=False)
        )
        await self.session.execute(statement)
