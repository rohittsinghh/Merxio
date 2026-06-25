from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_user
from app.dependencies.catalog import get_catalog_service
from app.models.user import User
from app.schemas.category import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest
from app.schemas.product import (
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from app.services.catalog import CatalogService

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    active_only: bool = True,
) -> list[CategoryResponse]:
    """List categories for catalog navigation."""

    categories = await catalog_service.list_categories(active_only=active_only)
    return [CategoryResponse.model_validate(category) for category in categories]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    payload: CategoryCreateRequest,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategoryResponse:
    """Create a category.

    We require authentication now; later this should be guarded by an admin RBAC
    permission once seed roles and permissions exist.
    """

    _ = current_user
    category = await catalog_service.create_category(payload)
    return CategoryResponse.model_validate(category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    payload: CategoryUpdateRequest,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategoryResponse:
    """Update a category."""

    _ = current_user
    category = await catalog_service.update_category(category_id=category_id, payload=payload)
    return CategoryResponse.model_validate(category)


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    search: str | None = Query(default=None, min_length=1, max_length=120),
    category_id: UUID | None = None,
    seller_id: UUID | None = None,
    active_only: bool = True,
    sort: Literal["newest", "price_asc", "price_desc", "name"] = "newest",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ProductListResponse:
    """Search, filter, sort, and paginate products."""

    products, total = await catalog_service.list_products(
        search=search,
        category_id=category_id,
        seller_id=seller_id,
        active_only=active_only,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return ProductListResponse(
        items=[ProductResponse.model_validate(product) for product in products],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductResponse:
    """Return one product by id."""

    product = await catalog_service.get_product(product_id)
    return ProductResponse.model_validate(product)


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    payload: ProductCreateRequest,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductResponse:
    """Create a product owned by the authenticated user."""

    product = await catalog_service.create_product(seller=current_user, payload=payload)
    return ProductResponse.model_validate(product)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    payload: ProductUpdateRequest,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ProductResponse:
    """Update a product owned by the authenticated user."""

    product = await catalog_service.update_product(
        seller=current_user,
        product_id=product_id,
        payload=payload,
    )
    return ProductResponse.model_validate(product)
