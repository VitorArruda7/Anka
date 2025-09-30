from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate

router = APIRouter()


@router.get("/", response_model=list[ClientRead])
async def list_clients(
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Client]:
    stmt = select(Client)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Client.name.ilike(pattern), Client.email.ilike(pattern)))
    if is_active is not None:
        stmt = stmt.where(Client.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


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
    return None
