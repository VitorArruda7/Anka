from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, JSON, Text
from typing import Optional
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


AUDIT_DATA_TYPE = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    entity: Mapped[str] = mapped_column(String(128))
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    data: Mapped[dict[str, object] | None] = mapped_column("metadata", AUDIT_DATA_TYPE, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")
