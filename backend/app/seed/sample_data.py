from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models import Allocation, Asset, Client, Movement, MovementType, User


async def seed_sample_data() -> None:
    async with AsyncSessionLocal() as session:
        await ensure_user(session)
        assets = await ensure_assets(session)
        clients = await ensure_clients(session)
        await ensure_allocations(session, clients, assets)
        await ensure_movements(session, clients)
        await session.commit()


async def ensure_user(session) -> None:
    demo_email = "demo@anka.com"
    result = await session.execute(select(User).where(User.email == demo_email))
    user = result.scalar_one_or_none()
    if user:
        return
    demo_user = User(
        name="Consultor Demo",
        email=demo_email,
        hashed_password=get_password_hash("demo123"),
        is_active=True,
    )
    session.add(demo_user)
    await session.flush()


async def ensure_assets(session) -> dict[str, Asset]:
    predefined = [
        {"ticker": "PETR4", "name": "Petrobras PN", "exchange": "B3", "currency": "BRL"},
        {"ticker": "ITUB4", "name": "Itaú Unibanco PN", "exchange": "B3", "currency": "BRL"},
        {"ticker": "BOVA11", "name": "iShares Ibovespa", "exchange": "B3", "currency": "BRL"},
        {"ticker": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD"},
        {"ticker": "GLD", "name": "SPDR Gold Shares", "exchange": "NYSEARCA", "currency": "USD"},
    ]
    assets: dict[str, Asset] = {}
    for item in predefined:
        result = await session.execute(select(Asset).where(Asset.ticker == item["ticker"]))
        asset = result.scalar_one_or_none()
        if not asset:
            asset = Asset(**item)
            session.add(asset)
            await session.flush()
        assets[item["ticker"]] = asset
    return assets


async def ensure_clients(session) -> dict[str, Client]:
    predefined = [
        {"name": "Aurora Capital", "email": "aurora@clients.com", "is_active": True},
        {"name": "Boreal Family Office", "email": "boreal@clients.com", "is_active": True},
        {"name": "Constelação Invest", "email": "constelacao@clients.com", "is_active": False},
    ]
    clients: dict[str, Client] = {}
    for item in predefined:
        result = await session.execute(select(Client).where(Client.email == item["email"]))
        client = result.scalar_one_or_none()
        if not client:
            client = Client(**item)
            session.add(client)
            await session.flush()
        clients[item["email"]] = client
    return clients


async def ensure_allocations(session, clients, assets) -> None:
    allocations = [
        ("aurora@clients.com", "PETR4", Decimal("1200"), Decimal("32.50"), date(2024, 5, 20)),
        ("aurora@clients.com", "BOVA11", Decimal("800"), Decimal("110.40"), date(2024, 3, 15)),
        ("boreal@clients.com", "ITUB4", Decimal("1500"), Decimal("28.70"), date(2024, 1, 10)),
        ("boreal@clients.com", "AAPL", Decimal("50"), Decimal("165.00"), date(2024, 6, 5)),
        ("constelacao@clients.com", "GLD", Decimal("75"), Decimal("181.20"), date(2023, 11, 22)),
    ]
    for client_email, ticker, quantity, price, buy_date in allocations:
        client = clients[client_email]
        asset = assets[ticker]
        result = await session.execute(
            select(Allocation).where(
                Allocation.client_id == client.id,
                Allocation.asset_id == asset.id,
            )
        )
        allocation = result.scalar_one_or_none()
        if allocation:
            continue
        allocation = Allocation(
            client_id=client.id,
            asset_id=asset.id,
            quantity=quantity,
            buy_price=price,
            buy_date=buy_date,
        )
        session.add(allocation)
    await session.flush()


async def ensure_movements(session, clients) -> None:
    movements = [
        ("aurora@clients.com", MovementType.deposit, Decimal("250000"), date(2024, 5, 18), "Aporte trimestral"),
        ("aurora@clients.com", MovementType.withdrawal, Decimal("85000"), date(2024, 7, 2), "Liquidação de lucro"),
        ("boreal@clients.com", MovementType.deposit, Decimal("180000"), date(2024, 2, 1), "Novo mandato"),
        ("boreal@clients.com", MovementType.deposit, Decimal("95000"), date(2024, 6, 8), "Reforço de carteira"),
        ("constelacao@clients.com", MovementType.withdrawal, Decimal("45000"), date(2024, 3, 29), "Rebalanceamento"),
    ]
    for client_email, mov_type, amount, mov_date, note in movements:
        client = clients[client_email]
        result = await session.execute(
            select(Movement).where(
                Movement.client_id == client.id,
                Movement.type == mov_type,
                Movement.amount == amount,
                Movement.date == mov_date,
            )
        )
        movement = result.scalar_one_or_none()
        if movement:
            continue
        movement = Movement(
            client_id=client.id,
            type=mov_type,
            amount=amount,
            date=mov_date,
            note=note,
        )
        session.add(movement)
    await session.flush()


def main() -> None:
    asyncio.run(seed_sample_data())


if __name__ == "__main__":
    main()
