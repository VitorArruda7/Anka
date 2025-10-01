import pytest


@pytest.mark.asyncio
async def test_audit_logs_registers_entries(client):
    client_payload = {
        "name": "Delta Partners",
        "email": "delta@example.com",
        "is_active": True,
    }
    create_response = await client.post("/api/clients/", json=client_payload)
    assert create_response.status_code == 201

    audit_response = await client.get("/api/audit/")
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["meta"]["total"] >= 1
    actions = {item["action"] for item in payload["items"]}
    assert "client.created" in actions


@pytest.mark.asyncio
async def test_audit_logs_filters_by_action(client):
    asset_payload = {
        "ticker": "abli11",
        "name": "Able Inc.",
        "exchange": "NYSE",
        "currency": "USD",
    }
    asset_response = await client.post("/api/assets/", json=asset_payload)
    assert asset_response.status_code == 201

    filtered_response = await client.get("/api/audit/", params={"action": "asset.created"})
    assert filtered_response.status_code == 200
    data = filtered_response.json()
    assert all(item["action"] == "asset.created" for item in data["items"])
    assert data["meta"]["total"] >= 1
