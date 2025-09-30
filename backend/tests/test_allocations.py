import pytest


@pytest.mark.asyncio
async def test_create_allocation(client):
    client_payload = {"name": "Dana", "email": "dana@example.com", "is_active": True}
    client_response = await client.post("/api/clients/", json=client_payload)
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]

    asset_payload = {
        "ticker": "DANA",
        "name": "Dana Asset",
        "exchange": "Test",
        "currency": "USD",
    }
    asset_response = await client.post("/api/assets/", json=asset_payload)
    assert asset_response.status_code == 201
    asset_id = asset_response.json()["id"]

    allocation_payload = {
        "client_id": client_id,
        "asset_id": asset_id,
        "quantity": "10",
        "buy_price": "100",
        "buy_date": "2024-01-01",
    }
    allocation_response = await client.post("/api/allocations/", json=allocation_payload)
    assert allocation_response.status_code == 201

    list_response = await client.get("/api/allocations/", params={"client_id": client_id})
    assert list_response.status_code == 200
    allocations = list_response.json()
    assert len(allocations) == 1
