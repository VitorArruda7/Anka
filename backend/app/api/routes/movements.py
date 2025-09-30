from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.movement import Movement
from app.models.user import User
from app.schemas.movement import MovementCreate, MovementRead

router = APIRouter()


@router.get("/", response_model=list[MovementRead])
async def list_movements(
    client_id: int | None = None,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Movement]:
    stmt = select(Movement)
    conditions = []
    if client_id is not None:
        conditions.append(Movement.client_id == client_id)
    if start_date is not None:
        conditions.append(Movement.date >= start_date)
    if end_date is not None:
        conditions.append(Movement.date <= end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    result = await session.execute(stmt.order_by(Movement.date.desc()))
    return list(result.scalars().all())


@router.post("/", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
async def create_movement(
    movement_in: MovementCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Movement:
    movement = Movement(**movement_in.model_dump())
    session.add(movement)
    await session.commit()
    await session.refresh(movement)
    return movement


@router.delete("/{movement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movement(
    movement_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> None:
    movement = await session.get(Movement, movement_id)
    if movement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movement not found")
    await session.delete(movement)
    await session.commit()
    return None
