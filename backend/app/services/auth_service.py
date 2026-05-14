from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


class AuthService:
    """Handles user registration and credential verification."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(self, payload: RegisterRequest) -> User:
        """Create a new user.  Raises ValueError if email already taken."""
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
