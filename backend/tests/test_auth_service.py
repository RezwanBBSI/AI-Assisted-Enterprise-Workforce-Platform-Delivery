"""Tests for AuthService — targeting 100% branch coverage."""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService


# ── register ──────────────────────────────────────────────────────────────────

async def test_register_creates_user(db_session: AsyncSession):
    svc = AuthService(db_session)
    payload = RegisterRequest(email="alice@example.com", password="secret123", full_name="Alice")
    user = await svc.register(payload)
    assert user.id is not None
    assert user.email == "alice@example.com"
    assert user.hashed_password != "secret123"  # must be hashed


async def test_register_duplicate_email_raises(db_session: AsyncSession):
    svc = AuthService(db_session)
    payload = RegisterRequest(email="dup@example.com", password="pass", full_name="Dup")
    await svc.register(payload)
    with pytest.raises(ValueError, match="already registered"):
        await svc.register(payload)


# ── authenticate ─────────────────────────────────────────────────────────────

async def test_authenticate_valid_credentials(db_session: AsyncSession):
    svc = AuthService(db_session)
    await svc.register(RegisterRequest(email="bob@example.com", password="mypass", full_name="Bob"))
    user = await svc.authenticate("bob@example.com", "mypass")
    assert user is not None
    assert user.email == "bob@example.com"


async def test_authenticate_wrong_password(db_session: AsyncSession):
    svc = AuthService(db_session)
    await svc.register(RegisterRequest(email="carol@example.com", password="correct", full_name="Carol"))
    result = await svc.authenticate("carol@example.com", "wrong")
    assert result is None


async def test_authenticate_unknown_email(db_session: AsyncSession):
    svc = AuthService(db_session)
    result = await svc.authenticate("nobody@example.com", "pass")
    assert result is None


async def test_authenticate_inactive_user(db_session: AsyncSession):
    svc = AuthService(db_session)
    user = await svc.register(RegisterRequest(email="inactive@example.com", password="pass", full_name="Off"))
    user.is_active = False
    await db_session.commit()
    result = await svc.authenticate("inactive@example.com", "pass")
    assert result is None


# ── issue_token ───────────────────────────────────────────────────────────────

async def test_issue_token_returns_string(db_session: AsyncSession):
    svc = AuthService(db_session)
    user = await svc.register(RegisterRequest(email="tok@example.com", password="p", full_name="T"))
    token = AuthService.issue_token(user)
    assert isinstance(token, str)
    assert len(token) > 20
