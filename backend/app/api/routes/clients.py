from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.client import Client
from app.models.user import User
from app.services.dashboard_metrics import invalidate_dashboard_metrics
from app.utils.pagination import paginate
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.schemas.pagination import Paginated

router = APIRouter()


@router.get("/", response_model=Paginated[ClientRead])
async def list_clients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    search: str | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Paginated[ClientRead]:
    stmt = select(Client)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Client.name.ilike(pattern), Client.email.ilike(pattern)))
    if is_active is not None:
        stmt = stmt.where(Client.is_active == is_active)
    stmt = stmt.order_by(Client.created_at.desc())
    return await paginate(session, stmt, page=page, page_size=page_size)


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Client:
    client = await session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.post("/", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: ClientCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Client:
    client = Client(**client_in.model_dump())
    session.add(client)
    await session.commit()
    await session.refresh(client)
    await invalidate_dashboard_metrics()
    return client


@router.put("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: int,
    client_in: ClientUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Client:
    client = await session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    update_data = client_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    await session.commit()
    await session.refresh(client)
    await invalidate_dashboard_metrics()
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> None:
    client = await session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    await session.delete(client)
    await session.commit()
    await invalidate_dashboard_metrics()
    return None
