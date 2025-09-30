import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    register_payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "password": "secret",
    }
    response = await client.post("/api/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == register_payload["email"]

    login_payload = {
        "email": register_payload["email"],
        "password": register_payload["password"],
    }
    login_response = await client.post("/api/auth/login", json=login_payload)
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
