"""Tests for auth HTTP endpoints — register, login, refresh, me."""
import pytest
from httpx import AsyncClient


# ── register ──────────────────────────────────────────────────────────────────

async def test_register_201(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "password": "pass123",
        "full_name": "Alice",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert "hashed_password" not in data


async def test_register_duplicate_409(client: AsyncClient):
    body = {"email": "dup@example.com", "password": "p", "full_name": "D"}
    await client.post("/api/v1/auth/register", json=body)
    resp = await client.post("/api/v1/auth/register", json=body)
    assert resp.status_code == 409


# ── login ─────────────────────────────────────────────────────────────────────

async def test_login_returns_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "bob@example.com", "password": "secret", "full_name": "Bob"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "bob@example.com", "password": "secret"
    })
    assert resp.status_code == 200
    assert resp.json()["access_token"]
    assert resp.json()["token_type"] == "bearer"


async def test_login_wrong_password_401(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "carol@example.com", "password": "right", "full_name": "Carol"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "carol@example.com", "password": "wrong"
    })
    assert resp.status_code == 401


async def test_login_unknown_email_401(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "ghost@example.com", "password": "x"
    })
    assert resp.status_code == 401


# ── me ────────────────────────────────────────────────────────────────────────

async def _register_and_login(client: AsyncClient, email: str) -> str:
    await client.post("/api/v1/auth/register", json={
        "email": email, "password": "pw", "full_name": "User"
    })
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "pw"})
    return resp.json()["access_token"]


async def test_me_returns_current_user(client: AsyncClient):
    token = await _register_and_login(client, "me@example.com")
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


async def test_me_no_token_401(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_invalid_token_401(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401


# ── refresh ───────────────────────────────────────────────────────────────────

async def test_refresh_returns_new_token(client: AsyncClient):
    token = await _register_and_login(client, "refresh@example.com")
    resp = await client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


# ── expired token ──────────────────────────────────────────────────────────────

async def test_expired_token_returns_401(client: AsyncClient):
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.core.config import settings

    expired_token = jwt.encode(
        {"sub": "fake-user-id", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    # Bearer scheme is valid so HTTPBearer passes through; JWTError → 401
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
