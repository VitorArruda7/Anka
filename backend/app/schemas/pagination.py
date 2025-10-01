from __future__ import annotations

from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)

    @classmethod
    def create(cls, *, total: int, page: int, page_size: int) -> "PaginationMeta":
        pages = ceil(total / page_size) if total else 0
        current_page = max(1, min(page, pages or 1))
        return cls(total=total, page=current_page, page_size=page_size, pages=pages)


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta
