import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimeEntry(Base):
    __tablename__ = "time_entries"

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
    clock_in: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    clock_out: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # status: open | closed | corrected
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    break_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    employee: Mapped["User"] = relationship("User", foreign_keys=[employee_id])  # noqa: F821
    company: Mapped["Company"] = relationship("Company")  # noqa: F821
    location: Mapped["Location | None"] = relationship("Location")  # noqa: F821
    corrections: Mapped[list["TimeCorrection"]] = relationship(  # noqa: F821
        "TimeCorrection", back_populates="time_entry", cascade="all, delete-orphan"
    )
