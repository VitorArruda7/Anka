import csv
import io
from decimal import Decimal
from typing import Iterable, Sequence

import pandas as pd

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.allocation import Allocation
from app.models.asset import Asset
from app.models.client import Client
from app.models.movement import Movement, MovementType
from app.models.user import User
from app.services.dashboard_metrics import cache_dashboard_metrics, compute_dashboard_metrics

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


def _ensure_float(value: float | int | Decimal | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def _bool_label(value: bool) -> str:
    return "Sim" if value else "Nao"


@router.get("/dashboard/excel")
async def export_dashboard_excel(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> StreamingResponse:
    clients_result = await session.execute(select(Client))
    clients = list(clients_result.scalars().all())

    assets_result = await session.execute(select(Asset))
    assets = list(assets_result.scalars().all())

    allocations_result = await session.execute(select(Allocation))
    allocations = list(allocations_result.scalars().all())

    movements_result = await session.execute(select(Movement))
    movements = list(movements_result.scalars().all())

    client_map = {client.id: client for client in clients}
    asset_map = {asset.id: asset for asset in assets}

    metrics = compute_dashboard_metrics(clients, assets, allocations, movements)
    await cache_dashboard_metrics(metrics)

    allocation_rows: list[dict[str, object]] = []
    for allocation in allocations:
        quantity = _ensure_float(allocation.quantity)
        price = _ensure_float(allocation.buy_price)
        invested_value = round(quantity * price, 2)

        asset = asset_map.get(allocation.asset_id)
        client = client_map.get(allocation.client_id)

        allocation_rows.append(
            {
                "ID": allocation.id,
                "Cliente": client.name if client else str(allocation.client_id),
                "Ticker": asset.ticker if asset else str(allocation.asset_id),
                "Ativo": asset.name if asset else "",
                "Quantidade": round(quantity, 4),
                "Preco de compra": round(price, 4),
                "Valor investido": invested_value,
                "Data da compra": allocation.buy_date.isoformat(),
                "Moeda": asset.currency if asset else "",
            }
        )

    movement_rows: list[dict[str, object]] = []
    for movement in movements:
        amount = round(_ensure_float(movement.amount), 2)
        client = client_map.get(movement.client_id)
        movement_type = "Deposito" if movement.type == MovementType.deposit else "Retirada"

        movement_rows.append(
            {
                "ID": movement.id,
                "Cliente": client.name if client else str(movement.client_id),
                "Tipo": movement_type,
                "Valor": amount,
                "Data": movement.date.isoformat(),
                "Observacao": movement.note or "",
            }
        )

    allocation_totals_map = {
        entry["client_id"]: entry["total"] for entry in metrics["allocation_totals_by_client"]
    }

    clients_rows = []
    for client in clients:
        total_for_client = allocation_totals_map.get(client.id, 0.0)
        clients_rows.append(
            {
                "ID": client.id,
                "Nome": client.name,
                "Email": client.email,
                "Ativo": _bool_label(client.is_active),
                "Total investido": round(total_for_client, 2),
                "Criado em": client.created_at.isoformat(),
            }
        )

    custody_rows = [
        {"Mes": point["label"], "Valor acumulado": round(point["value"], 2)}
        for point in metrics["custody_series"]
    ]

    flow_rows = [
        {
            "Mes": point["label"],
            "Entradas": round(point["inflow"], 2),
            "Saidas": round(point["outflow"], 2),
            "Saldo liquido": round(point["net"], 2),
        }
        for point in metrics["flow_series"]
    ]

    allocation_mix_rows = [
        {
            "Ativo": entry["label"],
            "Valor investido": round(entry["value"], 2),
            "Participacao (%)": round(entry["share"], 2),
        }
        for entry in metrics["allocation_mix"]
    ]

    kpi_rows = [
        {
            "Indicador": entry["indicator"],
            "Valor": entry["value"],
            "Variacao (%)": round(entry["variation"], 2),
        }
        for entry in metrics["kpis"]
    ]

    movement_totals = metrics["movement_totals"]
    movement_summary_df = pd.DataFrame(
        [
            {
                "Entradas": round(movement_totals["deposits"], 2),
                "Saidas": round(movement_totals["withdrawals"], 2),
                "Saldo liquido": round(movement_totals["net"], 2),
            }
        ]
    )

    custody_df = pd.DataFrame(custody_rows)
    if custody_df.empty:
        custody_df = pd.DataFrame(columns=["Mes", "Valor acumulado"])

    flow_df = pd.DataFrame(flow_rows)
    if flow_df.empty:
        flow_df = pd.DataFrame(columns=["Mes", "Entradas", "Saidas", "Saldo liquido"])

    allocation_mix_df = pd.DataFrame(allocation_mix_rows)
    if allocation_mix_df.empty:
        allocation_mix_df = pd.DataFrame(columns=["Ativo", "Valor investido", "Participacao (%)"])

    clients_df = pd.DataFrame(clients_rows)
    if clients_df.empty:
        clients_df = pd.DataFrame(columns=["ID", "Nome", "Email", "Ativo", "Total investido", "Criado em"])

    allocations_df = pd.DataFrame(allocation_rows)
    if allocations_df.empty:
        allocations_df = pd.DataFrame(
            columns=[
                "ID",
                "Cliente",
                "Ticker",
                "Ativo",
                "Quantidade",
                "Preco de compra",
                "Valor investido",
                "Data da compra",
                "Moeda",
            ]
        )

    movements_df = pd.DataFrame(movement_rows)
    if movements_df.empty:
        movements_df = pd.DataFrame(columns=["ID", "Cliente", "Tipo", "Valor", "Data", "Observacao"])

    kpi_df = pd.DataFrame(kpi_rows)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        kpi_df.to_excel(writer, sheet_name="KPIs", index=False)
        movement_summary_df.to_excel(writer, sheet_name="Resumo Mov.", index=False)
        custody_df.to_excel(writer, sheet_name="Custodia", index=False)
        flow_df.to_excel(writer, sheet_name="Fluxo", index=False)
        allocation_mix_df.to_excel(writer, sheet_name="Mix de Ativos", index=False)
        clients_df.to_excel(writer, sheet_name="Clientes", index=False)
        allocations_df.to_excel(writer, sheet_name="Alocacoes", index=False)
        movements_df.to_excel(writer, sheet_name="Movimentacoes", index=False)

    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=dashboard.xlsx"}
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
