from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def _ensure_serializable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


async def log_audit_event(
    session: AsyncSession,
    *,
    user_id: int | None,
    action: str,
    entity: str,
    entity_id: int | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    payload = metadata or {}
    safe_metadata = {key: _ensure_serializable(value) for key, value in payload.items()}

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id is not None else None,
        data=safe_metadata or None,
    )
    try:
        session.add(log_entry)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to enqueue audit log for %s:%s (%s)", entity, entity_id, exc)
