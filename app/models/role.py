from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.role_permission import RolePermission
    from app.models.user_role import UserRole


class Role(Base):
    """Named authorization role such as customer, seller, or admin."""

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("name", name="uq_roles_name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    users: Mapped[list[UserRole]] = relationship(back_populates="role")
    permissions: Mapped[list[RolePermission]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )
