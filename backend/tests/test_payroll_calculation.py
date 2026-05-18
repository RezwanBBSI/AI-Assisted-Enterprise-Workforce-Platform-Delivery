"""
Unit tests for PayrollCalculationService — 100% branch coverage required.

Tests use plain dicts / simple objects so no DB is needed.
"""
import json
from datetime import date, datetime, timedelta, time

import pytest

from app.services.payroll_calculation_service import PayrollCalculationService, _overlap_hours


# ── helpers ───────────────────────────────────────────────────────────────────

def _entry(clock_in: datetime, clock_out: datetime, break_minutes: int = 0) -> dict:
    return {
        "clock_in": clock_in,
        "clock_out": clock_out,
        "break_minutes": break_minutes,
    }


def _leave(leave_type: str, start: date, end: date) -> dict:
    return {"leave_type": leave_type, "start_date": start, "end_date": end}


def _items_by_type(items: list[dict], rate_type: str) -> list[dict]:
    return [i for i in items if i["rate_type"] == rate_type]


def _total(items: list[dict], rate_type: str) -> float:
    return sum(i["hours_worked"] for i in _items_by_type(items, rate_type))


svc = PayrollCalculationService()

# ── _overlap_hours ────────────────────────────────────────────────────────────

def test_overlap_hours_fully_inside_window():
    """Entry fully inside 22:00–06:00 → all hours counted."""
    ci = datetime(2026, 5, 14, 23, 0)
    co = datetime(2026, 5, 15, 2, 0)
    hours = _overlap_hours(ci, co, time(22, 0), time(6, 0))
    assert abs(hours - 3.0) < 1e-6


def test_overlap_hours_no_overlap():
    """Daytime entry → zero night overlap."""
    ci = datetime(2026, 5, 14, 9, 0)
    co = datetime(2026, 5, 14, 17, 0)
    hours = _overlap_hours(ci, co, time(22, 0), time(6, 0))
    assert hours == 0.0


# ── _classify_daily ───────────────────────────────────────────────────────────

def test_classify_daily_all_regular():
    """Exactly 8 hours → all regular, no OT."""
    reg, ot, double = PayrollCalculationService._classify_daily(8.0, 8.0, 12.0)
    assert reg == 8.0
    assert ot == 0.0
    assert double == 0.0


def test_classify_daily_with_ot():
    """10-hour day → 8 regular + 2 OT."""
    reg, ot, double = PayrollCalculationService._classify_daily(10.0, 8.0, 12.0)
    assert reg == 8.0
    assert ot == 2.0
    assert double == 0.0


def test_classify_daily_with_double_time():
    """14-hour day → 8 regular + 4 OT + 2 double-time."""
    reg, ot, double = PayrollCalculationService._classify_daily(14.0, 8.0, 12.0)
    assert reg == 8.0
    assert ot == 4.0
    assert double == 2.0


# ── Weekly OT ─────────────────────────────────────────────────────────────────

def test_weekly_ot_triggers_at_threshold():
    """5 × 9-hr days (45 hrs): first 40 hrs regular, last 5 hrs weekly OT."""
    entries = []
    for day_offset in range(5):
        d = date(2026, 5, 11) + timedelta(days=day_offset)
        ci = datetime.combine(d, datetime.min.time()).replace(hour=8)
        co = ci + timedelta(hours=9)
        entries.append(_entry(ci, co))

    items = svc.calculate(entries, [], {})
    assert abs(_total(items, "regular") - 40.0) < 1e-4
    assert abs(_total(items, "overtime") - 5.0) < 1e-4


def test_weekly_ot_not_triggered_under_threshold():
    """5 × 8-hr days (40 hrs): all regular, no weekly OT."""
    entries = []
    for day_offset in range(5):
        d = date(2026, 5, 11) + timedelta(days=day_offset)
        ci = datetime.combine(d, datetime.min.time()).replace(hour=8)
        co = ci + timedelta(hours=8)
        entries.append(_entry(ci, co))

    items = svc.calculate(entries, [], {})
    assert abs(_total(items, "regular") - 40.0) < 1e-4
    assert _total(items, "overtime") == 0.0


# ── Holiday ───────────────────────────────────────────────────────────────────

