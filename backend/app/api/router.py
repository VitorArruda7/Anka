from fastapi import APIRouter

from app.api.routes import (
    allocations,
    assets,
    auth,
    clients,
    dashboard,
    export,
    movements,
    users,
    audit,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(allocations.router, prefix="/allocations", tags=["allocations"])
api_router.include_router(movements.router, prefix="/movements", tags=["movements"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
