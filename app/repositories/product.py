from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.product_image import ProductImage


class ProductRepository:
    """Database queries for catalog products."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self,
        *,
        search: str | None,
        category_id: UUID | None,
        seller_id: UUID | None,
        active_only: bool,
        sort: str,
        limit: int,
        offset: int,
    ) -> tuple[list[Product], int]:
        statement = self._apply_filters(
            select(Product).options(selectinload(Product.images)),
            search=search,
            category_id=category_id,
            seller_id=seller_id,
            active_only=active_only,
        )
        count_statement = self._apply_filters(
            select(func.count()).select_from(Product),
            search=search,
            category_id=category_id,
            seller_id=seller_id,
            active_only=active_only,
        )

        statement = self._apply_sort(statement, sort).limit(limit).offset(offset)
        products = await self.session.execute(statement)
        total = await self.session.execute(count_statement)
        return list(products.scalars().all()), total.scalar_one()

    async def get_by_id(self, product_id: UUID) -> Product | None:
        statement = (
            select(Product)
            .options(selectinload(Product.images))
            .where(Product.id == product_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_for_seller(self, *, product_id: UUID, seller_id: UUID) -> Product | None:
        statement = (
            select(Product)
            .options(selectinload(Product.images))
            .where(Product.id == product_id, Product.seller_id == seller_id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, *, values: dict, images: list[dict]) -> Product:
        product = Product(**values)
        product.images = [ProductImage(**image) for image in images]
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product, attribute_names=["images"])
        return product

    async def update(self, product: Product, *, values: dict, images: list[dict]) -> Product:
        for field, value in values.items():
            setattr(product, field, value)
        product.images = [ProductImage(**image) for image in images]
        await self.session.flush()
        await self.session.refresh(product, attribute_names=["images"])
        return product

    async def slug_exists(self, *, slug: str, exclude_id: UUID | None = None) -> bool:
        return await self._value_exists(Product.slug == slug, exclude_id=exclude_id)

    async def sku_exists(self, *, sku: str, exclude_id: UUID | None = None) -> bool:
        return await self._value_exists(Product.sku == sku, exclude_id=exclude_id)

    async def _value_exists(self, condition, *, exclude_id: UUID | None = None) -> bool:
        statement = select(func.count()).select_from(Product).where(condition)
        if exclude_id is not None:
            statement = statement.where(Product.id != exclude_id)
        result = await self.session.execute(statement)
        return result.scalar_one() > 0

    def _apply_filters(
        self,
        statement: Select,
        *,
        search: str | None,
        category_id: UUID | None,
        seller_id: UUID | None,
        active_only: bool,
    ) -> Select:
        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                or_(Product.name.ilike(pattern), Product.description.ilike(pattern))
            )
        if category_id is not None:
            statement = statement.where(Product.category_id == category_id)
        if seller_id is not None:
            statement = statement.where(Product.seller_id == seller_id)
        if active_only:
            statement = statement.where(Product.is_active.is_(True))
        return statement

    def _apply_sort(self, statement: Select, sort: str) -> Select:
        sort_map = {
            "newest": Product.created_at.desc(),
            "price_asc": Product.price.asc(),
            "price_desc": Product.price.desc(),
            "name": Product.name.asc(),
        }
        return statement.order_by(sort_map.get(sort, Product.created_at.desc()))
