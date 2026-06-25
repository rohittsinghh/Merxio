from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserProfileRepository:
    """Database writes for user profile data."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def update_profile(self, user: User, *, first_name: str, last_name: str) -> User:
        user.first_name = first_name
        user.last_name = last_name
        await self.session.flush()
        await self.session.refresh(user)
        return user