def test_holiday_multiplier_applied():
    """Entry on a holiday date → rate_type becomes 'holiday', multiplier 2.0."""
    ci = datetime(2026, 5, 25, 9, 0)  # Memorial Day
    co = datetime(2026, 5, 25, 17, 0)
    policies = {"holiday_dates": json.dumps(["2026-05-25"])}

    items = svc.calculate([_entry(ci, co)], [], policies)
    holiday_items = _items_by_type(items, "holiday")
    assert len(holiday_items) > 0
    assert all(i["rate_multiplier"] == 2.0 for i in holiday_items)


def test_holiday_not_applied_on_non_holiday():
    """Regular day → no holiday items."""
    ci = datetime(2026, 5, 11, 9, 0)
    co = datetime(2026, 5, 11, 17, 0)
    policies = {"holiday_dates": json.dumps(["2026-05-25"])}

    items = svc.calculate([_entry(ci, co)], [], policies)
    assert len(_items_by_type(items, "holiday")) == 0


# ── Night differential ────────────────────────────────────────────────────────

def test_night_differential_applied():
    """Entry fully in night window → all hours are night_differential."""
    ci = datetime(2026, 5, 14, 22, 0)
    co = datetime(2026, 5, 15, 6, 0)  # 8 hrs overnight

    items = svc.calculate([_entry(ci, co)], [], {})
    night_items = _items_by_type(items, "night_differential")
    assert len(night_items) > 0
    assert all(i["rate_multiplier"] == 1.25 for i in night_items)
    # Total night hours should be 8
    assert abs(_total(items, "night_differential") - 8.0) < 1e-4


def test_no_night_differential_daytime():
    """Daytime entry → no night_differential items."""
    ci = datetime(2026, 5, 14, 9, 0)
    co = datetime(2026, 5, 14, 17, 0)
    items = svc.calculate([_entry(ci, co)], [], {})
    assert _total(items, "night_differential") == 0.0


# ── PTO leave items ───────────────────────────────────────────────────────────

def test_pto_leave_generates_line_item():
    """Approved PTO for 1 day → 8-hr 'pto' line item at 1.0×."""
    leave = _leave("pto", date(2026, 5, 15), date(2026, 5, 15))
    items = svc.calculate([], [leave], {})
    pto_items = _items_by_type(items, "pto")
    assert len(pto_items) == 1
    assert pto_items[0]["hours_worked"] == 8.0
    assert pto_items[0]["rate_multiplier"] == 1.0


def test_unpaid_leave_generates_no_item():
    """Unpaid leave → no line items."""
    leave = _leave("unpaid", date(2026, 5, 15), date(2026, 5, 15))
    items = svc.calculate([], [leave], {})
    assert len(items) == 0


def test_multi_day_sick_leave():
    """2-day sick leave → 2 × 8-hr sick items."""
    leave = _leave("sick", date(2026, 5, 15), date(2026, 5, 16))
    items = svc.calculate([], [leave], {})
    sick_items = _items_by_type(items, "sick")
    assert len(sick_items) == 2
    assert abs(_total(items, "sick") - 16.0) < 1e-6


# ── Open entry skipped ────────────────────────────────────────────────────────

def test_open_entry_skipped():
    """Entry with clock_out=None → not included in output."""
    entry = {"clock_in": datetime(2026, 5, 11, 8, 0), "clock_out": None, "break_minutes": 0}
    items = svc.calculate([entry], [], {})
    assert len(items) == 0


# ── Comp-time banking ─────────────────────────────────────────────────────────

def test_comp_time_banking():
    """OT hours banked as comp when bank_comp_time=true."""
    ci = datetime(2026, 5, 11, 8, 0)
    co = datetime(2026, 5, 11, 18, 0)  # 10 hrs → 2 OT → should become 'comp'
    policies = {"bank_comp_time": "true"}

    items = svc.calculate([_entry(ci, co)], [], policies)
    assert len(_items_by_type(items, "overtime")) == 0
    comp_items = _items_by_type(items, "comp")
    assert len(comp_items) > 0
    assert abs(_total(items, "comp") - 2.0) < 1e-4


# ── Invalid / bad policy values default gracefully ───────────────────────────

def test_invalid_policy_defaults():
    """Malformed policy values fall back to defaults without raising."""
    ci = datetime(2026, 5, 11, 8, 0)
    co = datetime(2026, 5, 11, 17, 0)  # 9 hrs
    policies = {
        "ot_daily_threshold": "INVALID",
        "holiday_dates": "NOT_JSON",
    }
    # Should not raise; defaults to 8-hr threshold
    items = svc.calculate([_entry(ci, co)], [], policies)
    assert len(items) > 0
