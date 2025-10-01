from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogUser(BaseModel):
    id: int
    name: str | None
    email: str | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuditLogRead(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity: str
    entity_id: str | None
    metadata: dict[str, Any] | None = Field(default=None, alias="data")
    created_at: datetime
    user: AuditLogUser | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
