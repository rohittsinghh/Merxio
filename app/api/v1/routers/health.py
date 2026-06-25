from typing import Annotated

from fastapi import APIRouter, Depends

from app.database.session import DatabaseHealth, check_database_health
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    database: Annotated[DatabaseHealth, Depends(check_database_health)],
) -> HealthCheckResponse:
    """Expose a lightweight health endpoint for load balancers and humans."""
    return HealthCheckResponse(status="ok", database=database.status)
