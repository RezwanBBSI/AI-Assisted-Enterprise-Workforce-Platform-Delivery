import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimeCorrection(Base):
    __tablename__ = "time_corrections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    time_entry_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("time_entries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    approved_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    original_clock_in: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    new_clock_in: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    original_clock_out: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    new_clock_out: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # status: pending | approved | denied
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    time_entry: Mapped["TimeEntry"] = relationship(  # noqa: F821
        "TimeEntry", back_populates="corrections"
    )
    requester: Mapped["User"] = relationship("User", foreign_keys=[requested_by])  # noqa: F821
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by])  # noqa: F821
