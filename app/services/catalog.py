from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest
from app.schemas.product import ProductCreateRequest, ProductUpdateRequest


class CatalogService:
    """Business logic for categories and products."""

    def __init__(
        self,
        session: AsyncSession,
        category_repository: CategoryRepository,
        product_repository: ProductRepository,
    ) -> None:
        self.session = session
        self.category_repository = category_repository
        self.product_repository = product_repository

    async def list_categories(self, *, active_only: bool) -> list[Category]:
        return await self.category_repository.list(active_only=active_only)

    async def create_category(self, payload: CategoryCreateRequest) -> Category:
        await self._validate_category(payload)
        category = await self.category_repository.create(payload.model_dump())
        await self.session.commit()
        return category

    async def update_category(
        self,
        *,
        category_id: UUID,
        payload: CategoryUpdateRequest,
    ) -> Category:
        category = await self.category_repository.get_by_id(category_id)
        if category is None:
            raise AppException(
                "Category was not found.",
                status_code=404,
                error_code="category_not_found",
            )

        await self._validate_category(payload, existing_category_id=category_id)
        updated_category = await self.category_repository.update(category, payload.model_dump())
        await self.session.commit()
        return updated_category

    async def list_products(
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
        return await self.product_repository.list(
            search=search,
            category_id=category_id,
            seller_id=seller_id,
            active_only=active_only,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    async def get_product(self, product_id: UUID) -> Product:
        product = await self.product_repository.get_by_id(product_id)
        if product is None:
            raise AppException(
                "Product was not found.",
                status_code=404,
                error_code="product_not_found",
            )
        return product

    async def create_product(self, *, seller: User, payload: ProductCreateRequest) -> Product:
        await self._validate_product(payload)
        values = payload.model_dump(exclude={"images"})
        values["seller_id"] = seller.id
        images = [image.model_dump(mode="json") for image in payload.images]
        product = await self.product_repository.create(values=values, images=images)
        await self.session.commit()
        return product

    async def update_product(
        self,
        *,
        seller: User,
        product_id: UUID,
        payload: ProductUpdateRequest,
    ) -> Product:
        product = await self.product_repository.get_for_seller(
            product_id=product_id,
            seller_id=seller.id,
        )
        if product is None:
            raise AppException(
                "Product was not found.",
                status_code=404,
                error_code="product_not_found",
            )

        await self._validate_product(payload, existing_product_id=product_id)
        values = payload.model_dump(exclude={"images"})
        images = [image.model_dump(mode="json") for image in payload.images]
        updated_product = await self.product_repository.update(
            product,
            values=values,
            images=images,
        )
        await self.session.commit()
        return updated_product

    async def _validate_category(
        self,
        payload: CategoryCreateRequest | CategoryUpdateRequest,
        *,
        existing_category_id: UUID | None = None,
    ) -> None:
        if payload.parent_id is not None:
            parent = await self.category_repository.get_by_id(payload.parent_id)
            if parent is None:
                raise AppException(
                    "Parent category was not found.",
                    status_code=404,
                    error_code="parent_category_not_found",
                )
            if parent.id == existing_category_id:
                raise AppException(
                    "Category cannot be its own parent.",
                    status_code=400,
                    error_code="invalid_parent_category",
                )

        if await self.category_repository.slug_exists(
            slug=payload.slug,
            exclude_id=existing_category_id,
        ):
            raise AppException(
                "Category slug already exists.",
                status_code=409,
                error_code="category_slug_exists",
            )

    async def _validate_product(
        self,
        payload: ProductCreateRequest | ProductUpdateRequest,
        *,
        existing_product_id: UUID | None = None,
    ) -> None:
        category = await self.category_repository.get_by_id(payload.category_id)
        if category is None or not category.is_active:
            raise AppException(
                "Category was not found.",
                status_code=404,
                error_code="category_not_found",
            )

        if await self.product_repository.slug_exists(
            slug=payload.slug,
            exclude_id=existing_product_id,
        ):
            raise AppException(
                "Product slug already exists.",
                status_code=409,
                error_code="product_slug_exists",
            )

        if await self.product_repository.sku_exists(
            sku=payload.sku,
            exclude_id=existing_product_id,
        ):
            raise AppException(
                "Product SKU already exists.",
                status_code=409,
                error_code="product_sku_exists",
            )
