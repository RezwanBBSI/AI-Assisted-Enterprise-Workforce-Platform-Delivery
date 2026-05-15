import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CompanyPolicy(Base):
    __tablename__ = "company_policies"
    __table_args__ = (
        UniqueConstraint("company_id", "policy_key", name="uq_company_policy_key"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    policy_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    policy_value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company")  # noqa: F821
    updater: Mapped["User | None"] = relationship("User")  # noqa: F821
