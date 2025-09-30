"""initial tables"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20230930_01"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_clients_email"), "clients", ["email"], unique=True)
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)
    op.create_index(op.f("ix_clients_name"), "clients", ["name"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ticker", sa.String(length=32), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("exchange", sa.String(length=128), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
    )
    op.create_index(op.f("ix_assets_id"), "assets", ["id"], unique=False)
    op.create_index(op.f("ix_assets_ticker"), "assets", ["ticker"], unique=True)

    op.create_table(
        "allocations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("buy_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("buy_date", sa.Date, nullable=False),
    )
    op.create_index(op.f("ix_allocations_id"), "allocations", ["id"], unique=False)

    op.create_table(
        "movements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("client_id", sa.Integer, sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("deposit", "withdrawal", name="movement_type"), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("note", sa.String(length=512), nullable=True),
    )
    op.create_index(op.f("ix_movements_id"), "movements", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_movements_id"), table_name="movements")
    op.drop_table("movements")
    op.drop_table("allocations")
    op.drop_index(op.f("ix_assets_ticker"), table_name="assets")
    op.drop_index(op.f("ix_assets_id"), table_name="assets")
    op.drop_table("assets")
    op.drop_index(op.f("ix_clients_name"), table_name="clients")
    op.drop_index(op.f("ix_clients_id"), table_name="clients")
    op.drop_index(op.f("ix_clients_email"), table_name="clients")
    op.drop_table("clients")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS movement_type")
