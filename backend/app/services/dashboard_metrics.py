from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import redis_delete, redis_get_json, redis_set_json
from app.core.config import get_settings
from app.models.allocation import Allocation
from app.models.asset import Asset
from app.models.client import Client
from app.models.movement import Movement, MovementType

logger = logging.getLogger(__name__)

DASHBOARD_CACHE_KEY = "dashboard:metrics"
MONTH_LABELS = [
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez",
]

DashboardMetrics = dict[str, Any]


def _ensure_float(value: float | int | Decimal | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _format_month_label(key: str) -> str:
    try:
        year, month = key.split("-")
        index = int(month) - 1
    except (ValueError, IndexError):
        return key
    label = MONTH_LABELS[index] if 0 <= index < len(MONTH_LABELS) else month
    return f"{label}/{year[-2:]}"


def compute_dashboard_metrics(
    clients: Sequence[Client],
    assets: Sequence[Asset],
    allocations: Sequence[Allocation],
    movements: Sequence[Movement],
) -> DashboardMetrics:
    asset_map = {asset.id: asset for asset in assets}

    allocation_totals_by_client: defaultdict[int, float] = defaultdict(float)
    allocation_mix_values: defaultdict[int, float] = defaultdict(float)
    custody_by_month: defaultdict[str, float] = defaultdict(float)

    for allocation in allocations:
        quantity = _ensure_float(allocation.quantity)
        price = _ensure_float(allocation.buy_price)
        invested_value = round(quantity * price, 2)

        allocation_totals_by_client[allocation.client_id] += invested_value
        allocation_mix_values[allocation.asset_id] += invested_value

        month_key = allocation.buy_date.strftime("%Y-%m")
        custody_by_month[month_key] += invested_value

    flow_by_month: defaultdict[str, dict[str, float]] = defaultdict(lambda: {"inflow": 0.0, "outflow": 0.0})
    movement_totals = {"deposits": 0.0, "withdrawals": 0.0, "net": 0.0}

    for movement in movements:
        amount = round(_ensure_float(movement.amount), 2)
        month_key = movement.date.strftime("%Y-%m")
        entry = flow_by_month[month_key]

        if movement.type == MovementType.deposit:
            entry["inflow"] += amount
            movement_totals["deposits"] += amount
            movement_totals["net"] += amount
        else:
            entry["outflow"] += amount
            movement_totals["withdrawals"] += amount
            movement_totals["net"] -= amount

    custody_series: list[dict[str, Any]] = []
    custody_totals: list[float] = []
    running_total = 0.0
    for key in sorted(custody_by_month.keys()):
        running_total = round(running_total + custody_by_month[key], 2)
        custody_totals.append(running_total)
        custody_series.append({
            "month": key,
            "label": _format_month_label(key),
            "value": running_total,
        })

    flow_series: list[dict[str, Any]] = []
    for key in sorted(flow_by_month.keys()):
        inflow = round(flow_by_month[key]["inflow"], 2)
        outflow = round(flow_by_month[key]["outflow"], 2)
        flow_series.append({
            "month": key,
            "label": _format_month_label(key),
            "inflow": inflow,
            "outflow": outflow,
            "net": round(inflow - outflow, 2),
        })

    total_invested_raw = sum(allocation_totals_by_client.values())

    allocation_mix: list[dict[str, Any]] = []
    for asset_id, value in allocation_mix_values.items():
        asset = asset_map.get(asset_id)
        label = f"{asset.ticker} - {asset.name}" if asset else f"Ativo {asset_id}"
        share = (value / total_invested_raw * 100) if total_invested_raw else 0.0
        allocation_mix.append({
            "asset_id": asset_id,
            "label": label,
            "value": round(value, 2),
            "share": round(share, 2),
        })
    allocation_mix.sort(key=lambda item: item["value"], reverse=True)

    allocation_totals_by_client_list = [
        {"client_id": client_id, "total": round(total, 2)}
        for client_id, total in allocation_totals_by_client.items()
    ]
    allocation_totals_by_client_list.sort(key=lambda item: item["total"], reverse=True)

    total_clients = len(clients)
    total_active = sum(1 for client in clients if client.is_active)
    active_ratio = (total_active / total_clients * 100) if total_clients else 0.0

    last_custody = custody_totals[-1] if custody_totals else 0.0
    prev_custody = custody_totals[-2] if len(custody_totals) > 1 else last_custody
    custody_diff = ((last_custody - prev_custody) / prev_custody * 100) if prev_custody else 0.0

    last_flow_entry = flow_series[-1] if flow_series else None
    prev_flow_entry = flow_series[-2] if len(flow_series) > 1 else last_flow_entry

    last_inflow = last_flow_entry["inflow"] if last_flow_entry else 0.0
    prev_inflow = prev_flow_entry["inflow"] if prev_flow_entry else last_inflow
    inflow_diff = ((last_inflow - prev_inflow) / prev_inflow * 100) if prev_inflow else 0.0

    last_net = last_flow_entry["net"] if last_flow_entry else 0.0
    prev_net = prev_flow_entry["net"] if prev_flow_entry else last_net
    net_diff = ((last_net - prev_net) / abs(prev_net) * 100) if prev_net else 0.0

    movement_totals = {key: round(value, 2) for key, value in movement_totals.items()}

    kpis = [
        {
            "indicator": "Clientes ativos",
            "value": f"{total_active}/{total_clients}",
            "variation": round(active_ratio, 2),
        },
        {
            "indicator": "Total investido",
            "value": round(total_invested_raw, 2),
            "variation": round(custody_diff, 2),
        },
        {
            "indicator": "Entradas do mes",
            "value": round(last_inflow, 2),
            "variation": round(inflow_diff, 2),
        },
        {
            "indicator": "Saldo liquido",
            "value": movement_totals["net"],
            "variation": round(net_diff, 2),
        },
    ]

    metrics: DashboardMetrics = {
        "generated_at": datetime.now(UTC).isoformat(),
        "totals": {
            "clients": total_clients,
            "active_clients": total_active,
            "active_ratio": round(active_ratio, 2),
            "total_invested": round(total_invested_raw, 2),
        },
        "movement_totals": movement_totals,
        "differences": {
            "custody": round(custody_diff, 2),
            "inflow": round(inflow_diff, 2),
            "net": round(net_diff, 2),
        },
        "last_period": {
            "custody": round(last_custody, 2),
            "inflow": round(last_inflow, 2),
            "net": round(last_net, 2),
        },
        "custody_series": custody_series,
        "flow_series": flow_series,
        "allocation_mix": allocation_mix,
        "allocation_totals_by_client": allocation_totals_by_client_list,
        "kpis": kpis,
    }
    return metrics


async def _fetch_dataset(session: AsyncSession) -> tuple[
    list[Client],
    list[Asset],
    list[Allocation],
    list[Movement],
]:
    clients_result = await session.execute(select(Client))
    clients = list(clients_result.scalars().all())

    assets_result = await session.execute(select(Asset))
    assets = list(assets_result.scalars().all())

    allocations_result = await session.execute(select(Allocation))
    allocations = list(allocations_result.scalars().all())

    movements_result = await session.execute(select(Movement))
    movements = list(movements_result.scalars().all())

    return clients, assets, allocations, movements


async def get_dashboard_metrics(
    session: AsyncSession,
    *,
    use_cache: bool = True,
) -> DashboardMetrics:
    if use_cache:
        cached = await redis_get_json(DASHBOARD_CACHE_KEY)
        if isinstance(cached, dict):
            return cached

    dataset = await _fetch_dataset(session)
    metrics = compute_dashboard_metrics(*dataset)
    await cache_dashboard_metrics(metrics)
    return metrics


async def cache_dashboard_metrics(metrics: DashboardMetrics) -> None:
    settings = get_settings()
    ttl = settings.dashboard_cache_ttl
    if ttl <= 0:
        return
    await redis_set_json(DASHBOARD_CACHE_KEY, metrics, ttl=ttl)


async def invalidate_dashboard_metrics() -> None:
    await redis_delete(DASHBOARD_CACHE_KEY)


__all__ = [
    "DASHBOARD_CACHE_KEY",
    "cache_dashboard_metrics",
    "get_dashboard_metrics",
    "invalidate_dashboard_metrics",
    "compute_dashboard_metrics",
]
