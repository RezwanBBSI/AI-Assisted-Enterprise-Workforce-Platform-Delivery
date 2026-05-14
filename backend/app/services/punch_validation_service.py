from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PunchError
from app.core.utils import now_utc
from app.models.time_entry import TimeEntry


class PunchValidationService:
    """Stateless validation rules for clock-in and clock-out events."""

    @staticmethod
    async def validate_clock_in(
        db: AsyncSession, employee_id: str, timestamp: datetime
    ) -> None:
        """Raise PunchError if the clock-in is invalid.

        Rules:
        - 422 if timestamp is in the future
        - 409 if employee already has an open entry
        """
        if timestamp > now_utc():
            raise PunchError("Clock-in time cannot be in the future", 422)

        result = await db.execute(
            select(TimeEntry).where(
                TimeEntry.employee_id == employee_id,
                TimeEntry.status == "open",
            )
        )
        if result.scalar_one_or_none() is not None:
            raise PunchError("Employee already has an open time entry", 409)

    @staticmethod
    async def validate_clock_out(
        db: AsyncSession,
        employee_id: str,
        timestamp: datetime,
        open_entry: TimeEntry | None,
    ) -> None:
        """Raise PunchError if the clock-out is invalid.

        Rules:
        - 404 if no open entry exists
        - 422 if timestamp is in the future
        - 422 if clock_out <= clock_in
        """
        if open_entry is None:
            raise PunchError("No open time entry found for this employee", 404)

        if timestamp > now_utc():
            raise PunchError("Clock-out time cannot be in the future", 422)

        if timestamp <= open_entry.clock_in:
            raise PunchError("Clock-out must be after clock-in", 422)
