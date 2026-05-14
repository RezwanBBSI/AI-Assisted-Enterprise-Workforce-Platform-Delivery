import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "company_id", "date", name="uq_attendance_emp_company_date"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    # status: present | absent | late | missing_punch
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    time_entry_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("time_entries.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    employee: Mapped["User"] = relationship("User")  # noqa: F821
    company: Mapped["Company"] = relationship("Company")  # noqa: F821
    time_entry: Mapped["TimeEntry | None"] = relationship("TimeEntry")  # noqa: F821
