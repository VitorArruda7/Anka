import pytest


@pytest.mark.asyncio
async def test_create_and_list_users(client):
    payload = {
        "name": "Bob",
        "email": "bob@example.com",
        "password": "secret",
    }
    create_response = await client.post("/api/users/", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["email"] == payload["email"]

    list_response = await client.get("/api/users/")
    assert list_response.status_code == 200
    data = list_response.json()
    assert data["meta"]["total"] >= 1
    assert any(user["email"] == payload["email"] for user in data["items"])
