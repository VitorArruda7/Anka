from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"))
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"))
    quantity: Mapped[float] = mapped_column(Numeric(18, 4))
    buy_price: Mapped[float] = mapped_column(Numeric(18, 4))
    buy_date: Mapped[date] = mapped_column(Date)

    client: Mapped["Client"] = relationship(back_populates="allocations")
    asset: Mapped["Asset"] = relationship(back_populates="allocations")
