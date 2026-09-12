"""Shared schema pieces: pagination query params and the paginated envelope."""
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Pagination:
    """FastAPI dependency: `limit`/`offset` query params, clamped to sane bounds."""

    def __init__(
        self,
        limit: int = Query(20, ge=1, le=100, description="Max items to return."),
        offset: int = Query(0, ge=0, description="Number of items to skip."),
    ) -> None:
        self.limit = limit
        self.offset = offset


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
