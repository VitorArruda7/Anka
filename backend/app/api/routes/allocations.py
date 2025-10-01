from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.allocation import Allocation
from app.models.user import User
from app.services.dashboard_metrics import invalidate_dashboard_metrics
from app.utils.pagination import paginate
from app.schemas.allocation import AllocationCreate, AllocationRead
from app.schemas.pagination import Paginated

router = APIRouter()


@router.get("/", response_model=Paginated[AllocationRead])
async def list_allocations(
    client_id: int | None = Query(default=None, ge=1),
    asset_id: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Paginated[AllocationRead]:
    stmt = select(Allocation)
    if client_id is not None:
        stmt = stmt.where(Allocation.client_id == client_id)
    if asset_id is not None:
        stmt = stmt.where(Allocation.asset_id == asset_id)
    stmt = stmt.order_by(Allocation.buy_date.desc(), Allocation.id.desc())
    return await paginate(session, stmt, page=page, page_size=page_size)


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
    await invalidate_dashboard_metrics()
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
    await invalidate_dashboard_metrics()
    return None
