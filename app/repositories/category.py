from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    """Database queries for categories."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, *, active_only: bool = False) -> list[Category]:
        statement = select(Category).order_by(Category.name)
        if active_only:
            statement = statement.where(Category.is_active.is_(True))
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_id(self, category_id: UUID) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, values: dict) -> Category:
        category = Category(**values)
        self.session.add(category)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def update(self, category: Category, values: dict) -> Category:
        for field, value in values.items():
            setattr(category, field, value)
        await self.session.flush()
        await self.session.refresh(category)
        return category

    async def slug_exists(self, *, slug: str, exclude_id: UUID | None = None) -> bool:
        statement: Select = select(func.count()).select_from(Category).where(Category.slug == slug)
        if exclude_id is not None:
            statement = statement.where(Category.id != exclude_id)
        result = await self.session.execute(statement)
        return result.scalar_one() > 0
