from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.item import ItemStatus


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    status: ItemStatus = ItemStatus.TO_READ
    description: str | None = None


class ItemUpdate(BaseModel):
    """All fields optional: PATCH-style partial update."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    status: ItemStatus | None = None
    description: str | None = None


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_id: int
    title: str
    status: ItemStatus
    description: str | None
    created_at: datetime
    updated_at: datetime
