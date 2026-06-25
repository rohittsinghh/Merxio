"""SQLAlchemy models.

Importing models here makes Alembic autogenerate see every table through
`Base.metadata`.
"""

from app.models.address import Address
from app.models.category import Category
from app.models.permission import Permission
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from app.models.user_role import UserRole

__all__ = [
    "Permission",
    "Address",
    "Category",
    "Product",
    "ProductImage",
    "RefreshToken",
    "Role",
    "RolePermission",
    "User",
    "UserRole",
]
