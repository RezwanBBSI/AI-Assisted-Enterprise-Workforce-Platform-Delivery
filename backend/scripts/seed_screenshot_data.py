"""
seed_screenshot_data.py — creates rich demo data for screenshots.

Workflow:
  1. Log in as employee → create 10 days of clock-in/out entries
  2. Log in as manager  → generate timesheets for employee + manager, approve them
  3. Create compliance violations directly in DB
  4. Create some correction requests

Usage (from backend/ directory):
    source venv/bin/activate
    python scripts/seed_screenshot_data.py
"""
import asyncio
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, ".")

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.attendance_record import AttendanceRecord
from app.models.compliance_violation import ComplianceViolation
from app.models.time_entry import TimeEntry
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.user_role import UserRole


# ── helpers ────────────────────────────────────────────────────────────────

async def get_user(db, email: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one()


async def get_company_id(db, email: str) -> str:
    user = await get_user(db, email)
    result = await db.execute(select(UserRole).where(UserRole.user_id == user.id))
    ur = result.scalar_one()
    return str(ur.company_id)


# ── time entries ────────────────────────────────────────────────────────────

async def seed_time_entries(db, user: User, company_id: str, start_date: date, days: int):
    """Create clock-in/out pairs for `days` working days starting at start_date."""
    from app.models.location import Location
    loc_result = await db.execute(
        select(Location).where(Location.company_id == company_id)
    )
    location = loc_result.scalar_one_or_none()
    loc_id = str(location.id) if location else None

    created = 0
    d = start_date
    for _ in range(days):
        # Skip weekends
        while d.weekday() >= 5:
            d += timedelta(days=1)

        # 8h shift with a 30m lunch gap split into two entries
        clock_in  = datetime(d.year, d.month, d.day, 9, 0, 0)
        clock_out = datetime(d.year, d.month, d.day, 13, 0, 0)  # morning: 4h
        clock_in2 = datetime(d.year, d.month, d.day, 13, 30, 0)
        clock_out2 = datetime(d.year, d.month, d.day, 17, 30, 0)  # afternoon: 4h

        # Check not already existing
        existing = await db.execute(
            select(TimeEntry).where(
                TimeEntry.employee_id == user.id,
                TimeEntry.clock_in == clock_in,
            )
        )
        if existing.scalar_one_or_none() is None:
            e1 = TimeEntry(
                employee_id=str(user.id),
                company_id=company_id,
                location_id=loc_id,
                clock_in=clock_in,
                clock_out=clock_out,
                status="approved",
                break_minutes=0,
            )
            e2 = TimeEntry(
                employee_id=str(user.id),
                company_id=company_id,
                location_id=loc_id,
                clock_in=clock_in2,
                clock_out=clock_out2,
                status="approved",
                break_minutes=0,
            )
            db.add(e1)
            db.add(e2)
            created += 2

        d += timedelta(days=1)

    await db.commit()
    print(f"  → {created} time entries created for {user.email}")
    return d  # next available date


# ── timesheet lifecycle ─────────────────────────────────────────────────────

async def seed_timesheet(db, user: User, company_id: str, period_start: date, period_end: date):
    """Generate a timesheet from existing time entries and approve it."""
    from app.services.payroll_service import TimesheetService

    # Check if one already exists
    existing = await db.execute(
        select(Timesheet).where(
            Timesheet.employee_id == user.id,
            Timesheet.pay_period_start == period_start,
        )
    )
    ts = existing.scalar_one_or_none()

    if ts is None:
        svc = TimesheetService(db)
        ts = await svc.generate(
            employee_id=str(user.id),
            company_id=company_id,
            pay_period_start=period_start,
            pay_period_end=period_end,
            requested_by=str(user.id),
        )
        print(f"  → Timesheet generated for {user.email}: {period_start} → {period_end}")
    else:
        print(f"  → Timesheet already exists for {user.email}")

    # Submit then approve
    if ts.status == "draft":
        ts.status = "submitted"
        await db.commit()
        await db.refresh(ts)
        print(f"  → Timesheet submitted")

    if ts.status == "submitted":
        ts.status = "approved"
        await db.commit()
        await db.refresh(ts)
        print(f"  → Timesheet approved  (regular={ts.total_regular_hrs}h, ot={ts.total_ot_hrs}h)")

    return ts


# ── compliance violations ───────────────────────────────────────────────────

VIOLATION_SAMPLES = [
    {
        "violation_type": "missed_punch",
        "description": "Employee clocked in but no clock-out recorded for shift",
        "resolved": False,
    },
    {
        "violation_type": "overtime_threshold",
        "description": "Employee exceeded 40h/week — 6.5 hours of unplanned overtime",
        "resolved": False,
    },
    {
        "violation_type": "meal_break_violation",
        "description": "No meal break recorded during an 8-hour shift (required ≥30 min)",
        "resolved": True,
    },
    {
        "violation_type": "missed_punch",
        "description": "Clock-in outside scheduled shift window by 45 minutes",
        "resolved": True,
    },
    {
        "violation_type": "overtime_threshold",
        "description": "Manager shift exceeded daily 10-hour cap by 1.5 hours",
        "resolved": False,
    },
]


async def seed_violations(db, company_id: str, employee: User, manager: User):
    existing = await db.execute(
        select(ComplianceViolation).where(ComplianceViolation.company_id == company_id)
    )
    if existing.scalars().first() is not None:
        print("  → Violations already exist, skipping")
        return

    users = [employee, manager, employee, manager, employee]
    for i, sample in enumerate(VIOLATION_SAMPLES):
        dt = datetime(2026, 5, 1 + i * 3, 9, 0) + timedelta(days=i)
        v = ComplianceViolation(
            company_id=company_id,
            employee_id=str(users[i].id),
            occurred_at=dt,
            **sample,
        )
        db.add(v)

    await db.commit()
    print(f"  → {len(VIOLATION_SAMPLES)} compliance violations created")


# ── attendance records ──────────────────────────────────────────────────────

async def seed_attendance_records(db, employee: User, company_id: str, start_date: date, days: int):
    existing = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.employee_id == employee.id)
    )
    if existing.scalars().first() is not None:
        print("  → Attendance records already exist, skipping")
        return

    d = start_date
    created = 0
    for _ in range(days):
        while d.weekday() >= 5:
            d += timedelta(days=1)
        rec = AttendanceRecord(
            employee_id=str(employee.id),
            company_id=company_id,
            date=d,
            status="present",
        )
        db.add(rec)
        d += timedelta(days=1)
        created += 1
    await db.commit()
    print(f"  → {created} attendance records created")


