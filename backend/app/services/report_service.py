"""
ReportService — read-only aggregations for compliance, attendance,
audit trail, operational, and crosscheck reports.
"""
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.compliance_violation import ComplianceViolation
from app.models.shift_schedule import ShiftSchedule
from app.models.time_entry import TimeEntry
from app.models.timesheet import Timesheet
from app.schemas.company import PaginatedResponse
from app.schemas.compliance import (
    AttendanceExceptionItem,
    AttendanceExceptionsResponse,
    AuditTrailItem,
    ComplianceReportResponse,
    ComplianceViolationResponse,
    CrossCheckEntry,
    CrossCheckResponse,
    OperationalReportResponse,
)


class ReportService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def compliance_report(
        self,
        company_id: str,
        pay_period_start: date,
        pay_period_end: date,
    ) -> ComplianceReportResponse:
        start_dt = datetime(pay_period_start.year, pay_period_start.month, pay_period_start.day)
        end_dt = datetime(pay_period_end.year, pay_period_end.month, pay_period_end.day, 23, 59, 59)

        result = await self._db.execute(
            select(ComplianceViolation).where(
                ComplianceViolation.company_id == company_id,
                ComplianceViolation.occurred_at >= start_dt,
                ComplianceViolation.occurred_at <= end_dt,
            )
        )
        violations = result.scalars().all()

        by_type: dict[str, int] = {}
        unresolved = 0
        for v in violations:
            by_type[v.violation_type] = by_type.get(v.violation_type, 0) + 1
            if not v.resolved:
                unresolved += 1

        return ComplianceReportResponse(
            company_id=company_id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            total_violations=len(violations),
            unresolved=unresolved,
            by_type=by_type,
            violations=[ComplianceViolationResponse.model_validate(v) for v in violations],
        )

    async def attendance_exceptions(
        self,
        company_id: str,
        start_date: date,
        end_date: date,
    ) -> AttendanceExceptionsResponse:
        result = await self._db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.company_id == company_id,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date,
                AttendanceRecord.status != "present",
            )
        )
        rows = result.scalars().all()

        return AttendanceExceptionsResponse(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            total=len(rows),
            items=[AttendanceExceptionItem.model_validate(r) for r in rows],
        )

    async def audit_trail(
        self,
        entity_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse:
        q = select(AuditLog)
        if entity_type:
            q = q.where(AuditLog.entity_type == entity_type)
        if start_date:
            q = q.where(
                AuditLog.performed_at >= datetime(start_date.year, start_date.month, start_date.day)
            )
        if end_date:
            q = q.where(
                AuditLog.performed_at <= datetime(
                    end_date.year, end_date.month, end_date.day, 23, 59, 59
                )
            )
        q = q.order_by(AuditLog.performed_at.desc())

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
            items=[AuditTrailItem.model_validate(r) for r in rows],
        )

    async def operational_report(
        self,
        company_id: str,
        pay_period_start: date,
        pay_period_end: date,
    ) -> OperationalReportResponse:
        ts_result = await self._db.execute(
            select(Timesheet).where(
                Timesheet.company_id == company_id,
                Timesheet.pay_period_start == pay_period_start,
                Timesheet.pay_period_end == pay_period_end,
            )
        )
        timesheets = ts_result.scalars().all()

        total_regular = sum(ts.total_regular_hrs or 0.0 for ts in timesheets)
        total_ot = sum(ts.total_ot_hrs or 0.0 for ts in timesheets)
        unique_employees = len({ts.employee_id for ts in timesheets})

        att_result = await self._db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.company_id == company_id,
                AttendanceRecord.date >= pay_period_start,
                AttendanceRecord.date <= pay_period_end,
            )
        )
        att_rows = att_result.scalars().all()
        absences = sum(1 for r in att_rows if r.status == "absent")
        late_arrivals = sum(1 for r in att_rows if r.status == "late")

        return OperationalReportResponse(
            company_id=company_id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            total_employees=unique_employees,
            total_regular_hrs=total_regular,
            total_ot_hrs=total_ot,
            total_absences=absences,
            total_late_arrivals=late_arrivals,
        )

    async def crosscheck(
        self,
        company_id: str,
        pay_period_start: date,
        pay_period_end: date,
    ) -> CrossCheckResponse:
        """Compare shift schedules against time entries; flag discrepancies."""
        sh_result = await self._db.execute(
            select(ShiftSchedule).where(
                ShiftSchedule.company_id == company_id,
                ShiftSchedule.shift_date >= pay_period_start,
                ShiftSchedule.shift_date <= pay_period_end,
            )
        )
        shifts = sh_result.scalars().all()

        start_dt = datetime(pay_period_start.year, pay_period_start.month, pay_period_start.day)
        end_dt = datetime(pay_period_end.year, pay_period_end.month, pay_period_end.day, 23, 59, 59)
        te_result = await self._db.execute(
            select(TimeEntry).where(
                TimeEntry.company_id == company_id,
                TimeEntry.clock_in >= start_dt,
                TimeEntry.clock_in <= end_dt,
                TimeEntry.status == "closed",
            )
        )
        entries = te_result.scalars().all()

        # Build lookup: (employee_id, clock_in.date()) -> TimeEntry
        entry_map: dict[tuple[str, date], TimeEntry] = {}
        for te in entries:
            entry_map[(te.employee_id, te.clock_in.date())] = te

        discrepancies: list[CrossCheckEntry] = []
        for shift in shifts:
            sd = shift.shift_date
            if isinstance(sd, datetime):
                sd = sd.date()

            s_start = datetime.combine(date.today(), shift.shift_start)
            s_end = datetime.combine(date.today(), shift.shift_end)
            if s_end <= s_start:
                s_end += timedelta(days=1)
            scheduled_hrs = (s_end - s_start).total_seconds() / 3600

            key = (shift.employee_id, sd)
            if key not in entry_map:
                discrepancies.append(CrossCheckEntry(
                    employee_id=shift.employee_id,
                    shift_date=sd,
                    issue="no_time_entry",
                    scheduled_hours=scheduled_hrs,
                    actual_hours=None,
                ))
            else:
                te = entry_map[key]
                actual_hrs = (
                    (te.clock_out - te.clock_in).total_seconds() / 3600
                    if te.clock_out
                    else 0.0
                )
                # Flag if actual differs from scheduled by more than 30 min
                if abs(actual_hrs - scheduled_hrs) > 0.5:
                    discrepancies.append(CrossCheckEntry(
                        employee_id=shift.employee_id,
                        shift_date=sd,
                        issue="hours_mismatch",
                        scheduled_hours=scheduled_hrs,
                        actual_hours=actual_hrs,
                    ))

        return CrossCheckResponse(
            company_id=company_id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            total_discrepancies=len(discrepancies),
            entries=discrepancies,
        )
