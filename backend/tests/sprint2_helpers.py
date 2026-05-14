"""
Shared Sprint 2 fixture: seeds roles, company, location, and 3 users with roles
then returns a dict of JWT tokens keyed by role name.
"""
import pytest_asyncio
from httpx import AsyncClient

from app.models.company import Company
from app.models.location import Location
from app.models.role import Role, RoleName
from app.models.user import User
from app.models.user_role import UserRole
from app.core.security import hash_password


async def _seed_sprint2(db_session, client: AsyncClient) -> dict:
    """Create company, location, 3 users; return {role: token} mapping."""
    # Roles
    roles = {}
    for rn in RoleName:
        r = Role(name=rn.value)
        db_session.add(r)
        roles[rn.value] = r
    await db_session.flush()

    # Company
    company = Company(name="Test Corp", is_active=True)
    db_session.add(company)
    await db_session.flush()

    # Location
    location = Location(
        company_id=company.id,
        name="HQ",
        timezone="America/Los_Angeles",
        is_active=True,
    )
    db_session.add(location)
    await db_session.flush()

    # Users
    users = {}
    for role_name, email, pw in [
        ("Admin", "admin@test.com", "Admin1234!"),
        ("Manager", "manager@test.com", "Manager1234!"),
        ("Employee", "employee@test.com", "Employee1234!"),
    ]:
        u = User(email=email, hashed_password=hash_password(pw), full_name=f"Test {role_name}", is_active=True)
        db_session.add(u)
        await db_session.flush()
        ur = UserRole(user_id=u.id, company_id=company.id, role_id=roles[role_name].id)
        db_session.add(ur)
        users[role_name] = u

    await db_session.commit()

    # Get tokens via login endpoint
    tokens = {}
    for role_name, email, pw in [
        ("Admin", "admin@test.com", "Admin1234!"),
        ("Manager", "manager@test.com", "Manager1234!"),
        ("Employee", "employee@test.com", "Employee1234!"),
    ]:
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
        assert resp.status_code == 200, f"Login failed for {role_name}: {resp.text}"
        tokens[role_name] = resp.json()["access_token"]

    return {
        "tokens": tokens,
        "company_id": company.id,
        "location_id": location.id,
        "users": {k: v.id for k, v in users.items()},
    }


# Re-export so tests can import from here
__all__ = ["_seed_sprint2"]
