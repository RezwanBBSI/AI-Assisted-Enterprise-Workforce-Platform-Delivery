from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel


# ── Leave Request ─────────────────────────────────────────────────────────────

class LeaveRequestCreate(BaseModel):
    company_id: str
    leave_type: str  # pto | sick | comp | unpaid
    start_date: date
    end_date: date
    days_requested: float
    reason: Optional[str] = None


class LeaveReviewRequest(BaseModel):
    approve: bool
    review_comment: Optional[str] = None


class LeaveRequestResponse(BaseModel):
    id: str
    employee_id: str
    company_id: str
    leave_type: str
    start_date: date
    end_date: date
    days_requested: float
    reason: Optional[str]
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    review_comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Leave Balance ─────────────────────────────────────────────────────────────

class LeaveBalanceResponse(BaseModel):
    id: str
    employee_id: str
    company_id: str
    year: int
    pto_total: float
    pto_used: float
    sick_total: float
    sick_used: float
    comp_earned: float
    comp_used: float
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Shift Schedule ────────────────────────────────────────────────────────────

class ShiftCreate(BaseModel):
    employee_id: str
    company_id: str
    location_id: Optional[str] = None
    shift_date: date
    shift_start: time
    shift_end: time
    break_minutes: int = 0


class ShiftUpdate(BaseModel):
    location_id: Optional[str] = None
    shift_date: Optional[date] = None
    shift_start: Optional[time] = None
    shift_end: Optional[time] = None
    break_minutes: Optional[int] = None


class ShiftResponse(BaseModel):
    id: str
    employee_id: str
    company_id: str
    location_id: Optional[str]
    shift_date: date
    shift_start: time
    shift_end: time
    break_minutes: int
    created_by: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Company Policy ────────────────────────────────────────────────────────────

class PolicyUpdate(BaseModel):
    policy_value: str  # raw JSON string


class PolicyResponse(BaseModel):
    id: str
    company_id: str
    policy_key: str
    policy_value: str
    updated_by: Optional[str]
    updated_at: datetime

    model_config = {"from_attributes": True}
