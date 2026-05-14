from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.company import Company
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.auth import RegisterRequest

_DEFAULT_COMPANY = "BBSI Demo"


class AuthService:
    """Handles user registration and credential verification."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(self, payload: RegisterRequest) -> User:
        """Create a new user and auto-assign the Employee role if seeded.

        Raises ValueError if email already taken.
        """
        existing = await self._db.execute(
            select(User).where(User.email == payload.email)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("Email already registered")

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        self._db.add(user)
        await self._db.flush()  # populate user.id before creating UserRole

        # Auto-assign Employee role in the default company if both exist.
        # Silent no-op when the database has not been seeded yet (e.g. in tests).
        role_result = await self._db.execute(
            select(Role).where(Role.name == "Employee")
        )
        role = role_result.scalar_one_or_none()
        company_result = await self._db.execute(
            select(Company).where(Company.name == _DEFAULT_COMPANY)
        )
        company = company_result.scalar_one_or_none()
        if role is not None and company is not None:
            self._db.add(
                UserRole(user_id=user.id, company_id=company.id, role_id=role.id)
            )

        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def authenticate(self, email: str, password: str) -> User | None:
        """Return User if credentials are valid, else None."""
        result = await self._db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        return create_access_token(subject=user.id)
