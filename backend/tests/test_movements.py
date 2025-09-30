import pytest


@pytest.mark.asyncio
async def test_create_movement(client):
    client_payload = {"name": "Eve", "email": "eve@example.com", "is_active": True}
    client_response = await client.post("/api/clients/", json=client_payload)
    assert client_response.status_code == 201
    client_id = client_response.json()["id"]

    movement_payload = {
        "client_id": client_id,
        "type": "deposit",
        "amount": "5000",
        "date": "2024-02-01",
        "note": "Initial deposit",
    }
    movement_response = await client.post("/api/movements/", json=movement_payload)
    assert movement_response.status_code == 201

    list_response = await client.get("/api/movements/", params={"client_id": client_id})
    assert list_response.status_code == 200
    movements = list_response.json()
    assert len(movements) == 1
