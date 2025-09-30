import pytest


@pytest.mark.asyncio
async def test_create_asset(client):
    payload = {
        "ticker": "TEST",
        "name": "Test Asset",
        "exchange": "Test Exchange",
        "currency": "USD",
    }
    response = await client.post("/api/assets/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["ticker"] == payload["ticker"]

    list_response = await client.get("/api/assets/")
    assert list_response.status_code == 200
    assets = list_response.json()
    assert any(asset["ticker"] == payload["ticker"] for asset in assets)
