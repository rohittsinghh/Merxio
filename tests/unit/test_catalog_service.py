from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.models.category import Category
from app.models.product import Product
from app.models.user import User
from app.schemas.category import CategoryCreateRequest
from app.schemas.product import ProductCreateRequest, ProductUpdateRequest
from app.services.catalog import CatalogService


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1


class FakeCategoryRepository:
    def __init__(self) -> None:
        self.categories: dict[object, Category] = {}

    async def list(self, *, active_only: bool = False):
        categories = list(self.categories.values())
        if active_only:
            categories = [category for category in categories if category.is_active]
        return categories

    async def get_by_id(self, category_id):
        return self.categories.get(category_id)

    async def get_by_slug(self, slug: str):
        return next(
            (category for category in self.categories.values() if category.slug == slug),
            None,
        )

    async def create(self, values: dict):
        category = Category(
            id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            **values,
        )
        self.categories[category.id] = category
        return category

    async def update(self, category: Category, values: dict):
        for field, value in values.items():
            setattr(category, field, value)
        return category

    async def slug_exists(self, *, slug: str, exclude_id=None):
        return any(
            category.slug == slug and category.id != exclude_id
            for category in self.categories.values()
        )


class FakeProductRepository:
    def __init__(self) -> None:
        self.products: dict[object, Product] = {}

    async def list(self, **kwargs):
        return list(self.products.values()), len(self.products)

    async def get_by_id(self, product_id):
        return self.products.get(product_id)

    async def get_for_seller(self, *, product_id, seller_id):
        product = self.products.get(product_id)
        if product is None or product.seller_id != seller_id:
            return None
        return product

    async def create(self, *, values: dict, images: list[dict]):
        product = Product(
            id=uuid4(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            images=[],
            **values,
        )
        self.products[product.id] = product
        return product

    async def update(self, product: Product, *, values: dict, images: list[dict]):
        for field, value in values.items():
            setattr(product, field, value)
        return product

    async def slug_exists(self, *, slug: str, exclude_id=None):
        return any(
            product.slug == slug and product.id != exclude_id for product in self.products.values()
        )

    async def sku_exists(self, *, sku: str, exclude_id=None):
        return any(
            product.sku == sku and product.id != exclude_id
            for product in self.products.values()
        )


def make_user() -> User:
    return User(
        id=uuid4(),
        email="seller@example.com",
        password_hash="not-used",
        first_name="Seller",
        last_name="User",
        is_active=True,
        is_verified=False,
        created_at=datetime.now(UTC),
    )


def build_service() -> tuple[
    CatalogService,
    FakeCategoryRepository,
    FakeProductRepository,
    FakeSession,
]:
    session = FakeSession()
    category_repository = FakeCategoryRepository()
    product_repository = FakeProductRepository()
    service = CatalogService(
        session=session,
        category_repository=category_repository,
        product_repository=product_repository,
    )
    return service, category_repository, product_repository, session


@pytest.mark.asyncio
async def test_create_category_rejects_duplicate_slug() -> None:
    """Category slugs are public identifiers and must be unique."""

    service, _, _, _ = build_service()
    payload = CategoryCreateRequest(name="Books", slug="books")

    await service.create_category(payload)

    with pytest.raises(AppException) as exc_info:
        await service.create_category(payload)

    assert exc_info.value.error_code == "category_slug_exists"


@pytest.mark.asyncio
async def test_create_product_requires_active_category() -> None:
    """Products should not be created under missing or inactive categories."""

    service, _, _, _ = build_service()

    with pytest.raises(AppException) as exc_info:
        await service.create_product(
            seller=make_user(),
            payload=ProductCreateRequest(
                category_id=uuid4(),
                name="Clean Architecture",
                slug="clean-architecture",
                sku="BOOK-001",
                description="A backend engineering book.",
                price=Decimal("49.99"),
            ),
        )

    assert exc_info.value.error_code == "category_not_found"


@pytest.mark.asyncio
async def test_create_product_assigns_authenticated_user_as_seller() -> None:
    """Seller ownership should come from the access token, not the request body."""

    service, category_repository, _, session = build_service()
    seller = make_user()
    category = await category_repository.create(
        {
            "name": "Books",
            "slug": "books",
            "description": None,
            "parent_id": None,
            "is_active": True,
        }
    )

    product = await service.create_product(
        seller=seller,
        payload=ProductCreateRequest(
            category_id=category.id,
            name="Clean Architecture",
            slug="clean-architecture",
            sku="BOOK-001",
            description="A backend engineering book.",
            price=Decimal("49.99"),
        ),
    )

    assert product.seller_id == seller.id
    assert session.commits == 1


@pytest.mark.asyncio
async def test_update_product_rejects_non_owner() -> None:
    """A seller should not be able to update another seller's product."""

    service, category_repository, product_repository, _ = build_service()
    owner = make_user()
    other_seller = make_user()
    category = await category_repository.create(
        {
            "name": "Books",
            "slug": "books",
            "description": None,
            "parent_id": None,
            "is_active": True,
        }
    )
    product = await product_repository.create(
        values={
            "category_id": category.id,
            "seller_id": owner.id,
            "name": "Clean Architecture",
            "slug": "clean-architecture",
            "sku": "BOOK-001",
            "description": "A backend engineering book.",
            "price": Decimal("49.99"),
            "compare_at_price": None,
            "currency": "USD",
            "is_active": True,
        },
        images=[],
    )

    with pytest.raises(AppException) as exc_info:
        await service.update_product(
            seller=other_seller,
            product_id=product.id,
            payload=ProductUpdateRequest(
                category_id=category.id,
                name="Updated Book",
                slug="updated-book",
                sku="BOOK-002",
                description="Updated description.",
                price=Decimal("59.99"),
            ),
        )

    assert exc_info.value.error_code == "product_not_found"
