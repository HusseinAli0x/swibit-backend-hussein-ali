import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.list import List as ListModel


class ItemStatus(str, enum.Enum):
    """Domain flavor: a book's reading progress on its shelf."""

    TO_READ = "to_read"
    READING = "reading"
    FINISHED = "finished"


class Item(Base):
    """A single entry inside a list (domain flavor: a "book" on a shelf)."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(
        ForeignKey("lists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ItemStatus] = mapped_column(
        SAEnum(
            ItemStatus,
            name="item_status",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=ItemStatus.TO_READ,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    list: Mapped["ListModel"] = relationship("List", back_populates="items")
