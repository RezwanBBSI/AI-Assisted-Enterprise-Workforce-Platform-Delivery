from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.exceptions import PunchError
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.company import PaginatedResponse
from app.schemas.payroll import (
    ExportDownloadResponse,
    ExportRequest,
    PayrollExportResponse,
    TimesheetGenerateRequest,
    TimesheetResponse,
)
from app.services.payroll_service import TimesheetService

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")


async def _is_manager_or_admin(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(
        select(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, Role.name.in_(["Manager", "Admin"]))
    )
    return result.first() is not None


# ── Generate ──────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=TimesheetResponse, status_code=201)
async def generate_timesheet(
    payload: TimesheetGenerateRequest,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimesheetResponse:
    svc = TimesheetService(db)
    try:
        ts = await svc.generate(
            employee_id=payload.employee_id,
            company_id=payload.company_id,
            pay_period_start=payload.pay_period_start,
            pay_period_end=payload.pay_period_end,
            requested_by=current_user.id,
        )
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return TimesheetResponse.model_validate(ts)


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse)
async def list_timesheets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    is_privileged = await _is_manager_or_admin(db, current_user.id)
    effective_employee_id = employee_id if is_privileged else current_user.id

    svc = TimesheetService(db)
    result = await svc.list_timesheets(
        employee_id=effective_employee_id,
        company_id=company_id,
        status=status,
        page=page,
        size=size,
    )
    result["items"] = [TimesheetResponse.model_validate(t) for t in result["items"]]
    return result


# ── Get single ────────────────────────────────────────────────────────────────

@router.get("/{timesheet_id}", response_model=TimesheetResponse)
async def get_timesheet(
    timesheet_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimesheetResponse:
    svc = TimesheetService(db)
    ts = await svc.get_timesheet(timesheet_id)
    if ts is None:
        raise HTTPException(status_code=404, detail="Timesheet not found")

    is_privileged = await _is_manager_or_admin(db, current_user.id)
    if not is_privileged and ts.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return TimesheetResponse.model_validate(ts)


# ── Submit ────────────────────────────────────────────────────────────────────

@router.put("/{timesheet_id}/submit", response_model=TimesheetResponse)
async def submit_timesheet(
    timesheet_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimesheetResponse:
    svc = TimesheetService(db)
    try:
        ts = await svc.submit(timesheet_id, submitted_by=current_user.id)
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return TimesheetResponse.model_validate(ts)


# ── Approve ───────────────────────────────────────────────────────────────────

@router.put("/{timesheet_id}/approve", response_model=TimesheetResponse)
async def approve_timesheet(
    timesheet_id: str,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimesheetResponse:
    svc = TimesheetService(db)
    try:
        ts = await svc.approve(timesheet_id, approved_by=current_user.id)
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return TimesheetResponse.model_validate(ts)


# ── Export ────────────────────────────────────────────────────────────────────

@router.post("/{timesheet_id}/export", response_model=ExportDownloadResponse)
async def export_timesheet(
    timesheet_id: str,
    payload: ExportRequest,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExportDownloadResponse:
    svc = TimesheetService(db)
    try:
        pe, content = await svc.export(
            timesheet_id=timesheet_id,
            export_format=payload.export_format,
            exported_by=current_user.id,
        )
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return ExportDownloadResponse(
        export=PayrollExportResponse.model_validate(pe),
        content=content,
    )
