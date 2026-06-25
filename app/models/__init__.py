"""SQLAlchemy models.

Importing models here makes Alembic autogenerate see every table through
`Base.metadata`.
"""

from app.models.permission import Permission
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole

__all__ = [
    "Permission",
    "RefreshToken",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
]
