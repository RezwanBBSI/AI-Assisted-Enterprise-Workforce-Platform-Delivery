"""Tests for RBAC dependency — get_current_user and require_role."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.auth import RegisterRequest
from app.services.auth_service import AuthService


async def _create_user_with_role(db: AsyncSession, email: str, role_name: str) -> str:
    """Register a user, seed roles table, assign role, return JWT."""
    svc = AuthService(db)
    user = await svc.register(RegisterRequest(email=email, password="pw", full_name="Test"))
    token = AuthService.issue_token(user)

    # Ensure role row exists
    from sqlalchemy import select
    result = await db.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name=role_name)
        db.add(role)
        await db.flush()

    company = Company(name="Test Co")
    db.add(company)
    await db.flush()

    db.add(UserRole(user_id=user.id, company_id=company.id, role_id=role.id))
    await db.commit()

    return token


# ── Admin-only endpoint (GET /api/v1/companies) ───────────────────────────────

async def test_admin_can_access_companies(client: AsyncClient, db_session: AsyncSession):
    token = await _create_user_with_role(db_session, "admin@example.com", "Admin")
    resp = await client.get("/api/v1/companies", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


async def test_employee_forbidden_from_companies(client: AsyncClient, db_session: AsyncSession):
    token = await _create_user_with_role(db_session, "emp@example.com", "Employee")
    resp = await client.get("/api/v1/companies", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


async def test_unauthenticated_from_companies_401(client: AsyncClient):
    resp = await client.get("/api/v1/companies")
    assert resp.status_code == 401


# ── Locations (Admin OR Manager) ──────────────────────────────────────────────

async def test_manager_can_access_locations(client: AsyncClient, db_session: AsyncSession):
    token = await _create_user_with_role(db_session, "mgr@example.com", "Manager")
    resp = await client.get("/api/v1/locations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


async def test_employee_forbidden_from_locations(client: AsyncClient, db_session: AsyncSession):
    token = await _create_user_with_role(db_session, "emp2@example.com", "Employee")
    resp = await client.get("/api/v1/locations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
