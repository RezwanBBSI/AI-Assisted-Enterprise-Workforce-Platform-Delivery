from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", "role_id", name="uq_user_company_role"),
    )

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company_id: Mapped[str] = mapped_column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_roles")  # noqa: F821
    company: Mapped["Company"] = relationship("Company", back_populates="user_roles")  # noqa: F821
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")  # noqa: F821
