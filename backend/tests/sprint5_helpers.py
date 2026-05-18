"""
Sprint 5 test fixtures: extend Sprint 4 seed with data that triggers compliance
violations and attendance exceptions.

Pay period used throughout Sprint 5 tests: 2026-06-01 → 2026-06-07
"""
from datetime import date, datetime, time

from app.models.attendance_record import AttendanceRecord
from app.models.shift_schedule import ShiftSchedule
from app.models.time_entry import TimeEntry
from tests.sprint4_helpers import _seed_sprint4


async def _seed_sprint5(db_session, client) -> dict:
    """Extend _seed_sprint4 with Sprint 5 compliance/reporting data."""
    ctx = await _seed_sprint4(db_session, client)

    employee_id = ctx["users"]["Employee"]
    company_id = ctx["company_id"]
    location_id = ctx["location_id"]

    # Sprint 5 pay period (separate from Sprint 4's May period)
    s5_pay_start = date(2026, 6, 1)
    s5_pay_end = date(2026, 6, 7)

    # ── Trigger: missing_punch ────────────────────────────────────────────────
    # Open time entry within the pay period (no clock_out)
    te_open = TimeEntry(
        employee_id=employee_id,
        company_id=company_id,
        location_id=location_id,
        clock_in=datetime(2026, 6, 2, 9, 0, 0),
        clock_out=None,
        status="open",
        break_minutes=0,
    )
    db_session.add(te_open)

    # ── Trigger: mandatory_break ──────────────────────────────────────────────
    # 9-hour shift with no break_minutes scheduled
    shift_long = ShiftSchedule(
        employee_id=employee_id,
        company_id=company_id,
        location_id=location_id,
        shift_date=date(2026, 6, 3),
        shift_start=time(9, 0),
        shift_end=time(18, 0),
        break_minutes=0,
    )
    db_session.add(shift_long)

    # ── A short shift (≤6 hrs) with no break — should NOT trigger violation ──
    shift_short = ShiftSchedule(
        employee_id=employee_id,
        company_id=company_id,
        location_id=location_id,
        shift_date=date(2026, 6, 4),
        shift_start=time(9, 0),
        shift_end=time(15, 0),
        break_minutes=0,
    )
    db_session.add(shift_short)

    # ── Trigger: attendance exception (absent) ────────────────────────────────
    att_absent = AttendanceRecord(
        employee_id=employee_id,
        company_id=company_id,
        date=date(2026, 6, 5),
        status="absent",
    )
    db_session.add(att_absent)

    # ── Trigger: attendance exception (late) ─────────────────────────────────
    att_late = AttendanceRecord(
        employee_id=employee_id,
        company_id=company_id,
        date=date(2026, 6, 6),
        status="late",
    )
    db_session.add(att_late)

    # ── Present record (should NOT appear in exceptions) ─────────────────────
    att_present = AttendanceRecord(
        employee_id=employee_id,
        company_id=company_id,
        date=date(2026, 6, 1),
        status="present",
    )
    db_session.add(att_present)

    # ── Closed time entry matching long shift (for crosscheck tests) ─────────
    # Same date as shift_long (2026-06-03) but only 4 hours → hours_mismatch
    te_short_actual = TimeEntry(
        employee_id=employee_id,
        company_id=company_id,
        location_id=location_id,
        clock_in=datetime(2026, 6, 3, 9, 0, 0),
        clock_out=datetime(2026, 6, 3, 13, 0, 0),
        status="closed",
        break_minutes=0,
    )
    db_session.add(te_short_actual)

    await db_session.commit()

    ctx["s5_pay_start"] = s5_pay_start
    ctx["s5_pay_end"] = s5_pay_end
    ctx["s5_te_open_id"] = te_open.id
    ctx["s5_shift_long_id"] = shift_long.id
    ctx["s5_shift_short_id"] = shift_short.id

    return ctx


__all__ = ["_seed_sprint5"]
