import json
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PunchError
from app.core.utils import now_utc
from app.models.audit_log import AuditLog
from app.models.shift_schedule import ShiftSchedule
from app.schemas.scheduling import ShiftCreate, ShiftUpdate


class ScheduleService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Break enforcement — 100% branch coverage required ────────────────────

    @staticmethod
    def _validate_break(
        shift_start: time,
        shift_end: time,
        break_minutes: int,
    ) -> None:
        """
        Oregon break rules:
        - ≤ 6 hrs  → no minimum break required
        - 6–8 hrs  → at least 30 min break
        - > 8 hrs  → at least 60 min break
        """
        # Compute shift duration in hours
        start_dt = datetime.combine(date.today(), shift_start)
        end_dt = datetime.combine(date.today(), shift_end)
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)  # overnight shift
        duration_hours = (end_dt - start_dt).total_seconds() / 3600

        if duration_hours <= 6:
            return  # no minimum
        elif duration_hours <= 8:
            if break_minutes < 30:
                raise PunchError(
                    f"Shifts between 6 and 8 hours require at least 30 minutes break "
                    f"(got {break_minutes} min)",
                    422,
                )
        else:
            if break_minutes < 60:
                raise PunchError(
                    f"Shifts over 8 hours require at least 60 minutes break "
                    f"(got {break_minutes} min)",
                    422,
                )

    # ── CRUD ──────────────────────────────────────────────────────────────────

    async def create(self, payload: ShiftCreate, created_by: str) -> ShiftSchedule:
        self._validate_break(payload.shift_start, payload.shift_end, payload.break_minutes)

        shift = ShiftSchedule(
            employee_id=payload.employee_id,
            company_id=payload.company_id,
            location_id=payload.location_id,
            shift_date=payload.shift_date,
            shift_start=payload.shift_start,
            shift_end=payload.shift_end,
            break_minutes=payload.break_minutes,
            created_by=created_by,
        )
        self._db.add(shift)
        await self._db.flush()

        self._db.add(AuditLog(
            entity_type="shift_schedule",
            entity_id=shift.id,
            action="shift_created",
            performed_by=created_by,
            performed_at=now_utc(),
            details=json.dumps({
                "employee_id": payload.employee_id,
                "shift_date": str(payload.shift_date),
            }),
        ))

        await self._db.commit()
        await self._db.refresh(shift)
        return shift

    async def list_shifts(
        self,
        employee_id: str | None = None,
        company_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        q = select(ShiftSchedule)
        if employee_id:
            q = q.where(ShiftSchedule.employee_id == employee_id)
        if company_id:
            q = q.where(ShiftSchedule.company_id == company_id)
        if date_from:
            q = q.where(ShiftSchedule.shift_date >= date_from)
        if date_to:
            q = q.where(ShiftSchedule.shift_date <= date_to)

        count_result = await self._db.execute(q)
        total = len(count_result.scalars().all())

        items = (
            await self._db.execute(q.offset((page - 1) * size).limit(size))
        ).scalars().all()

        return {"total": total, "page": page, "size": size, "items": list(items)}

    async def get_shift(self, shift_id: str) -> ShiftSchedule | None:
        result = await self._db.execute(
            select(ShiftSchedule).where(ShiftSchedule.id == shift_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self, shift_id: str, payload: ShiftUpdate, updated_by: str
    ) -> ShiftSchedule:
        shift = await self.get_shift(shift_id)
        if shift is None:
            raise PunchError("Shift not found", 404)

        # Apply only provided fields
        new_start = payload.shift_start if payload.shift_start is not None else shift.shift_start
        new_end = payload.shift_end if payload.shift_end is not None else shift.shift_end
        new_break = payload.break_minutes if payload.break_minutes is not None else shift.break_minutes

        self._validate_break(new_start, new_end, new_break)

        if payload.location_id is not None:
            shift.location_id = payload.location_id
        if payload.shift_date is not None:
            shift.shift_date = payload.shift_date
        shift.shift_start = new_start
        shift.shift_end = new_end
        shift.break_minutes = new_break

        self._db.add(AuditLog(
            entity_type="shift_schedule",
            entity_id=shift_id,
            action="shift_updated",
            performed_by=updated_by,
            performed_at=now_utc(),
            details="{}",
        ))

        await self._db.commit()
        await self._db.refresh(shift)
        return shift

    async def delete(self, shift_id: str, deleted_by: str) -> None:
        shift = await self.get_shift(shift_id)
        if shift is None:
            raise PunchError("Shift not found", 404)

        self._db.add(AuditLog(
            entity_type="shift_schedule",
            entity_id=shift_id,
            action="shift_deleted",
            performed_by=deleted_by,
            performed_at=now_utc(),
            details="{}",
        ))

        await self._db.delete(shift)
        await self._db.commit()
