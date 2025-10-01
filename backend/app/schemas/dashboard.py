from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


class CustodyPoint(BaseModel):
    month: str
    label: str
    value: float


class FlowPoint(BaseModel):
    month: str
    label: str
    inflow: float
    outflow: float
    net: float


class AllocationMixEntry(BaseModel):
    asset_id: int
    label: str
    value: float
    share: float


class AllocationTotalByClient(BaseModel):
    client_id: int
    total: float


class KpiEntry(BaseModel):
    indicator: str
    value: float | str
    variation: float


class DashboardTotals(BaseModel):
    clients: int
    active_clients: int
    active_ratio: float
    total_invested: float


class MovementTotals(BaseModel):
    deposits: float
    withdrawals: float
    net: float


class Differences(BaseModel):
    custody: float
    inflow: float
    net: float


class LastPeriod(BaseModel):
    custody: float
    inflow: float
    net: float


class DashboardMetrics(BaseModel):
    generated_at: datetime
    totals: DashboardTotals
    movement_totals: MovementTotals
    differences: Differences
    last_period: LastPeriod
    custody_series: List[CustodyPoint]
    flow_series: List[FlowPoint]
    allocation_mix: List[AllocationMixEntry]
    allocation_totals_by_client: List[AllocationTotalByClient]
    kpis: List[KpiEntry]
