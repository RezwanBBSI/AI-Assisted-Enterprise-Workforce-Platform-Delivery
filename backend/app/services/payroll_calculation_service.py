"""
PayrollCalculationService — stateless; 100% branch coverage required.

Converts closed TimeEntry rows + approved LeaveRequest rows for a given pay period
into a flat list of line-item dicts ready to be stored as PayrollLineItem rows.

Policy keys consumed from CompanyPolicy (all optional with sensible defaults):
  ot_daily_threshold    — hours/day before daily OT kicks in  (default: 8)
  ot_double_threshold   — hours/day before double-time kicks in (default: 12)
  weekly_ot_threshold   — hours/week before weekly OT kicks in  (default: 40)
  holiday_dates         — JSON list of ISO date strings e.g. '["2026-12-25"]'
  night_diff_start      — 24-hr time string for night window start (default: "22:00")
  night_diff_end        — 24-hr time string for night window end   (default: "06:00")
  bank_comp_time        — "true" / "false" — if true, OT hours become comp balance
                          instead of overtime line items (default: "false")
"""
import json
from datetime import date, datetime, time, timedelta
from typing import Any


# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_time(t_str: str) -> time:
    h, m = t_str.split(":")
    return time(int(h), int(m))


def _overlap_hours(
    clock_in: datetime,
    clock_out: datetime,
    window_start: time,
    window_end: time,
) -> float:
    """Return the number of hours that [clock_in, clock_out) overlaps the nightly
    window [window_start, window_end).  The window may cross midnight."""
    total = 0.0
    # Iterate over each calendar day that the entry spans
    day = clock_in.date()
    while day <= clock_out.date():
        # Build the window interval for this day
        ws_dt = datetime.combine(day, window_start)
        # window_end is on the *next* calendar day when it is earlier than window_start
        if window_end <= window_start:
            we_dt = datetime.combine(day + timedelta(days=1), window_end)
        else:
            we_dt = datetime.combine(day, window_end)

        # Clamp to the actual entry
        seg_start = max(clock_in, ws_dt)
        seg_end = min(clock_out, we_dt)
        if seg_end > seg_start:
            total += (seg_end - seg_start).total_seconds() / 3600
        day += timedelta(days=1)
    return total


# ── main service ──────────────────────────────────────────────────────────────

