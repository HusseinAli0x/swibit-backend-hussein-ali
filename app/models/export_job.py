import enum
from datetime import datetime, timezone

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExportStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportJob(Base):
    """A background job that renders one list (and its items) to a file."""

    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Denormalized owner_id: lets authorization checks avoid a join through
    # `lists`, and keeps the job (and its status) visible to its owner even
    # if the source list is later deleted.
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    list_id: Mapped[int] = mapped_column(
        ForeignKey("lists.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[ExportStatus] = mapped_column(
        SAEnum(
            ExportStatus,
            name="export_status",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ExportStatus.PENDING,
    )
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
