import pytest


@pytest.mark.asyncio
async def test_create_and_filter_clients(client):
    payload = {
        "name": "Charlie",
        "email": "charlie@example.com",
        "is_active": True,
    }
    create_response = await client.post("/api/clients/", json=payload)
    assert create_response.status_code == 201

    list_response = await client.get("/api/clients/", params={"search": "char"})
    assert list_response.status_code == 200
    clients = list_response.json()
    assert any(c["email"] == payload["email"] for c in clients)
