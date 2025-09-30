from __future__ import annotations

from datetime import date
from enum import Enum

from sqlalchemy import Date, Enum as SqlEnum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MovementType(str, Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"


class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
    type: Mapped[MovementType] = mapped_column(SqlEnum(MovementType, name="movement_type"))
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    date: Mapped[date] = mapped_column(Date)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)

    client: Mapped["Client"] = relationship(back_populates="movements")
