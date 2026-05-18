"""
Shared Sprint 4 fixture: extends Sprint 3 seed with closed TimeEntry rows
spanning scenarios needed by payroll calculation tests, plus approved leave.
"""
from datetime import date, datetime, timedelta

from app.core.security import hash_password
from app.models.company_policy import CompanyPolicy
from app.models.leave_request import LeaveRequest
from app.models.time_entry import TimeEntry
from tests.sprint3_helpers import _seed_sprint3


async def _seed_sprint4(db_session, client) -> dict:
    """Extend _seed_sprint3 context with time entries and approved leave."""
    ctx = await _seed_sprint3(db_session, client)

    employee_id = ctx["users"]["Employee"]
    company_id = ctx["company_id"]
    location_id = ctx["location_id"]

    # Pay period: Mon 2026-05-11 → Sun 2026-05-17
    pay_start = date(2026, 5, 11)
    pay_end = date(2026, 5, 17)

    # Day 1 (Mon 2026-05-11): normal 8-hour day → all regular
    # clock_in 08:00, clock_out 16:00
    te_normal = TimeEntry(
        employee_id=employee_id,
        company_id=company_id,
        location_id=location_id,
        clock_in=datetime(2026, 5, 11, 8, 0, 0),
        clock_out=datetime(2026, 5, 11, 16, 0, 0),
        status="closed",
        break_minutes=0,
    )
    db_session.add(te_normal)

    # Day 2 (Tue 2026-05-12): 10-hour day → 8 regular + 2 OT (1.5×)
    # clock_in 08:00, clock_out 18:00
    te_daily_ot = TimeEntry(
        employee_id=employee_id,
        company_id=company_id,
        location_id=location_id,
        clock_in=datetime(2026, 5, 12, 8, 0, 0),
        clock_out=datetime(2026, 5, 12, 18, 0, 0),
        status="closed",
        break_minutes=0,
    )
    db_session.add(te_daily_ot)

    # Day 3 (Wed 2026-05-13): 14-hour day → 8 regular + 4 OT + 2 double (2.0×)
    # clock_in 08:00, clock_out 22:00
    te_double = TimeEntry(
        employee_id=employee_id,
        company_id=company_id,
        location_id=location_id,
        clock_in=datetime(2026, 5, 13, 8, 0, 0),
        clock_out=datetime(2026, 5, 13, 22, 0, 0),
        status="closed",
        break_minutes=0,
    )
    db_session.add(te_double)

    # Day 4 (Thu 2026-05-14): night-shift — 22:00 Thu → 06:00 Fri (8 hrs)
    # All 8 hours fall in the night differential window (22:00–06:00)
    te_night = TimeEntry(
        employee_id=employee_id,
        company_id=company_id,
        location_id=location_id,
        clock_in=datetime(2026, 5, 14, 22, 0, 0),
        clock_out=datetime(2026, 5, 15, 6, 0, 0),
        status="closed",
        break_minutes=0,
    )
    db_session.add(te_night)

    # Add holiday policy so Day 3 (2026-05-13) acts as a holiday in holiday tests
    # (used only in test_payroll_calculation.py unit tests — not injected here globally)

    # Add payroll-specific policies
    for key, value in [
        ("ot_daily_threshold", "8"),
        ("ot_double_threshold", "12"),
        ("weekly_ot_threshold", "40"),
        ("night_diff_start", '"22:00"'),
        ("night_diff_end", '"06:00"'),
    ]:
        db_session.add(CompanyPolicy(
            company_id=company_id,
            policy_key=key,
            policy_value=value,
        ))

    # Approved PTO leave: Fri 2026-05-15 (1 day)
    leave = LeaveRequest(
        employee_id=employee_id,
        company_id=company_id,
        leave_type="pto",
        start_date=date(2026, 5, 15),
        end_date=date(2026, 5, 15),
        days_requested=1.0,
        status="approved",
        reason="Vacation",
    )
    db_session.add(leave)

    await db_session.commit()

    ctx["pay_start"] = pay_start
    ctx["pay_end"] = pay_end
    ctx["time_entry_ids"] = {
        "normal": te_normal.id,
        "daily_ot": te_daily_ot.id,
        "double": te_double.id,
        "night": te_night.id,
    }
    ctx["leave_id"] = leave.id
    return ctx


__all__ = ["_seed_sprint4"]
