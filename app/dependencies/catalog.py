from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.services.catalog import CatalogService


async def get_catalog_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CatalogService:
    """Build the catalog service with category and product repositories."""

    return CatalogService(
        session=session,
        category_repository=CategoryRepository(session),
        product_repository=ProductRepository(session),
    )
