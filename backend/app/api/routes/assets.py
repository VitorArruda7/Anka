from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetRead
from app.services.yahoo_finance import yahoo_finance_service

router = APIRouter()


@router.get("/", response_model=list[AssetRead])
async def list_assets(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Asset]:
    result = await session.execute(select(Asset).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.post("/", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_in: AssetCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Asset:
    payload = asset_in.model_dump()
    payload["ticker"] = payload["ticker"].upper()
    asset = Asset(**payload)
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    return asset


@router.post("/fetch/{ticker}", response_model=AssetRead)
async def fetch_asset(
    ticker: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Asset:
    normalized = ticker.upper()
    result = await session.execute(select(Asset).where(Asset.ticker == normalized))
    existing = result.scalars().first()
    if existing:
        return existing
    try:
        payload = await yahoo_finance_service.fetch_quote(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    asset = Asset(
        ticker=payload.get("symbol", normalized).upper(),
        name=payload.get("shortName") or payload.get("longName") or normalized,
        exchange=payload.get("fullExchangeName", "Unknown"),
        currency=payload.get("currency", "USD"),
    )
    session.add(asset)
    await session.commit()
    await session.refresh(asset)
    return asset
