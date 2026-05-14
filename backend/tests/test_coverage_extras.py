"""Targeted tests for deps.py branches not covered by other test modules."""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService


def _make_token(sub: str | None, *, expired: bool = False) -> str:
    payload: dict = {}
    if sub is not None:
        payload["sub"] = sub
    exp = datetime.now(timezone.utc) + (
        timedelta(hours=-1) if expired else timedelta(minutes=60)
    )
    payload["exp"] = exp
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── No 'sub' in token payload ─────────────────────────────────────────────────

async def test_no_sub_in_token_returns_401(client: AsyncClient):
    """Token decodes fine but has no 'sub' claim → 401."""
    token = _make_token(sub=None)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# ── Valid token but user no longer exists in DB ───────────────────────────────

async def test_deleted_user_token_returns_401(client: AsyncClient):
    """Token is cryptographically valid but points to an unknown user ID → 401."""
    token = _make_token(sub="00000000-0000-0000-0000-000000000000")
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# ── POST /companies (Admin creates company) ───────────────────────────────────

async def _make_admin_token(db: AsyncSession, email: str) -> str:
    from app.models.company import Company
    from app.models.role import Role
    from app.models.user_role import UserRole
    from sqlalchemy import select

    svc = AuthService(db)
    user = await svc.register(RegisterRequest(email=email, password="pw", full_name="Admin"))
    token = AuthService.issue_token(user)

    result = await db.execute(select(Role).where(Role.name == "Admin"))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name="Admin")
        db.add(role)
        await db.flush()

    company = Company(name="Seed Co")
    db.add(company)
    await db.flush()
    db.add(UserRole(user_id=user.id, company_id=company.id, role_id=role.id))
    await db.commit()
    return token


async def test_create_company(client: AsyncClient, db_session: AsyncSession):
    token = await _make_admin_token(db_session, "admin1@example.com")
    resp = await client.post(
        "/api/v1/companies",
        json={"name": "Acme Corp"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Acme Corp"


async def test_list_companies_pagination(client: AsyncClient, db_session: AsyncSession):
    token = await _make_admin_token(db_session, "admin2@example.com")
    # Create 3 companies
    for i in range(3):
        await client.post(
            "/api/v1/companies",
            json={"name": f"Co {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
    resp = await client.get(
        "/api/v1/companies?page=1&size=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 3  # includes the seed company
    assert len(data["items"]) == 2
    assert data["page"] == 1


# ── POST /locations (Admin creates location) ──────────────────────────────────

async def test_create_location(client: AsyncClient, db_session: AsyncSession):
    token = await _make_admin_token(db_session, "admin3@example.com")

    # First create a company to get its id
    create_resp = await client.post(
        "/api/v1/companies",
        json={"name": "Location Co"},
        headers={"Authorization": f"Bearer {token}"},
    )
    company_id = create_resp.json()["id"]

    resp = await client.post(
        "/api/v1/locations",
        json={"company_id": company_id, "name": "HQ", "timezone": "America/New_York"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "HQ"
    assert resp.json()["timezone"] == "America/New_York"


async def test_list_locations_filtered_by_company(client: AsyncClient, db_session: AsyncSession):
    token = await _make_admin_token(db_session, "admin4@example.com")

    create_resp = await client.post(
        "/api/v1/companies",
        json={"name": "Filter Co"},
        headers={"Authorization": f"Bearer {token}"},
    )
    company_id = create_resp.json()["id"]

    await client.post(
        "/api/v1/locations",
        json={"company_id": company_id, "name": "Branch A", "timezone": "UTC"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(
        f"/api/v1/locations?company_id={company_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Branch A"
