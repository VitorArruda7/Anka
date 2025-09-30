from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.allocation import Allocation
from app.models.user import User
from app.schemas.allocation import AllocationCreate, AllocationRead

router = APIRouter()


@router.get("/", response_model=list[AllocationRead])
async def list_allocations(
    client_id: int | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Allocation]:
    stmt = select(Allocation)
    if client_id is not None:
        stmt = stmt.where(Allocation.client_id == client_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("/", response_model=AllocationRead, status_code=status.HTTP_201_CREATED)
async def create_allocation(
    allocation_in: AllocationCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Allocation:
    allocation = Allocation(**allocation_in.model_dump())
    session.add(allocation)
    await session.commit()
    await session.refresh(allocation)
    return allocation


@router.delete("/{allocation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allocation(
    allocation_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> None:
    allocation = await session.get(Allocation, allocation_id)
    if not allocation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allocation not found")
    await session.delete(allocation)
    await session.commit()
    return None
