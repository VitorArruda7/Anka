from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.pagination import Paginated
from app.utils.pagination import paginate

router = APIRouter()


@router.get("/", response_model=Paginated[AuditLogRead])
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    action: str | None = Query(default=None),
    entity: str | None = Query(default=None),
    user_id: int | None = Query(default=None, ge=1),
    starts_at: datetime | None = Query(default=None),
    ends_at: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Paginated[AuditLogRead]:
    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    )
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if starts_at:
        stmt = stmt.where(AuditLog.created_at >= starts_at)
    if ends_at:
        stmt = stmt.where(AuditLog.created_at <= ends_at)

    return await paginate(session, stmt, page=page, page_size=page_size)
