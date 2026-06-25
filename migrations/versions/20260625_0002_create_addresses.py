"""create addresses

Revision ID: 20260625_0002
Revises: 20260625_0001
Create Date: 2026-06-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260625_0002"
down_revision: str | None = "20260625_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "addresses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("address_type", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone_number", sa.String(length=30), nullable=False),
        sa.Column("line1", sa.String(length=255), nullable=False),
        sa.Column("line2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("postal_code", sa.String(length=30), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "address_type IN ('shipping', 'billing')",
            name="ck_addresses_address_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_addresses_user_type", "addresses", ["user_id", "address_type"])


def downgrade() -> None:
    op.drop_index("ix_addresses_user_type", table_name="addresses")
    op.drop_table("addresses")
