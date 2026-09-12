from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ListCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ListUpdate(BaseModel):
    """All fields optional: PATCH-style partial update."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime
