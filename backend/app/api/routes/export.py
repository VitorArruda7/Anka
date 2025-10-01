import csv
import io
from collections import defaultdict
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


MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def _format_month_label(key: str) -> str:
    try:
        year, month = key.split("-")
        index = int(month) - 1
    except (ValueError, IndexError):
        return key
    label = MONTH_LABELS[index] if 0 <= index < len(MONTH_LABELS) else month
    return f"{label}/{year[-2:]}"


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

    allocation_totals_by_client = defaultdict(float)
    allocation_mix_values = defaultdict(float)
    custody_by_month = defaultdict(float)
    allocation_rows: list[dict[str, object]] = []

    for allocation in allocations:
        quantity = _ensure_float(allocation.quantity)
        price = _ensure_float(allocation.buy_price)
        invested_value = round(quantity * price, 2)

        allocation_totals_by_client[allocation.client_id] += invested_value
        allocation_mix_values[allocation.asset_id] += invested_value

        month_key = allocation.buy_date.strftime("%Y-%m")
        custody_by_month[month_key] += invested_value

        client = client_map.get(allocation.client_id)
        asset = asset_map.get(allocation.asset_id)

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

    flow_by_month: defaultdict[str, dict[str, float]] = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0})
    movement_rows: list[dict[str, object]] = []
    movement_totals = {"deposits": 0.0, "withdrawals": 0.0, "net": 0.0}

    for movement in movements:
        amount = round(_ensure_float(movement.amount), 2)
        month_key = movement.date.strftime("%Y-%m")
        entry = flow_by_month[month_key]

        client = client_map.get(movement.client_id)

        if movement.type == MovementType.deposit:
            entry["inflow"] += amount
            movement_totals["deposits"] += amount
            movement_totals["net"] += amount
            movement_type = "Deposito"
        else:
            entry["outflow"] += amount
            movement_totals["withdrawals"] += amount
            movement_totals["net"] -= amount
            movement_type = "Retirada"

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

    custody_rows: list[dict[str, object]] = []
    custody_totals: list[float] = []
    running_total = 0.0
    for key in sorted(custody_by_month.keys()):
        running_total = round(running_total + custody_by_month[key], 2)
        custody_totals.append(running_total)
        custody_rows.append({"Mes": _format_month_label(key), "Valor acumulado": running_total})

    flow_entries: list[dict[str, object]] = []
    for key in sorted(flow_by_month.keys()):
        inflow = round(flow_by_month[key]["inflow"], 2)
        outflow = round(flow_by_month[key]["outflow"], 2)
        flow_entries.append({"key": key, "label": _format_month_label(key), "inflow": inflow, "outflow": outflow})

    flow_rows = [
        {
            "Mes": entry["label"],
            "Entradas": entry["inflow"],
            "Saidas": entry["outflow"],
            "Saldo liquido": round(entry["inflow"] - entry["outflow"], 2),
        }
        for entry in flow_entries
    ]

    total_invested_raw = sum(allocation_totals_by_client.values())
    allocation_mix_rows = []
    for asset_id, value in allocation_mix_values.items():
        asset = asset_map.get(asset_id)
        label = f"{asset.ticker} - {asset.name}" if asset else f"Ativo {asset_id}"
        share = (value / total_invested_raw * 100) if total_invested_raw else 0.0
        allocation_mix_rows.append(
            {
                "Ativo": label,
                "Valor investido": round(value, 2),
                "Participacao (%)": round(share, 2),
            }
        )

    clients_rows = []
    for client in clients:
        total_for_client = allocation_totals_by_client.get(client.id, 0.0)
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

    last_custody = custody_totals[-1] if custody_totals else 0.0
    prev_custody = custody_totals[-2] if len(custody_totals) > 1 else last_custody
    custody_diff = ((last_custody - prev_custody) / prev_custody * 100) if prev_custody else 0.0

    last_flow_entry = flow_entries[-1] if flow_entries else None
    prev_flow_entry = flow_entries[-2] if len(flow_entries) > 1 else last_flow_entry

    last_inflow = last_flow_entry["inflow"] if last_flow_entry else 0.0
    prev_inflow = prev_flow_entry["inflow"] if prev_flow_entry else last_inflow
    inflow_diff = ((last_inflow - prev_inflow) / prev_inflow * 100) if prev_inflow else 0.0

    last_net = (
        (last_flow_entry["inflow"] - last_flow_entry["outflow"]) if last_flow_entry else 0.0
    )
    prev_net = (
        (prev_flow_entry["inflow"] - prev_flow_entry["outflow"]) if prev_flow_entry else last_net
    )
    net_diff = ((last_net - prev_net) / abs(prev_net) * 100) if prev_net else 0.0

    total_clients = len(clients)
    total_active = sum(1 for client in clients if client.is_active)
    active_ratio = (total_active / total_clients * 100) if total_clients else 0.0

    kpi_rows = [
        {
            "Indicador": "Clientes ativos",
            "Valor": f"{total_active}/{total_clients}",
            "Variacao (%)": round(active_ratio, 2),
        },
        {
            "Indicador": "Total investido",
            "Valor": round(total_invested_raw, 2),
            "Variacao (%)": round(custody_diff, 2),
        },
        {
            "Indicador": "Entradas do mes",
            "Valor": round(last_inflow, 2),
            "Variacao (%)": round(inflow_diff, 2),
        },
        {
            "Indicador": "Saldo liquido",
            "Valor": round(movement_totals["net"], 2),
            "Variacao (%)": round(net_diff, 2),
        },
    ]

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
