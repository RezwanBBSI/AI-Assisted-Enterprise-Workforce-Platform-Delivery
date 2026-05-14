import json
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PunchError
from app.core.utils import now_utc, to_utc_naive
from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.time_correction import TimeCorrection
from app.models.time_entry import TimeEntry
from app.schemas.time_entry import CorrectionRequest, CorrectionReviewRequest


class TimeEntryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Clock-in ─────────────────────────────────────────────────────────────

    async def clock_in(
        self,
        employee_id: str,
        company_id: str,
        location_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> TimeEntry:
        from app.services.punch_validation_service import PunchValidationService

        ts = to_utc_naive(timestamp) if timestamp else now_utc()
        await PunchValidationService.validate_clock_in(self._db, employee_id, ts)

        entry = TimeEntry(
            employee_id=employee_id,
            company_id=company_id,
            location_id=location_id,
            clock_in=ts,
            status="open",
        )
        self._db.add(entry)
        await self._db.flush()

        # Create or update attendance record for today
        today = ts.date()
        result = await self._db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.employee_id == employee_id,
                AttendanceRecord.company_id == company_id,
                AttendanceRecord.date == today,
            )
        )
        ar = result.scalar_one_or_none()
        if ar is None:
            self._db.add(
                AttendanceRecord(
                    employee_id=employee_id,
                    company_id=company_id,
                    date=today,
                    status="present",
                    time_entry_id=entry.id,
                )
            )

        self._db.add(
            AuditLog(
                entity_type="time_entry",
                entity_id=entry.id,
                action="clock_in",
                performed_by=employee_id,
                performed_at=ts,
                details=json.dumps({"company_id": company_id, "location_id": location_id}),
            )
        )

        await self._db.commit()
        await self._db.refresh(entry)
        return entry

    # ── Clock-out ────────────────────────────────────────────────────────────

    async def clock_out(
        self, employee_id: str, timestamp: datetime | None = None
    ) -> TimeEntry:
        from app.services.punch_validation_service import PunchValidationService

        ts = to_utc_naive(timestamp) if timestamp else now_utc()

        result = await self._db.execute(
            select(TimeEntry).where(
                TimeEntry.employee_id == employee_id,
                TimeEntry.status == "open",
            )
        )
        entry = result.scalar_one_or_none()
        await PunchValidationService.validate_clock_out(self._db, employee_id, ts, entry)

        entry.clock_out = ts
        entry.status = "closed"

        self._db.add(
            AuditLog(
                entity_type="time_entry",
                entity_id=entry.id,
                action="clock_out",
                performed_by=employee_id,
                performed_at=ts,
                details=json.dumps(
                    {"clock_in": entry.clock_in.isoformat(), "clock_out": ts.isoformat()}
                ),
            )
        )

        await self._db.commit()
        await self._db.refresh(entry)
        return entry

    # ── List / get entries ───────────────────────────────────────────────────

    async def get_entries(
        self,
        employee_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        q = select(TimeEntry)
        if employee_id:
            q = q.where(TimeEntry.employee_id == employee_id)
        if company_id:
            q = q.where(TimeEntry.company_id == company_id)
        if status:
            q = q.where(TimeEntry.status == status)

        count_result = await self._db.execute(q)
        total = len(count_result.scalars().all())

        q = q.offset((page - 1) * size).limit(size)
        result = await self._db.execute(q)
        items = result.scalars().all()

        return {"total": total, "page": page, "size": size, "items": list(items)}

    async def get_entry(self, entry_id: str) -> TimeEntry | None:
        result = await self._db.execute(
            select(TimeEntry).where(TimeEntry.id == entry_id)
        )
        return result.scalar_one_or_none()

    # ── Corrections ──────────────────────────────────────────────────────────

    async def submit_correction(
        self, entry_id: str, requested_by: str, payload: CorrectionRequest
    ) -> TimeCorrection:
        entry = await self.get_entry(entry_id)
        if entry is None:
            raise PunchError("Time entry not found", 404)
        if entry.employee_id != requested_by:
            raise PunchError("Cannot submit a correction for another employee's entry", 403)

        new_ci = to_utc_naive(payload.new_clock_in)
        new_co = to_utc_naive(payload.new_clock_out) if payload.new_clock_out else None

        correction = TimeCorrection(
            time_entry_id=entry_id,
            requested_by=requested_by,
            reason=payload.reason,
            original_clock_in=entry.clock_in,
            new_clock_in=new_ci,
            original_clock_out=entry.clock_out,
            new_clock_out=new_co,
            status="pending",
        )
        self._db.add(correction)
        await self._db.flush()

        self._db.add(
            AuditLog(
                entity_type="time_correction",
                entity_id=correction.id,
                action="correction_submitted",
                performed_by=requested_by,
                performed_at=now_utc(),
                details=json.dumps({"entry_id": entry_id, "reason": payload.reason}),
            )
        )

        await self._db.commit()
        await self._db.refresh(correction)
        return correction

    async def review_correction(
        self,
        entry_id: str,
        correction_id: str,
        reviewed_by: str,
        payload: CorrectionReviewRequest,
    ) -> TimeCorrection:
        result = await self._db.execute(
            select(TimeCorrection).where(
                TimeCorrection.id == correction_id,
                TimeCorrection.time_entry_id == entry_id,
            )
        )
        correction = result.scalar_one_or_none()
        if correction is None:
            raise PunchError("Correction not found", 404)
        if correction.status != "pending":
            raise PunchError("Correction has already been reviewed", 409)

        correction.approved_by = reviewed_by
        correction.reviewed_at = now_utc()

        if payload.approve:
            correction.status = "approved"
            entry = await self.get_entry(entry_id)
            entry.clock_in = correction.new_clock_in
            entry.clock_out = correction.new_clock_out
            entry.status = "corrected"
            action = "correction_approved"
        else:
            correction.status = "denied"
            action = "correction_denied"

        self._db.add(
            AuditLog(
                entity_type="time_correction",
                entity_id=correction_id,
                action=action,
                performed_by=reviewed_by,
                performed_at=now_utc(),
                details=json.dumps({"approve": payload.approve}),
            )
        )

        await self._db.commit()
        await self._db.refresh(correction)
        return correction


class AttendanceService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_attendance(
        self,
        company_id: str | None = None,
        employee_id: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        q = select(AttendanceRecord)
        if company_id:
            q = q.where(AttendanceRecord.company_id == company_id)
        if employee_id:
            q = q.where(AttendanceRecord.employee_id == employee_id)

        count_result = await self._db.execute(q)
        total = len(count_result.scalars().all())

        q = q.offset((page - 1) * size).limit(size)
        result = await self._db.execute(q)
        items = result.scalars().all()

        return {"total": total, "page": page, "size": size, "items": list(items)}

    async def get_missing_punches(self, company_id: str | None = None) -> list[TimeEntry]:
        """Return open time entries with clock_in older than 24 hours."""
        cutoff = now_utc() - timedelta(hours=24)
        q = select(TimeEntry).where(
            TimeEntry.status == "open",
            TimeEntry.clock_in < cutoff,
        )
        if company_id:
            q = q.where(TimeEntry.company_id == company_id)
        result = await self._db.execute(q)
        return list(result.scalars().all())
