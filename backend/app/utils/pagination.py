from __future__ import annotations

from math import ceil
from typing import Any

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.schemas.pagination import Paginated, PaginationMeta

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 500


def normalize_pagination(page: int | None, page_size: int | None) -> tuple[int, int]:
    page = page or DEFAULT_PAGE
    page_size = page_size or DEFAULT_PAGE_SIZE
    if page < 1:
        page = DEFAULT_PAGE
    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE
    page_size = min(page_size, MAX_PAGE_SIZE)
    return page, page_size


async def paginate(
    session: AsyncSession,
    stmt: Select[Any],
    *,
    page: int,
    page_size: int,
) -> Paginated[Any]:
    page, page_size = normalize_pagination(page, page_size)
    count_stmt = stmt.order_by(None).with_only_columns(func.count())
    total_result = await session.execute(count_stmt)
    total = int(total_result.scalar_one() or 0)
    pages = ceil(total / page_size) if total else 0
    if total == 0:
        page = 1
    elif page > pages:
        page = pages
    offset = (page - 1) * page_size if total else 0
    limited_stmt = stmt.offset(offset).limit(page_size)
    items_result = await session.execute(limited_stmt)
    items = list(items_result.scalars().all())
    meta = PaginationMeta(total=total, page=page, page_size=page_size, pages=pages)
    return Paginated(items=items, meta=meta)
