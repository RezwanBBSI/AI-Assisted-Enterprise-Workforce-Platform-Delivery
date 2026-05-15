import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "company_id", "year",
            name="uq_leave_balance_employee_company_year",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    pto_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    pto_used: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sick_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sick_used: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comp_earned: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comp_used: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    employee: Mapped["User"] = relationship("User", foreign_keys=[employee_id])  # noqa: F821
    company: Mapped["Company"] = relationship("Company")  # noqa: F821
