from datetime import date, datetime

from pydantic import BaseModel


# ── Compliance Validation ────────────────────────────────────────────────────

class ComplianceRunRequest(BaseModel):
    company_id: str
    pay_period_start: date
    pay_period_end: date


class ComplianceViolationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    employee_id: str
    company_id: str
    violation_type: str
    description: str
    occurred_at: datetime
    resolved: bool
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None
    created_at: datetime


class ViolationResolveRequest(BaseModel):
    resolution_notes: str


class ComplianceRunResult(BaseModel):
    violations_created: int
    violations: list[ComplianceViolationResponse]


# ── Reports ──────────────────────────────────────────────────────────────────

class ComplianceReportResponse(BaseModel):
    company_id: str
    pay_period_start: date
    pay_period_end: date
    total_violations: int
    unresolved: int
    by_type: dict[str, int]
    violations: list[ComplianceViolationResponse]


class AttendanceExceptionItem(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    employee_id: str
    company_id: str
    date: date
    status: str
    time_entry_id: str | None = None


class AttendanceExceptionsResponse(BaseModel):
    company_id: str
    start_date: date
    end_date: date
    total: int
    items: list[AttendanceExceptionItem]


class AuditTrailItem(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    entity_type: str
    entity_id: str
    action: str
    performed_by: str | None = None
    performed_at: datetime
    details: str | None = None


class OperationalReportResponse(BaseModel):
    company_id: str
    pay_period_start: date
    pay_period_end: date
    total_employees: int
    total_regular_hrs: float
    total_ot_hrs: float
    total_absences: int
    total_late_arrivals: int


class CrossCheckEntry(BaseModel):
    employee_id: str
    shift_date: date
    # issue: no_time_entry | hours_mismatch
    issue: str
    scheduled_hours: float | None = None
    actual_hours: float | None = None


class CrossCheckResponse(BaseModel):
    company_id: str
    pay_period_start: date
    pay_period_end: date
    total_discrepancies: int
    entries: list[CrossCheckEntry]
