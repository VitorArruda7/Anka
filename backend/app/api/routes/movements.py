from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.movement import Movement, MovementType
from app.models.user import User
from app.services.audit import log_audit_event
from app.services.dashboard_metrics import invalidate_dashboard_metrics
from app.utils.pagination import paginate
from app.schemas.movement import MovementCreate, MovementRead
from app.schemas.pagination import Paginated

router = APIRouter()


@router.get("/", response_model=Paginated[MovementRead])
async def list_movements(
    client_id: int | None = Query(default=None, ge=1),
    movement_type: MovementType | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Paginated[MovementRead]:
    stmt = select(Movement)
    conditions = []
    if client_id is not None:
        conditions.append(Movement.client_id == client_id)
    if movement_type is not None:
        conditions.append(Movement.type == movement_type)
    if start_date is not None:
        conditions.append(Movement.date >= start_date)
    if end_date is not None:
        conditions.append(Movement.date <= end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(Movement.date.desc(), Movement.id.desc())
    return await paginate(session, stmt, page=page, page_size=page_size)


@router.post("/", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
async def create_movement(
    movement_in: MovementCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Movement:
    movement = Movement(**movement_in.model_dump())
    session.add(movement)
    await session.flush()
    await log_audit_event(
        session,
        user_id=current_user.id,
        action="movement.created",
        entity="movement",
        entity_id=movement.id,
        metadata={
            "client_id": movement.client_id,
            "type": movement.type.value,
        },
    )
    await session.commit()
    await session.refresh(movement)
    await invalidate_dashboard_metrics()
    return movement


@router.delete("/{movement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movement(
    movement_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    movement = await session.get(Movement, movement_id)
    if movement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movement not found")
    await log_audit_event(
        session,
        user_id=current_user.id,
        action="movement.deleted",
        entity="movement",
        entity_id=movement.id,
        metadata={
            "client_id": movement.client_id,
            "type": movement.type.value,
        },
    )
    await session.delete(movement)
    await session.commit()
    await invalidate_dashboard_metrics()
    return None
