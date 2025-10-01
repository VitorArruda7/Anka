from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.asset import Asset
from app.models.user import User
from app.utils.pagination import paginate
from app.schemas.asset import AssetCreate, AssetRead
from app.schemas.pagination import Paginated
from app.services.audit import log_audit_event
from app.services.dashboard_metrics import invalidate_dashboard_metrics
from app.services.yahoo_finance import yahoo_finance_service

router = APIRouter()


@router.get("/", response_model=Paginated[AssetRead])
async def list_assets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    search: str | None = None,
    exchange: str | None = None,
    currency: str | None = None,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Paginated[AssetRead]:
    stmt = select(Asset)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(Asset.ticker.ilike(pattern), Asset.name.ilike(pattern)))
    if exchange:
        stmt = stmt.where(Asset.exchange.ilike(f"%{exchange}%"))
    if currency:
        stmt = stmt.where(Asset.currency.ilike(f"%{currency}%"))
    stmt = stmt.order_by(Asset.ticker.asc())
    return await paginate(session, stmt, page=page, page_size=page_size)


@router.post("/", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_in: AssetCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Asset:
    payload = asset_in.model_dump()
    payload["ticker"] = payload["ticker"].upper()
    asset = Asset(**payload)
    session.add(asset)
    await session.flush()
    await log_audit_event(
        session,
        user_id=current_user.id,
        action="asset.created",
        entity="asset",
        entity_id=asset.id,
        metadata={"ticker": asset.ticker, "name": asset.name},
    )
    await session.commit()
    await session.refresh(asset)
    await invalidate_dashboard_metrics()
    return asset


@router.post("/fetch/{ticker}", response_model=AssetRead)
async def fetch_asset(
    ticker: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
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
    await session.flush()
    await log_audit_event(
        session,
        user_id=current_user.id,
        action="asset.imported",
        entity="asset",
        entity_id=asset.id,
        metadata={
            "ticker": asset.ticker,
            "source": "yahoo",
        },
    )
    await session.commit()
    await session.refresh(asset)
    await invalidate_dashboard_metrics()
    return asset
