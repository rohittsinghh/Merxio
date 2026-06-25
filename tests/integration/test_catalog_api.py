from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.dependencies.catalog import get_catalog_service
from app.main import create_app
from app.models.category import Category
from app.models.product import Product
from app.models.user import User


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


class FakeCatalogService:
    def __init__(self) -> None:
        self.user = make_user()
        self.category = Category(
            id=uuid4(),
            parent_id=None,
            name="Books",
            slug="books",
            description=None,
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.product = Product(
            id=uuid4(),
            category_id=self.category.id,
            seller_id=self.user.id,
            name="Clean Architecture",
            slug="clean-architecture",
            sku="BOOK-001",
            description="A backend engineering book.",
            price=Decimal("49.99"),
            compare_at_price=None,
            currency="USD",
            is_active=True,
            images=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def list_categories(self, *, active_only: bool):
        return [self.category]

    async def create_category(self, payload):
        return self.category

    async def update_category(self, *, category_id, payload):
        return self.category

    async def list_products(self, **kwargs):
        return [self.product], 1

    async def get_product(self, product_id):
        return self.product

    async def create_product(self, *, seller, payload):
        return self.product

    async def update_product(self, *, seller, product_id, payload):
        return self.product


def build_client() -> TestClient:
    app = create_app()
    current_user = make_user()
    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_catalog_service] = lambda: FakeCatalogService()
    return TestClient(app)


def test_list_categories_returns_catalog_categories() -> None:
    """Category list is a public catalog read endpoint."""

    client = build_client()

    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "books"


def test_create_category_returns_created_category() -> None:
    """Category creation should expose the category response contract."""

    client = build_client()

    response = client.post("/api/v1/categories", json={"name": "Books", "slug": "books"})

    assert response.status_code == 201
    assert response.json()["name"] == "Books"


def test_list_products_returns_paginated_catalog() -> None:
    """Product listing should include pagination metadata."""

    client = build_client()

    response = client.get("/api/v1/products?search=Clean&sort=name&limit=10&offset=0")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["sku"] == "BOOK-001"


def test_create_product_returns_created_product() -> None:
    """Product creation should attach ownership through the current user."""

    client = build_client()
    category_id = str(uuid4())

    response = client.post(
        "/api/v1/products",
        json={
            "category_id": category_id,
            "name": "Clean Architecture",
            "slug": "clean-architecture",
            "sku": "BOOK-001",
            "description": "A backend engineering book.",
            "price": "49.99",
            "images": [],
        },
    )

    assert response.status_code == 201
    assert response.json()["slug"] == "clean-architecture"
