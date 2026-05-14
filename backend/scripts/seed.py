"""
Database seed script — populates roles, a default company, default demo users,
and optionally assigns a role to any existing user.

Usage (from the backend/ directory):
    source venv/bin/activate

    # Full seed (roles + company + demo users):
    python scripts/seed.py

    # Seed and also make YOUR registered user an Admin:
    python scripts/seed.py --email you@example.com --role Admin

    # Wipe all data and re-seed from scratch (DEV ONLY):
    python scripts/seed.py --reset

Default demo credentials created automatically:
    admin@bbsi.demo    / Admin1234!     → Admin role
    manager@bbsi.demo  / Manager1234!   → Manager role
    employee@bbsi.demo / Employee1234!  → Employee role
"""
import argparse
import asyncio
import sys

sys.path.insert(0, ".")  # allow running from backend/

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.models.company import Company  # noqa: F401 — ensures table registered
from app.models.location import Location  # noqa: F401
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole


ROLE_NAMES = ["Admin", "Manager", "Employee"]
DEFAULT_COMPANY = "BBSI Demo"

# Default demo users created during seeding.
# Format: (email, plaintext_password, role_name)
DEFAULT_USERS = [
    ("admin@bbsi.demo", "Admin1234!", "Admin"),
    ("manager@bbsi.demo", "Manager1234!", "Manager"),
    ("employee@bbsi.demo", "Employee1234!", "Employee"),
]


async def reset_db() -> None:
    """Drop all tables and recreate them (destructive — dev only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("  [!] Database reset — all tables dropped and recreated.")


async def seed_roles_and_company(db) -> tuple[dict[str, Role], Company]:
    """Ensure all three roles and the default company exist. Returns both."""
    roles: dict[str, Role] = {}
    for name in ROLE_NAMES:
        result = await db.execute(select(Role).where(Role.name == name))
        role = result.scalar_one_or_none()
        if role is None:
            role = Role(name=name)
            db.add(role)
            await db.flush()
            print(f"  [+] Created role: {name}")
        else:
            print(f"  [=] Role already exists: {name}")
        roles[name] = role

    result = await db.execute(select(Company).where(Company.name == DEFAULT_COMPANY))
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(name=DEFAULT_COMPANY)
        db.add(company)
        await db.flush()
        print(f"  [+] Created company: {DEFAULT_COMPANY}  (id={company.id})")
    else:
        print(f"  [=] Company already exists: {DEFAULT_COMPANY}  (id={company.id})")

    return roles, company


async def assign_role(db, email: str, role_name: str, roles: dict, company: Company) -> None:
    """Assign *role_name* to the user with *email* in the default company."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        print(f"\n  [!] No user found with email: {email}")
        print("      Register first via POST /api/v1/auth/register, then re-run this script.")
        return

    role = roles.get(role_name)
    if role is None:
        print(f"  [!] Unknown role: {role_name}")
        return

    existing = await db.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.company_id == company.id,
            UserRole.role_id == role.id,
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(UserRole(user_id=user.id, company_id=company.id, role_id=role.id))
        print(f"  [+] Assigned {role_name} role to {email} in '{DEFAULT_COMPANY}'")
    else:
        print(f"  [=] {email} already has {role_name} role in '{DEFAULT_COMPANY}'")


async def seed_default_users(db, roles: dict, company: Company) -> None:
    """Create the three default demo users if they don't already exist."""
    for email, password, role_name in DEFAULT_USERS:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                full_name=role_name,  # e.g. "Admin", "Manager", "Employee"
            )
            db.add(user)
            await db.flush()
            print(f"  [+] Created user: {email}  (password: {password})")
        else:
            print(f"  [=] User already exists: {email}")

        await assign_role(db, email, role_name, roles, company)


async def run(email: str | None, role_name: str, reset: bool) -> None:
    if reset:
        await reset_db()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("\nSeeding roles and company...")
        roles, company = await seed_roles_and_company(db)

        print("\nSeeding default demo users...")
        await seed_default_users(db, roles, company)

        if email:
            print(f"\nAssigning {role_name} to {email}...")
            await assign_role(db, email, role_name, roles, company)

        await db.commit()

    print("\nSeed complete.")
    print(f"  → Demo users: admin@bbsi.demo / manager@bbsi.demo / employee@bbsi.demo")
    print(f"  → Passwords: Admin1234! / Manager1234! / Employee1234!")
    if email:
        print(f"  → Also assigned {role_name} to {email}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the workforce platform database.")
    parser.add_argument("--email", default=None, help="User email to assign a role to")
    parser.add_argument(
        "--role",
        default="Admin",
        choices=ROLE_NAMES,
        help="Role to assign (default: Admin)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables and recreate before seeding (DEV ONLY — destructive!)",
    )
    args = parser.parse_args()
    asyncio.run(run(email=args.email, role_name=args.role, reset=args.reset))
