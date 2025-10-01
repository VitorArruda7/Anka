from datetime import date

import pytest


@pytest.mark.asyncio
async def test_dashboard_metrics_endpoint(client):
    asset_payload = {
        "ticker": "PETR4",
        "name": "Petrobras",
        "exchange": "B3",
        "currency": "BRL",
    }
    asset_response = await client.post("/api/assets/", json=asset_payload)
    assert asset_response.status_code == 201
    asset_id = asset_response.json()["id"]

    client_payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "is_active": True,
    }
    client_response = await client.post("/api/clients/", json=client_payload)
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]

    allocation_payload = {
        "client_id": client_id,
        "asset_id": asset_id,
        "quantity": 10,
        "buy_price": 15.5,
        "buy_date": date(2024, 5, 1).isoformat(),
    }
    allocation_response = await client.post("/api/allocations/", json=allocation_payload)
    assert allocation_response.status_code == 201

    movement_payload = {
        "client_id": client_id,
        "type": "deposit",
        "amount": 500,
        "date": date(2024, 5, 3).isoformat(),
        "note": "Initial deposit",
    }
    movement_response = await client.post("/api/movements/", json=movement_payload)
    assert movement_response.status_code == 201

    metrics_response = await client.get("/api/dashboard/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()

    assert metrics["totals"]["clients"] == 1
    assert metrics["totals"]["active_clients"] == 1
    assert metrics["totals"]["total_invested"] == pytest.approx(155.0)
    assert metrics["movement_totals"]["deposits"] == pytest.approx(500.0)

    allocation_totals = metrics["allocation_totals_by_client"]
    total_entry = next((item for item in allocation_totals if item["client_id"] == client_id), None)
    assert total_entry is not None
    assert total_entry["total"] == pytest.approx(155.0)

    custody_series = metrics["custody_series"]
    assert custody_series and custody_series[0]["value"] == pytest.approx(155.0)

    flow_series = metrics["flow_series"]
    assert flow_series and flow_series[0]["inflow"] == pytest.approx(500.0)

    assert len(metrics["kpis"]) == 4

    refresh_response = await client.get("/api/dashboard/metrics", params={"refresh": "true"})
    assert refresh_response.status_code == 200
