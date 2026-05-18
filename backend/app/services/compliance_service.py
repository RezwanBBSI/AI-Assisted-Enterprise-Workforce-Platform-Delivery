"""
ComplianceValidationService — stateless rule checks; 100% branch coverage required.
ComplianceService — async CRUD for compliance violations and audit logging.

Violation types:
  missing_punch   — TimeEntry with no clock_out when pay period has ended
  max_hours       — Weekly total hours > CompanyPolicy.max_hours_per_week (default 60)
  mandatory_break — ShiftSchedule > 6 hrs with break_minutes == 0
  ot_threshold    — OT hours exceed CompanyPolicy.ot_alert_threshold
"""
import json
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PunchError
from app.core.utils import now_utc
from app.models.audit_log import AuditLog
from app.models.company_policy import CompanyPolicy
from app.models.compliance_violation import ComplianceViolation
from app.models.shift_schedule import ShiftSchedule
from app.models.time_entry import TimeEntry
from app.models.timesheet import Timesheet
from app.schemas.company import PaginatedResponse
from app.schemas.compliance import (
    ComplianceRunResult,
    ComplianceViolationResponse,
)


# ── Stateless validation helpers ──────────────────────────────────────────────

class ComplianceValidationService:
    """Stateless; 100% branch coverage required."""

    @staticmethod
    def _policy_float(policies: dict[str, str], key: str, default: float) -> float:
        val = policies.get(key)
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def check_missing_punch(
        entries: list[TimeEntry],
        pay_period_end: date,
    ) -> list[dict]:
        """Return violation dicts for open entries whose pay period has ended."""
        period_end_dt = datetime(
            pay_period_end.year, pay_period_end.month, pay_period_end.day, 23, 59, 59
        )
        violations = []
        for entry in entries:
            if entry.clock_out is None and entry.clock_in <= period_end_dt:
                violations.append({
                    "employee_id": entry.employee_id,
                    "violation_type": "missing_punch",
                    "description": (
                        f"No clock-out recorded for entry started at "
                        f"{entry.clock_in.strftime('%Y-%m-%d %H:%M')}"
                    ),
                    "occurred_at": entry.clock_in,
                })
        return violations

    @staticmethod
    def check_max_hours(
        timesheets: list[Timesheet],
        policies: dict[str, str],
    ) -> list[dict]:
        """Return violations for employees who exceeded max weekly hours."""
        max_hours = ComplianceValidationService._policy_float(
            policies, "max_hours_per_week", 60.0
        )
        violations = []
        for ts in timesheets:
            total = (ts.total_regular_hrs or 0.0) + (ts.total_ot_hrs or 0.0)
            if total > max_hours:
                violations.append({
                    "employee_id": ts.employee_id,
                    "violation_type": "max_hours",
                    "description": (
                        f"Total hours {total:.1f} exceeded max {max_hours:.0f} hrs/week"
                    ),
                    "occurred_at": datetime(
                        ts.pay_period_end.year,
                        ts.pay_period_end.month,
                        ts.pay_period_end.day,
                    ),
                })
        return violations

    @staticmethod
    def check_mandatory_break(shifts: list[ShiftSchedule]) -> list[dict]:
        """Return violations for shifts > 6 hrs with break_minutes == 0."""
        violations = []
        for shift in shifts:
            # Compute duration; shift_start / shift_end are time objects
            start_dt = datetime.combine(date.today(), shift.shift_start)
            end_dt = datetime.combine(date.today(), shift.shift_end)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)  # overnight shift
            duration_hrs = (end_dt - start_dt).total_seconds() / 3600
            if duration_hrs > 6.0 and (shift.break_minutes or 0) == 0:
                # resolve shift_date to a date object regardless of type
                sd = shift.shift_date
                if isinstance(sd, datetime):
                    sd = sd.date()
                violations.append({
                    "employee_id": shift.employee_id,
                    "violation_type": "mandatory_break",
                    "description": (
                        f"Shift on {sd} is {duration_hrs:.1f} hrs with no break scheduled"
                    ),
                    "occurred_at": datetime.combine(sd, shift.shift_start),
                })
        return violations

    @staticmethod
    def check_ot_threshold(
        timesheets: list[Timesheet],
        policies: dict[str, str],
    ) -> list[dict]:
        """Return violations where OT hours exceed the configured alert threshold."""
        threshold = ComplianceValidationService._policy_float(
            policies, "ot_alert_threshold", 0.0
        )
        # A threshold of 0 means no alert configured — skip entirely
        if threshold <= 0.0:
            return []
        violations = []
        for ts in timesheets:
            ot = ts.total_ot_hrs or 0.0
            if ot > threshold:
                violations.append({
                    "employee_id": ts.employee_id,
                    "violation_type": "ot_threshold",
                    "description": (
                        f"OT hours {ot:.1f} exceeded alert threshold {threshold:.0f} hrs"
                    ),
                    "occurred_at": datetime(
                        ts.pay_period_end.year,
                        ts.pay_period_end.month,
                        ts.pay_period_end.day,
                    ),
                })
        return violations


