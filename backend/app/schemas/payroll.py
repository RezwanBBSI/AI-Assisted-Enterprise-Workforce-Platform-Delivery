from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


# ── Generate Request ──────────────────────────────────────────────────────────

class TimesheetGenerateRequest(BaseModel):
    employee_id: str
    company_id: str
    pay_period_start: date
    pay_period_end: date


# ── Line Item ─────────────────────────────────────────────────────────────────

class PayrollLineItemResponse(BaseModel):
    id: str
    timesheet_id: str
    entry_date: date
    hours_worked: float
    rate_type: str
    rate_multiplier: float
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Timesheet ─────────────────────────────────────────────────────────────────

class TimesheetResponse(BaseModel):
    id: str
    employee_id: str
    company_id: str
    pay_period_start: date
    pay_period_end: date
    status: str
    total_regular_hrs: float
    total_ot_hrs: float
    total_holiday_hrs: float
    total_differential_hrs: float
    submitted_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    line_items: list[PayrollLineItemResponse] = []

    model_config = {"from_attributes": True}


# ── Export ────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    export_format: str = "csv"  # csv | json


class PayrollExportResponse(BaseModel):
    id: str
    company_id: str
    pay_period_start: date
    pay_period_end: date
    exported_at: datetime
    exported_by: str
    export_format: str
    record_count: int
    file_name: str

    model_config = {"from_attributes": True}


class ExportDownloadResponse(BaseModel):
    export: PayrollExportResponse
    content: str  # raw CSV or JSON string
