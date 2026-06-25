from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.repositories.address import AddressRepository
from app.repositories.user import UserProfileRepository
from app.services.user import UserService


async def get_user_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserService:
    """Build the user service with profile and address repositories."""

    return UserService(
        session=session,
        user_repository=UserProfileRepository(session),
        address_repository=AddressRepository(session),
    )
