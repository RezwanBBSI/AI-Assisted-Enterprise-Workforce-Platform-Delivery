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
from datetime import date, time, timedelta

sys.path.insert(0, ".")  # allow running from backend/

from sqlalchemy import select, text

from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.models.company import Company  # noqa: F401 — ensures table registered
from app.models.leave_balance import LeaveBalance  # noqa: F401
from app.models.leave_request import LeaveRequest  # noqa: F401
from app.models.location import Location  # noqa: F401
from app.models.role import Role
from app.models.shift_schedule import ShiftSchedule  # noqa: F401
from app.models.user import User
from app.models.user_role import UserRole


ROLE_NAMES = ["Admin", "Manager", "Employee"]
DEFAULT_COMPANY = "BBSI Demo"

# Default demo location for the BBSI Demo company.
DEFAULT_LOCATION = {
    "name": "BBSI Vancouver HQ",
    "address_line_1": "805 Broadway St",
    "city": "Vancouver",
    "state": "WA",
    "zip_code": "98660",
    "country": "US",
    "timezone": "America/Los_Angeles",
}

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


async def seed_default_location(db, company: Company) -> None:
    """Create the default HQ location under the default company if not present."""
    result = await db.execute(
        select(Location).where(
            Location.company_id == company.id,
            Location.name == DEFAULT_LOCATION["name"],
        )
    )
    location = result.scalar_one_or_none()
    if location is None:
        location = Location(company_id=company.id, **DEFAULT_LOCATION)
        db.add(location)
        await db.flush()
        print(
            f"  [+] Created location: {DEFAULT_LOCATION['name']}  "
            f"({DEFAULT_LOCATION['city']}, {DEFAULT_LOCATION['state']})"
        )
    else:
        print(f"  [=] Location already exists: {DEFAULT_LOCATION['name']}")


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


async def seed_demo_data(db, company: Company) -> None:
    """Seed realistic demo data: leave balances, leave requests, and schedules.
    Skipped if data already exists.
    """
    # Look up users
    result = await db.execute(select(User).where(User.email.in_([
        "admin@bbsi.demo", "manager@bbsi.demo", "employee@bbsi.demo"
    ])))
    users = {u.email: u for u in result.scalars().all()}
    emp = users.get("employee@bbsi.demo")
    mgr = users.get("manager@bbsi.demo")
    admin = users.get("admin@bbsi.demo")
    if not emp or not mgr or not admin:
        print("  [!] Demo users missing, skipping demo data.")
        return

    # Get location
    loc_result = await db.execute(select(Location).where(Location.company_id == company.id))
    location = loc_result.scalar_one_or_none()

    today = date.today()
    year = today.year

    # ── Leave balances ────────────────────────────────────────────────────────
    for user, pto, sick, comp in [
        (emp,   80.0, 40.0, 8.0),
        (mgr,   80.0, 40.0, 0.0),
        (admin, 80.0, 40.0, 0.0),
    ]:
        existing = await db.execute(select(LeaveBalance).where(
            LeaveBalance.employee_id == user.id,
            LeaveBalance.company_id == company.id,
            LeaveBalance.year == year,
        ))
        bal = existing.scalar_one_or_none()
        if bal is None:
            db.add(LeaveBalance(
                employee_id=user.id, company_id=company.id, year=year,
                pto_total=pto, pto_used=8.0,
                sick_total=sick, sick_used=0.0,
                comp_earned=comp, comp_used=0.0,
            ))
            print(f"  [+] Leave balance created for {user.email}")
        else:
            # Update to non-zero values if still at defaults
            if bal.pto_total == 0.0:
                bal.pto_total = pto
                bal.sick_total = sick
                bal.comp_earned = comp
                print(f"  [~] Leave balance updated for {user.email}")
            else:
                print(f"  [=] Leave balance already set for {user.email}")

    # ── Leave requests ────────────────────────────────────────────────────────
    pending_count = (await db.execute(select(LeaveRequest).where(
        LeaveRequest.company_id == company.id, LeaveRequest.status == "pending"
    ))).scalars().all()
    if not pending_count:
        next_mon = today + timedelta(days=(7 - today.weekday()))  # next Monday
        db.add(LeaveRequest(
            employee_id=emp.id, company_id=company.id,
            leave_type="pto", days_requested=2,
            start_date=next_mon, end_date=next_mon + timedelta(days=1),
            reason="Family appointment", status="pending",
        ))
        db.add(LeaveRequest(
            employee_id=mgr.id, company_id=company.id,
            leave_type="sick", days_requested=1,
            start_date=today - timedelta(days=3), end_date=today - timedelta(days=3),
            reason="Sick day", status="approved",
            reviewed_by=admin.id, review_comment="Approved",
        ))
        print("  [+] Demo leave requests created")
    else:
        print("  [=] Leave requests already exist")

    # ── Schedules (shifts for next week) ──────────────────────────────────────
    shift_count = (await db.execute(select(ShiftSchedule).where(
        ShiftSchedule.company_id == company.id,
        ShiftSchedule.shift_date >= today,
    ))).scalars().all()
    if not shift_count:
        next_mon = today + timedelta(days=(7 - today.weekday()))
        loc_id = location.id if location else None
        for i, (user, s, e) in enumerate([
            (emp,   time(9, 0),  time(17, 0)),
            (emp,   time(9, 0),  time(17, 0)),
            (emp,   time(9, 0),  time(17, 0)),
            (mgr,   time(8, 0),  time(16, 0)),
            (mgr,   time(8, 0),  time(16, 0)),
            (admin, time(10, 0), time(18, 0)),
        ]):
            day = next_mon + timedelta(days=i % 5)
            db.add(ShiftSchedule(
                employee_id=user.id, company_id=company.id,
                location_id=loc_id, shift_date=day,
                shift_start=s, shift_end=e, break_minutes=30,
                created_by=admin.id,
            ))
        print("  [+] Demo shifts created for next week")
    else:
        print("  [=] Future shifts already exist")


async def run(email: str | None, role_name: str, reset: bool) -> None:
    if reset:
        await reset_db()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("\nSeeding roles and company...")
        roles, company = await seed_roles_and_company(db)

        print("\nSeeding default location...")
        await seed_default_location(db, company)

        print("\nSeeding default demo users...")
        await seed_default_users(db, roles, company)

        print("\nSeeding demo data (balances, leave requests, schedules)...")
        await seed_demo_data(db, company)

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
