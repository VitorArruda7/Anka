import pytest

from app.core.config import get_settings
from app.services.yahoo_finance import MarketDataService


@pytest.mark.asyncio
async def test_market_data_service_returns_cached(monkeypatch):
    service = MarketDataService()

    async def fake_get_json(key: str):
        return {"symbol": "PETR4"}

    async def fake_set_json(*args, **kwargs):
        raise AssertionError("cache should not be updated when hit")

    async def fake_yahoo_fetch(self, ticker: str):
        raise AssertionError("remote fetch should not happen on cache hit")

    monkeypatch.setattr("app.services.yahoo_finance.redis_get_json", fake_get_json)
    monkeypatch.setattr("app.services.yahoo_finance.redis_set_json", fake_set_json)
    monkeypatch.setattr(
        "app.services.yahoo_finance.YahooFinanceClient.fetch_quote",
        fake_yahoo_fetch,
    )

    result = await service.fetch_quote("PETR4")
    assert result["symbol"] == "PETR4"


@pytest.mark.asyncio
async def test_market_data_service_caches_new_quote(monkeypatch):
    service = MarketDataService()
    stored: dict[str, object] = {}

    async def fake_get_json(key: str):
        stored["get_key"] = key
        return None

    async def fake_set_json(key: str, value: dict, ttl: int | None = None):
        stored["set"] = {"key": key, "value": value, "ttl": ttl}

    async def fake_yahoo_fetch(self, ticker: str):
        return {"symbol": ticker.upper(), "shortName": "Mock"}

    async def fake_brapi_fetch(self, ticker: str):
        raise AssertionError("fallback should not run when primary succeeds")

    monkeypatch.setattr("app.services.yahoo_finance.redis_get_json", fake_get_json)
    monkeypatch.setattr("app.services.yahoo_finance.redis_set_json", fake_set_json)
    monkeypatch.setattr(
        "app.services.yahoo_finance.YahooFinanceClient.fetch_quote",
        fake_yahoo_fetch,
    )
    monkeypatch.setattr(
        "app.services.yahoo_finance.BrapiClient.fetch_quote",
        fake_brapi_fetch,
    )

    result = await service.fetch_quote("petr4")
    assert result["symbol"] == "PETR4"
    assert stored["get_key"] == "market:quote:PETR4"
    cache_record = stored["set"]
    assert cache_record["key"] == "market:quote:PETR4"
    assert cache_record["value"]["symbol"] == "PETR4"
    assert cache_record["ttl"] == get_settings().market_cache_ttl
