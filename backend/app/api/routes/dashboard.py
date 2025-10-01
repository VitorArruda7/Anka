from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardMetrics
from app.services.dashboard_metrics import get_dashboard_metrics

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
async def read_dashboard_metrics(
    refresh: bool = Query(default=False),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> DashboardMetrics:
    return await get_dashboard_metrics(session, use_cache=not refresh)
