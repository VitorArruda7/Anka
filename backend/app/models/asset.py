from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    exchange: Mapped[str] = mapped_column(String(128))
    currency: Mapped[str] = mapped_column(String(8))

    allocations: Mapped[list[Allocation]] = relationship(back_populates="asset", cascade="all, delete-orphan")
