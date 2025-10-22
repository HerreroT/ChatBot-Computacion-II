"""add booking tables

Revision ID: 0002
Revises: 0001
Create Date: 2024-09-05 12:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("phone_number", name="uq_customers_phone_number"),
    )
    op.create_index("ix_customers_phone_number", "customers", ["phone_number"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service", sa.String(length=100), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw_message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("starts_at", name="uq_booking_starts_at"),
    )
    op.create_index("ix_bookings_starts_at", "bookings", ["starts_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_bookings_starts_at", table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("ix_customers_phone_number", table_name="customers")
    op.drop_table("customers")
