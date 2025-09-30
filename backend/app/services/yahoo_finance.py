from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class YahooFinanceClient:
    quote_api = "https://query1.finance.yahoo.com/v7/finance/quote"
    crumb_endpoint = "https://query1.finance.yahoo.com/v1/test/getcrumb"
    auth_endpoint = "https://fc.yahoo.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }

    async def fetch_quote(self, ticker: str) -> dict[str, Any]:
        symbol = ticker.upper().strip()
        async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
            await client.get(self.auth_endpoint)
            crumb_response = await client.get(self.crumb_endpoint)
            crumb_response.raise_for_status()
            crumb = crumb_response.text.strip()
            if not crumb:
                raise ValueError("N?o foi poss?vel obter credenciais do Yahoo Finance")

            params = {"symbols": symbol, "crumb": crumb}
            response = await client.get(self.quote_api, params=params)
            if response.status_code == 401:
                raise ValueError("Ticker n?o encontrado no Yahoo Finance")
            response.raise_for_status()

        payload = response.json()
        results = payload.get("quoteResponse", {}).get("result")
        if not results:
            raise ValueError("Ticker n?o encontrado no Yahoo Finance")

        info = results[0]
        exchange = (
            info.get("fullExchangeName")
            or info.get("market")
            or ("B3" if symbol.endswith(".SA") else "Desconhecida")
        )
        return {
            "symbol": info.get("symbol", symbol).upper(),
            "shortName": info.get("shortName"),
            "longName": info.get("longName"),
            "fullExchangeName": exchange,
            "currency": info.get("currency") or ("BRL" if symbol.endswith(".SA") else "USD"),
        }


class BrapiClient:
    base_url = "https://brapi.dev/api/quote/"

    async def fetch_quote(self, ticker: str) -> dict[str, Any]:
        symbol = ticker.upper().strip()
        is_b3 = False
        if symbol.endswith(".SA"):
            symbol = symbol[:-3]
            is_b3 = True

        settings = get_settings()
        params: dict[str, str] = {}
        if settings.brapi_token:
            params["token"] = settings.brapi_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(urljoin(self.base_url, symbol), params=params)

        if response.status_code == 401:
            raise ValueError("A API de mercado recusou o ticker informado")

        response.raise_for_status()
        payload = response.json()
        results = payload.get("results")
        if not results:
            raise ValueError("Ticker n?o encontrado")

        info = results[0]
        exchange = info.get("market") or ("B3" if is_b3 else "Desconhecida")
        return {
            "symbol": info.get("symbol", symbol).upper(),
            "shortName": info.get("shortName"),
            "longName": info.get("longName"),
            "fullExchangeName": exchange,
            "currency": info.get("currency") or ("BRL" if is_b3 else "USD"),
        }


class MarketDataService:
    def __init__(self) -> None:
        self.yahoo = YahooFinanceClient()
        self.brapi = BrapiClient()

    async def fetch_quote(self, ticker: str) -> dict[str, Any]:
        try:
            quote = await self.yahoo.fetch_quote(ticker)
            logger.info("Quote fetched via Yahoo Finance for %s", ticker)
            return quote
        except Exception as yahoo_error:  # noqa: BLE001
            logger.warning(
                "Yahoo Finance fetch failed for %s: %s. Falling back to BRAPI.",
                ticker,
                yahoo_error,
            )
            try:
                quote = await self.brapi.fetch_quote(ticker)
                logger.info("Quote fetched via BRAPI for %s", ticker)
                return quote
            except Exception as brapi_error:  # noqa: BLE001
                logger.error(
                    "BRAPI fetch also failed for %s: %s (Yahoo error: %s)",
                    ticker,
                    brapi_error,
                    yahoo_error,
                )
                raise brapi_error


market_data_service = MarketDataService()
yahoo_finance_service = market_data_service
