from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.dependencies.auth import require_permission
from app.models.user import User


class PermissionDenyingAuthService:
    async def user_has_permission(self, user_id, permission: str) -> bool:
        return False


@pytest.mark.asyncio
async def test_rbac_dependency_rejects_missing_permission() -> None:
    """Users without the required permission should receive a 403 error."""

    current_user = User(
        id=uuid4(),
        email="ada@example.com",
        password_hash="not-used",
        first_name="Ada",
        last_name="Lovelace",
        is_active=True,
        is_verified=False,
        created_at=datetime.now(UTC),
    )
    dependency = require_permission("orders:read")

    with pytest.raises(AppException) as exc_info:
        await dependency(
            current_user=current_user,
            auth_service=PermissionDenyingAuthService(),
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.error_code == "permission_denied"
