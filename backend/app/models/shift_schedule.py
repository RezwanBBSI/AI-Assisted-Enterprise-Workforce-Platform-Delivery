import uuid
from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ShiftSchedule(Base):
    __tablename__ = "shift_schedules"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    shift_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    shift_start: Mapped[datetime] = mapped_column(Time, nullable=False)
    shift_end: Mapped[datetime] = mapped_column(Time, nullable=False)
    break_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    employee: Mapped["User"] = relationship("User", foreign_keys=[employee_id])  # noqa: F821
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by])  # noqa: F821
    location: Mapped["Location | None"] = relationship("Location")  # noqa: F821
    company: Mapped["Company"] = relationship("Company")  # noqa: F821