# ── Async CRUD service ────────────────────────────────────────────────────────

class ComplianceService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def run_validation(
        self,
        company_id: str,
        pay_period_start: date,
        pay_period_end: date,
        validated_by: str,
    ) -> ComplianceRunResult:
        """Run all compliance checks and persist violations found."""
        # Load company policies
        pol_result = await self._db.execute(
            select(CompanyPolicy).where(CompanyPolicy.company_id == company_id)
        )
        policies = {p.policy_key: p.policy_value for p in pol_result.scalars().all()}

        # Load all time entries within the pay period
        start_dt = datetime(
            pay_period_start.year, pay_period_start.month, pay_period_start.day
        )
        end_dt = datetime(
            pay_period_end.year, pay_period_end.month, pay_period_end.day, 23, 59, 59
        )
        te_result = await self._db.execute(
            select(TimeEntry).where(
                TimeEntry.company_id == company_id,
                TimeEntry.clock_in >= start_dt,
                TimeEntry.clock_in <= end_dt,
            )
        )
        entries = te_result.scalars().all()

        # Load timesheets for this pay period
        ts_result = await self._db.execute(
            select(Timesheet).where(
                Timesheet.company_id == company_id,
                Timesheet.pay_period_start == pay_period_start,
                Timesheet.pay_period_end == pay_period_end,
            )
        )
        timesheets = ts_result.scalars().all()

        # Load shifts within the pay period
        sh_result = await self._db.execute(
            select(ShiftSchedule).where(
                ShiftSchedule.company_id == company_id,
                ShiftSchedule.shift_date >= pay_period_start,
                ShiftSchedule.shift_date <= pay_period_end,
            )
        )
        shifts = sh_result.scalars().all()

        # Run stateless checks
        all_violations: list[dict] = []
        all_violations.extend(
            ComplianceValidationService.check_missing_punch(entries, pay_period_end)
        )
        all_violations.extend(
            ComplianceValidationService.check_max_hours(timesheets, policies)
        )
        all_violations.extend(
            ComplianceValidationService.check_mandatory_break(shifts)
        )
        all_violations.extend(
            ComplianceValidationService.check_ot_threshold(timesheets, policies)
        )

        # Persist violations
        created: list[ComplianceViolation] = []
        for v in all_violations:
            violation = ComplianceViolation(
                employee_id=v["employee_id"],
                company_id=company_id,
                violation_type=v["violation_type"],
                description=v["description"],
                occurred_at=v["occurred_at"],
            )
            self._db.add(violation)
            created.append(violation)

        # Audit log
        self._db.add(AuditLog(
            entity_type="compliance_validation",
            entity_id=company_id,
            action="validate",
            performed_by=validated_by,
            performed_at=now_utc(),
            details=json.dumps({
                "pay_period_start": str(pay_period_start),
                "pay_period_end": str(pay_period_end),
                "violations_found": len(created),
            }),
        ))

        await self._db.commit()
        for v in created:
            await self._db.refresh(v)

        return ComplianceRunResult(
            violations_created=len(created),
            violations=[ComplianceViolationResponse.model_validate(v) for v in created],
        )

    async def list_violations(
        self,
        company_id: str,
        employee_id: Optional[str] = None,
        violation_type: Optional[str] = None,
        resolved: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse:
        q = select(ComplianceViolation).where(
            ComplianceViolation.company_id == company_id
        )
        if employee_id:
            q = q.where(ComplianceViolation.employee_id == employee_id)
        if violation_type:
            q = q.where(ComplianceViolation.violation_type == violation_type)
        if resolved is not None:
            q = q.where(ComplianceViolation.resolved == resolved)

        total = (
            await self._db.execute(select(func.count()).select_from(q.subquery()))
        ).scalar_one()

        rows = (
            await self._db.execute(q.offset((page - 1) * size).limit(size))
        ).scalars().all()

        return PaginatedResponse(
            total=total,
            page=page,
            size=size,
            items=[ComplianceViolationResponse.model_validate(r) for r in rows],
        )

    async def resolve(
        self,
        violation_id: str,
        resolved_by: str,
        resolution_notes: str,
    ) -> ComplianceViolationResponse:
        result = await self._db.execute(
            select(ComplianceViolation).where(ComplianceViolation.id == violation_id)
        )
        violation = result.scalar_one_or_none()
        if violation is None:
            raise PunchError("Compliance violation not found", 404)
        if violation.resolved:
            raise PunchError("Violation is already resolved", 409)

        violation.resolved = True
        violation.resolved_at = now_utc()
        violation.resolved_by = resolved_by
        violation.resolution_notes = resolution_notes

        self._db.add(AuditLog(
            entity_type="compliance_violation",
            entity_id=violation.id,
            action="resolve",
            performed_by=resolved_by,
            performed_at=now_utc(),
            details=json.dumps({"resolution_notes": resolution_notes}),
        ))

        await self._db.commit()
        await self._db.refresh(violation)
        return ComplianceViolationResponse.model_validate(violation)
