import csv
import io
from typing import Iterable, Sequence

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.allocation import Allocation
from app.models.client import Client
from app.models.movement import Movement
from app.models.user import User

router = APIRouter()


def _query_to_dicts(rows: Sequence, columns: Iterable[str]) -> list[dict[str, str]]:
    data: list[dict[str, str]] = []
    for row in rows:
        values = {}
        for column in columns:
            value = getattr(row, column, "")
            values[column] = str(value) if value is not None else ""
        data.append(values)
    return data


def _list_to_csv(data: list[dict[str, str]]) -> StreamingResponse:
    buffer = io.StringIO()
    if not data:
        writer = csv.writer(buffer)
        writer.writerow([])
    else:
        writer = csv.DictWriter(buffer, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)
    buffer.seek(0)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv")


@router.get("/clients")
async def export_clients(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> StreamingResponse:
    result = await session.execute(select(Client))
    clients = list(result.scalars().all())
    data = _query_to_dicts(clients, ("id", "name", "email", "is_active", "created_at"))
    response = _list_to_csv(data)
    response.headers["Content-Disposition"] = "attachment; filename=clients.csv"
    return response


@router.get("/allocations")
async def export_allocations(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> StreamingResponse:
    result = await session.execute(select(Allocation))
    allocations = list(result.scalars().all())
    data = _query_to_dicts(
        allocations,
        ("id", "client_id", "asset_id", "quantity", "buy_price", "buy_date"),
    )
    response = _list_to_csv(data)
    response.headers["Content-Disposition"] = "attachment; filename=allocations.csv"
    return response


@router.get("/movements")
async def export_movements(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> StreamingResponse:
    result = await session.execute(select(Movement))
    movements = list(result.scalars().all())
    data = _query_to_dicts(
        movements,
        ("id", "client_id", "type", "amount", "date", "note"),
    )
    response = _list_to_csv(data)
    response.headers["Content-Disposition"] = "attachment; filename=movements.csv"
    return response
