import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PayrollLineItem(Base):
    __tablename__ = "payroll_line_items"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    timesheet_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("timesheets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours_worked: Mapped[float] = mapped_column(Float, nullable=False)
    # rate_type: regular | overtime | double_time | holiday | night_differential | pto | comp
    rate_type: Mapped[str] = mapped_column(String(24), nullable=False)
    rate_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    timesheet: Mapped["Timesheet"] = relationship("Timesheet", back_populates="line_items")  # noqa: F821
