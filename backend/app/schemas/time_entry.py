from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Clock-in / Clock-out ─────────────────────────────────────────────────────

class ClockInRequest(BaseModel):
    company_id: str
    location_id: Optional[str] = None
    timestamp: Optional[datetime] = None  # defaults to server now() UTC


class ClockOutRequest(BaseModel):
    timestamp: Optional[datetime] = None  # defaults to server now() UTC


# ── Time entry response ───────────────────────────────────────────────────────

class TimeEntryResponse(BaseModel):
    id: str
    employee_id: str
    company_id: str
    location_id: Optional[str]
    clock_in: datetime
    clock_out: Optional[datetime]
    status: str
    break_minutes: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Correction schemas ────────────────────────────────────────────────────────

class CorrectionRequest(BaseModel):
    reason: str
    new_clock_in: datetime
    new_clock_out: Optional[datetime] = None


class CorrectionReviewRequest(BaseModel):
    approve: bool


class CorrectionResponse(BaseModel):
    id: str
    time_entry_id: str
    requested_by: str
    approved_by: Optional[str]
    reason: str
    original_clock_in: datetime
    new_clock_in: datetime
    original_clock_out: Optional[datetime]
    new_clock_out: Optional[datetime]
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Attendance schemas ────────────────────────────────────────────────────────

class AttendanceResponse(BaseModel):
    id: str
    employee_id: str
    company_id: str
    date: datetime  # returned as ISO date string; Date stored as datetime at midnight
    status: str
    time_entry_id: Optional[str]

    model_config = {"from_attributes": True}