# ── main ────────────────────────────────────────────────────────────────────

async def main():
    today = date.today()
    # Use May 2026 pay period (bi-weekly: May 1–14 and May 15–28)
    period1_start = date(2026, 5, 1)
    period1_end   = date(2026, 5, 14)
    period2_start = date(2026, 5, 15)
    period2_end   = date(2026, 5, 28)

    async with AsyncSessionLocal() as db:
        employee = await get_user(db, "employee@bbsi.demo")
        manager  = await get_user(db, "manager@bbsi.demo")
        company_id = await get_company_id(db, "employee@bbsi.demo")

        print(f"\nCompany: {company_id}")
        print(f"Employee: {employee.id}")
        print(f"Manager:  {manager.id}")

        print("\n[1] Seeding time entries — employee (May 1–14)…")
        await seed_time_entries(db, employee, company_id, period1_start, 10)

        print("\n[2] Seeding time entries — employee (May 15–28)…")
        await seed_time_entries(db, employee, company_id, period2_start, 10)

        print("\n[3] Seeding time entries — manager (May 1–14)…")
        await seed_time_entries(db, manager, company_id, period1_start, 10)

        print("\n[4] Generating + approving timesheet — employee period 1…")
        await seed_timesheet(db, employee, company_id, period1_start, period1_end)

        print("\n[5] Generating + approving timesheet — employee period 2…")
        await seed_timesheet(db, employee, company_id, period2_start, period2_end)

        print("\n[6] Generating + approving timesheet — manager period 1…")
        await seed_timesheet(db, manager, company_id, period1_start, period1_end)

        print("\n[7] Seeding compliance violations…")
        await seed_violations(db, company_id, employee, manager)

        print("\n[8] Seeding attendance records…")
        await seed_attendance_records(db, employee, company_id, period1_start, 20)

    print("\n✅ Screenshot data seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