class PayrollCalculationService:
    """Stateless payroll rule engine."""

    # ── Policy helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _get_float(policies: dict[str, str], key: str, default: float) -> float:
        val = policies.get(key)
        if val is None:
            return default
        try:
            return float(val.strip('"'))
        except (ValueError, AttributeError):
            return default

    @staticmethod
    def _get_str(policies: dict[str, str], key: str, default: str) -> str:
        val = policies.get(key)
        if val is None:
            return default
        return val.strip('"')

    @staticmethod
    def _get_holiday_dates(policies: dict[str, str]) -> set[date]:
        raw = policies.get("holiday_dates")
        if not raw:
            return set()
        try:
            dates = json.loads(raw)
            return {date.fromisoformat(d) for d in dates}
        except (json.JSONDecodeError, ValueError):
            return set()

    # ── Daily classification ──────────────────────────────────────────────────

    @staticmethod
    def _classify_daily(
        gross_hours: float,
        daily_threshold: float,
        double_threshold: float,
    ) -> tuple[float, float, float]:
        """
        Split gross_hours into (regular, overtime, double_time).

        - regular     : first `daily_threshold` hours
        - overtime    : hours between `daily_threshold` and `double_threshold`  (1.5×)
        - double_time : hours beyond `double_threshold`                          (2.0×)
        """
        if gross_hours <= daily_threshold:
            return gross_hours, 0.0, 0.0

        if gross_hours <= double_threshold:
            return daily_threshold, gross_hours - daily_threshold, 0.0

        return daily_threshold, double_threshold - daily_threshold, gross_hours - double_threshold

    # ── Night differential ────────────────────────────────────────────────────

    @staticmethod
    def _split_night_differential(
        clock_in: datetime,
        clock_out: datetime,
        gross_hours: float,
        window_start: time,
        window_end: time,
    ) -> tuple[float, float]:
        """
        Return (day_hours, night_hours).  Night hours fall within the overnight
        window and attract a 1.25× differential.  Hours may not exceed gross_hours.
        """
        night = min(_overlap_hours(clock_in, clock_out, window_start, window_end), gross_hours)
        day = gross_hours - night
        return day, night

    # ── Weekly OT redistribution ──────────────────────────────────────────────

    @staticmethod
    def _apply_weekly_ot(
        daily_items: list[dict[str, Any]],
        weekly_threshold: float,
    ) -> list[dict[str, Any]]:
        """
        After daily classification, scan through regular-hour items in chronological
        order. Once the running weekly total of regular + overtime hours exceeds
        `weekly_threshold`, re-classify surplus regular hours as overtime (1.5×).

        Double-time hours are *not* re-classified by the weekly rule.
        Returns a new list with updated items (original list unchanged).
        """
        result: list[dict[str, Any]] = []
        weekly_total = 0.0  # counts regular + ot (not double-time)

        for item in sorted(daily_items, key=lambda x: x["entry_date"]):
            if item["rate_type"] not in ("regular", "overtime"):
                result.append(item)
                continue

            hours = item["hours_worked"]
            if item["rate_type"] == "overtime":
                # Daily OT hours are already classified — they do NOT consume
                # the weekly regular-hour threshold.
                result.append(item)
                continue

            # regular hours — check if weekly cap is hit
            remaining_regular = max(0.0, weekly_threshold - weekly_total)
            if hours <= remaining_regular:
                weekly_total += hours
                result.append(item)
            else:
                # split this item into regular + weekly_ot portions
                regular_portion = remaining_regular
                ot_portion = hours - remaining_regular
                weekly_total += hours

                if regular_portion > 0:
                    result.append({**item, "hours_worked": round(regular_portion, 6)})
                result.append({
                    **item,
                    "hours_worked": round(ot_portion, 6),
                    "rate_type": "overtime",
                    "rate_multiplier": 1.5,
                    "notes": (item.get("notes") or "") + " [weekly OT]",
                })
        return result

    # ── Holiday override ──────────────────────────────────────────────────────

    @staticmethod
    def _apply_holiday(
        items: list[dict[str, Any]],
        holiday_dates: set[date],
    ) -> list[dict[str, Any]]:
        """
        For any line item whose entry_date is in holiday_dates, upgrade the
        rate_type to 'holiday' and set multiplier to 2.0 regardless of the
        daily/weekly classification.
        """
        result = []
        for item in items:
            if item["entry_date"] in holiday_dates:
                result.append({
                    **item,
                    "rate_type": "holiday",
                    "rate_multiplier": 2.0,
                    "notes": (item.get("notes") or "") + " [holiday]",
                })
            else:
                result.append(item)
        return result

    # ── PTO / comp-leave injection ────────────────────────────────────────────

    @staticmethod
    def _build_leave_items(leave_requests: list[Any]) -> list[dict[str, Any]]:
        """
        Convert approved leave requests into synthetic 8-hr line items.
        leave_requests: list of LeaveRequest ORM objects (or dicts with same keys).
        """
        items = []
        for req in leave_requests:
            # Support both ORM objects and plain dicts
            leave_type = req.leave_type if hasattr(req, "leave_type") else req["leave_type"]
            start = req.start_date if hasattr(req, "start_date") else req["start_date"]
            end = req.end_date if hasattr(req, "end_date") else req["end_date"]

            if leave_type == "unpaid":
                continue  # unpaid leave generates no pay line items

            rate_type = leave_type  # "pto", "sick", "comp"
            current = start
            while current <= end:
                items.append({
                    "entry_date": current,
                    "hours_worked": 8.0,
                    "rate_type": rate_type,
                    "rate_multiplier": 1.0,
                    "notes": f"Leave: {leave_type}",
                })
                current += timedelta(days=1)
        return items

    # ── Main orchestrator ─────────────────────────────────────────────────────

    def calculate(
        self,
        time_entries: list[Any],
        leave_requests: list[Any],
        policies: dict[str, str],
    ) -> list[dict[str, Any]]:
        """
        Calculate payroll line items for a pay period.

        Parameters
        ----------
        time_entries  : list of closed TimeEntry ORM objects
        leave_requests: list of approved LeaveRequest ORM objects
        policies      : dict of {policy_key: policy_value} from CompanyPolicy rows

        Returns
        -------
        list of line-item dicts ready to be stored as PayrollLineItem rows
        """
        daily_threshold = self._get_float(policies, "ot_daily_threshold", 8.0)
        double_threshold = self._get_float(policies, "ot_double_threshold", 12.0)
        weekly_threshold = self._get_float(policies, "weekly_ot_threshold", 40.0)
        holiday_dates = self._get_holiday_dates(policies)
        night_start = _parse_time(self._get_str(policies, "night_diff_start", "22:00"))
        night_end = _parse_time(self._get_str(policies, "night_diff_end", "06:00"))
        bank_comp = self._get_str(policies, "bank_comp_time", "false").lower() == "true"

        line_items: list[dict[str, Any]] = []

        for entry in time_entries:
            # Support both ORM objects and plain dicts
            clock_in = entry.clock_in if hasattr(entry, "clock_in") else entry["clock_in"]
            clock_out = entry.clock_out if hasattr(entry, "clock_out") else entry["clock_out"]
            break_minutes = (
                entry.break_minutes if hasattr(entry, "break_minutes") else entry.get("break_minutes", 0)
            ) or 0

            if clock_out is None:
                continue  # open entries are skipped

            gross_hours = (clock_out - clock_in).total_seconds() / 3600 - break_minutes / 60
            if gross_hours <= 0:
                continue

            entry_date = clock_in.date()

            # Night differential split first (before daily OT classification)
            day_hours, night_hours = self._split_night_differential(
                clock_in, clock_out, gross_hours, night_start, night_end
            )

            # Classify the daytime portion
            regular, ot, double = self._classify_daily(day_hours, daily_threshold, double_threshold)

            if regular > 0:
                line_items.append({
                    "entry_date": entry_date,
                    "hours_worked": round(regular, 6),
                    "rate_type": "regular",
                    "rate_multiplier": 1.0,
                    "notes": None,
                })
            if ot > 0:
                if bank_comp:
                    line_items.append({
                        "entry_date": entry_date,
                        "hours_worked": round(ot, 6),
                        "rate_type": "comp",
                        "rate_multiplier": 1.0,
                        "notes": "comp-time banked",
                    })
                else:
                    line_items.append({
                        "entry_date": entry_date,
                        "hours_worked": round(ot, 6),
                        "rate_type": "overtime",
                        "rate_multiplier": 1.5,
                        "notes": None,
                    })
            if double > 0:
                line_items.append({
                    "entry_date": entry_date,
                    "hours_worked": round(double, 6),
                    "rate_type": "double_time",
                    "rate_multiplier": 2.0,
                    "notes": None,
                })

            # Night differential portion
            if night_hours > 0:
                line_items.append({
                    "entry_date": entry_date,
                    "hours_worked": round(night_hours, 6),
                    "rate_type": "night_differential",
                    "rate_multiplier": 1.25,
                    "notes": "night differential",
                })

        # Apply weekly OT redistribution (only on regular/ot items, not night/double)
        line_items = self._apply_weekly_ot(line_items, weekly_threshold)

        # Holiday override
        line_items = self._apply_holiday(line_items, holiday_dates)

        # Inject leave line items
        line_items.extend(self._build_leave_items(leave_requests))

        return line_items
