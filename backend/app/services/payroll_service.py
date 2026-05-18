import csv
import io
import json
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import PunchError
from app.core.utils import now_utc
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.company_policy import CompanyPolicy
from app.models.leave_request import LeaveRequest
from app.models.payroll_export import PayrollExport
from app.models.payroll_line_item import PayrollLineItem
from app.models.time_entry import TimeEntry
from app.models.timesheet import Timesheet
from app.services.payroll_calculation_service import PayrollCalculationService


class TimesheetService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._calc = PayrollCalculationService()

    # ── Generate ──────────────────────────────────────────────────────────────

    async def generate(
        self,
        employee_id: str,
        company_id: str,
        pay_period_start: date,
        pay_period_end: date,
        requested_by: str,
    ) -> Timesheet:
        if pay_period_end < pay_period_start:
            raise PunchError("pay_period_end must be on or after pay_period_start", 422)

        # Fetch closed time entries for this employee in this pay period
        entries_result = await self._db.execute(
            select(TimeEntry).where(
                TimeEntry.employee_id == employee_id,
                TimeEntry.company_id == company_id,
                TimeEntry.status.in_(["closed", "corrected"]),
                TimeEntry.clock_in >= datetime.combine(pay_period_start, datetime.min.time()),
                TimeEntry.clock_in <= datetime.combine(pay_period_end, datetime.max.time()),
            )
        )
        time_entries = entries_result.scalars().all()

        # Fetch approved leave requests that overlap the pay period
        leave_result = await self._db.execute(
            select(LeaveRequest).where(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.company_id == company_id,
                LeaveRequest.status == "approved",
                LeaveRequest.start_date <= pay_period_end,
                LeaveRequest.end_date >= pay_period_start,
            )
        )
        leave_requests = leave_result.scalars().all()

        # Fetch company policies
        policy_result = await self._db.execute(
            select(CompanyPolicy).where(CompanyPolicy.company_id == company_id)
        )
        policy_rows = policy_result.scalars().all()
        policies = {row.policy_key: row.policy_value for row in policy_rows}

        # Calculate line items
        raw_items = self._calc.calculate(time_entries, leave_requests, policies)

        # Aggregate totals
        total_regular = sum(i["hours_worked"] for i in raw_items if i["rate_type"] == "regular")
        total_ot = sum(
            i["hours_worked"]
            for i in raw_items
            if i["rate_type"] in ("overtime", "double_time")
        )
        total_holiday = sum(i["hours_worked"] for i in raw_items if i["rate_type"] == "holiday")
        total_diff = sum(
            i["hours_worked"] for i in raw_items if i["rate_type"] == "night_differential"
        )

        # Create timesheet
        ts = Timesheet(
            employee_id=employee_id,
            company_id=company_id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            status="draft",
            total_regular_hrs=round(total_regular, 4),
            total_ot_hrs=round(total_ot, 4),
            total_holiday_hrs=round(total_holiday, 4),
            total_differential_hrs=round(total_diff, 4),
        )
        self._db.add(ts)
        await self._db.flush()

        # Create line items
        for item in raw_items:
            self._db.add(PayrollLineItem(
                timesheet_id=ts.id,
                entry_date=item["entry_date"],
                hours_worked=item["hours_worked"],
                rate_type=item["rate_type"],
                rate_multiplier=item["rate_multiplier"],
                notes=item.get("notes"),
            ))

        self._db.add(AuditLog(
            entity_type="timesheet",
            entity_id=ts.id,
            action="timesheet_generated",
            performed_by=requested_by,
            performed_at=now_utc(),
            details=json.dumps({
                "employee_id": employee_id,
                "pay_period_start": str(pay_period_start),
                "pay_period_end": str(pay_period_end),
                "line_items": len(raw_items),
            }),
        ))

        await self._db.commit()
        await self._db.refresh(ts)
        # Eager-load line items
        result = await self._db.execute(
            select(Timesheet)
            .options(selectinload(Timesheet.line_items))
            .where(Timesheet.id == ts.id)
        )
        return result.scalar_one()

    # ── List ──────────────────────────────────────────────────────────────────

    async def list_timesheets(
        self,
        employee_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        q = select(Timesheet).options(selectinload(Timesheet.line_items))
        if employee_id:
            q = q.where(Timesheet.employee_id == employee_id)
        if company_id:
            q = q.where(Timesheet.company_id == company_id)
        if status:
            q = q.where(Timesheet.status == status)

        count_result = await self._db.execute(q)
        total = len(count_result.scalars().all())

        items = (
            await self._db.execute(q.offset((page - 1) * size).limit(size))
        ).scalars().all()

        return {"total": total, "page": page, "size": size, "items": list(items)}

    # ── Get single ────────────────────────────────────────────────────────────

    async def get_timesheet(self, timesheet_id: str) -> Timesheet | None:
        result = await self._db.execute(
            select(Timesheet)
            .options(selectinload(Timesheet.line_items))
            .where(Timesheet.id == timesheet_id)
        )
        return result.scalar_one_or_none()

    # ── Submit ────────────────────────────────────────────────────────────────

    async def submit(self, timesheet_id: str, submitted_by: str) -> Timesheet:
        ts = await self.get_timesheet(timesheet_id)
        if ts is None:
            raise PunchError("Timesheet not found", 404)
        if ts.employee_id != submitted_by:
            raise PunchError("You can only submit your own timesheets", 403)
        if ts.status != "draft":
            raise PunchError("Only draft timesheets can be submitted", 409)

        ts.status = "submitted"
        ts.submitted_at = now_utc()
        await self._db.flush()

        self._db.add(AuditLog(
            entity_type="timesheet",
            entity_id=ts.id,
            action="timesheet_submitted",
            performed_by=submitted_by,
            performed_at=now_utc(),
            details=json.dumps({"timesheet_id": ts.id}),
        ))

        await self._db.commit()
        await self._db.refresh(ts)
        return ts

    # ── Approve ───────────────────────────────────────────────────────────────

    async def approve(self, timesheet_id: str, approved_by: str) -> Timesheet:
        ts = await self.get_timesheet(timesheet_id)
        if ts is None:
            raise PunchError("Timesheet not found", 404)
        if ts.status != "submitted":
            raise PunchError("Only submitted timesheets can be approved", 409)

        ts.status = "approved"
        ts.approved_by = approved_by
        ts.approved_at = now_utc()
        await self._db.flush()

        self._db.add(AuditLog(
            entity_type="timesheet",
            entity_id=ts.id,
            action="timesheet_approved",
            performed_by=approved_by,
            performed_at=now_utc(),
            details=json.dumps({"timesheet_id": ts.id}),
        ))

        await self._db.commit()
        await self._db.refresh(ts)
        return ts

    # ── Export ────────────────────────────────────────────────────────────────

    async def export(
        self,
        timesheet_id: str,
        export_format: str,
        exported_by: str,
    ) -> tuple[PayrollExport, str]:
        ts = await self.get_timesheet(timesheet_id)
        if ts is None:
            raise PunchError("Timesheet not found", 404)
        if ts.status not in ("approved", "exported"):
            raise PunchError("Only approved timesheets can be exported", 409)
        if export_format not in ("csv", "json"):
            raise PunchError("export_format must be 'csv' or 'json'", 422)

        items = ts.line_items

        if export_format == "csv":
            content = self._build_csv(ts, items)
        else:
            content = self._build_json(ts, items)

        file_name = (
            f"timesheet_{ts.employee_id[:8]}_{ts.pay_period_start}_{ts.pay_period_end}.{export_format}"
        )

        pe = PayrollExport(
            company_id=ts.company_id,
            pay_period_start=ts.pay_period_start,
            pay_period_end=ts.pay_period_end,
            exported_at=now_utc(),
            exported_by=exported_by,
            export_format=export_format,
            record_count=len(items),
            file_name=file_name,
        )
        self._db.add(pe)
        await self._db.flush()

        ts.status = "exported"
        await self._db.flush()

        self._db.add(AuditLog(
            entity_type="payroll_export",
            entity_id=pe.id,
            action="payroll_exported",
            performed_by=exported_by,
            performed_at=now_utc(),
            details=json.dumps({
                "timesheet_id": ts.id,
                "format": export_format,
                "record_count": len(items),
            }),
        ))

        await self._db.commit()
        await self._db.refresh(pe)
        return pe, content

    # ── Export format builders ────────────────────────────────────────────────

    @staticmethod
    def _build_csv(ts: Timesheet, items: list[PayrollLineItem]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "timesheet_id", "employee_id", "company_id",
            "pay_period_start", "pay_period_end",
            "entry_date", "rate_type", "hours_worked", "rate_multiplier", "notes",
        ])
        for item in items:
            writer.writerow([
                ts.id, ts.employee_id, ts.company_id,
                ts.pay_period_start, ts.pay_period_end,
                item.entry_date, item.rate_type,
                item.hours_worked, item.rate_multiplier, item.notes or "",
            ])
        return buf.getvalue()

    @staticmethod
    def _build_json(ts: Timesheet, items: list[PayrollLineItem]) -> str:
        payload = {
            "timesheet_id": ts.id,
            "employee_id": ts.employee_id,
            "company_id": ts.company_id,
            "pay_period_start": str(ts.pay_period_start),
            "pay_period_end": str(ts.pay_period_end),
            "summary": {
                "total_regular_hrs": ts.total_regular_hrs,
                "total_ot_hrs": ts.total_ot_hrs,
                "total_holiday_hrs": ts.total_holiday_hrs,
                "total_differential_hrs": ts.total_differential_hrs,
            },
            "line_items": [
                {
                    "entry_date": str(item.entry_date),
                    "rate_type": item.rate_type,
                    "hours_worked": item.hours_worked,
                    "rate_multiplier": item.rate_multiplier,
                    "notes": item.notes,
                }
                for item in items
            ],
        }
        return json.dumps(payload, indent=2)
