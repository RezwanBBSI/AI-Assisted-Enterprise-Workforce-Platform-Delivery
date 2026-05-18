from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.company import PaginatedResponse
from app.schemas.compliance import (
    AttendanceExceptionsResponse,
    ComplianceReportResponse,
    CrossCheckResponse,
    OperationalReportResponse,
)
from app.services.report_service import ReportService

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")
_admin_only = require_role("Admin")


# ── Compliance report ─────────────────────────────────────────────────────────

@router.get("/compliance", response_model=ComplianceReportResponse)
async def compliance_report(
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: str = Query(...),
    pay_period_start: date = Query(...),
    pay_period_end: date = Query(...),
) -> ComplianceReportResponse:
    svc = ReportService(db)
    return await svc.compliance_report(company_id, pay_period_start, pay_period_end)


# ── Attendance exceptions ─────────────────────────────────────────────────────

@router.get("/attendance-exceptions", response_model=AttendanceExceptionsResponse)
async def attendance_exceptions(
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: str = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> AttendanceExceptionsResponse:
    svc = ReportService(db)
    return await svc.attendance_exceptions(company_id, start_date, end_date)


# ── Audit trail ───────────────────────────────────────────────────────────────

@router.get("/audit-trail", response_model=PaginatedResponse)
async def audit_trail(
    current_user: Annotated[User, Depends(_admin_only)],
    db: Annotated[AsyncSession, Depends(get_db)],
    entity_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    svc = ReportService(db)
    return await svc.audit_trail(entity_type, start_date, end_date, page, size)


# ── Operational report ────────────────────────────────────────────────────────

@router.get("/operational", response_model=OperationalReportResponse)
async def operational_report(
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: str = Query(...),
    pay_period_start: date = Query(...),
    pay_period_end: date = Query(...),
) -> OperationalReportResponse:
    svc = ReportService(db)
    return await svc.operational_report(company_id, pay_period_start, pay_period_end)


# ── Cross-check report ────────────────────────────────────────────────────────

@router.get("/crosscheck", response_model=CrossCheckResponse)
async def crosscheck_report(
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: str = Query(...),
    pay_period_start: date = Query(...),
    pay_period_end: date = Query(...),
) -> CrossCheckResponse:
    svc = ReportService(db)
    return await svc.crosscheck(company_id, pay_period_start, pay_period_end)
