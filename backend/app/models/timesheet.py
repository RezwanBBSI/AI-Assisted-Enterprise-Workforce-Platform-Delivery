import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Timesheet(Base):
    __tablename__ = "timesheets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pay_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    pay_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    # status: draft | submitted | approved | exported
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    total_regular_hrs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_ot_hrs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_holiday_hrs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_differential_hrs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    employee: Mapped["User"] = relationship("User", foreign_keys=[employee_id])  # noqa: F821
    approver: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by])  # noqa: F821
    company: Mapped["Company"] = relationship("Company")  # noqa: F821
    line_items: Mapped[list["PayrollLineItem"]] = relationship(  # noqa: F821
        "PayrollLineItem", back_populates="timesheet", cascade="all, delete-orphan"
    )
