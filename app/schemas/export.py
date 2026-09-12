from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.export_job import ExportStatus


class ExportJobCreate(BaseModel):
    list_id: int


class ExportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    list_id: int | None
    status: ExportStatus
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None
