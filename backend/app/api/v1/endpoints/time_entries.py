from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.exceptions import PunchError
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.company import PaginatedResponse
from app.schemas.time_entry import (
    ClockInRequest,
    ClockOutRequest,
    CorrectionRequest,
    CorrectionResponse,
    CorrectionReviewRequest,
    TimeEntryResponse,
)
from app.services.time_entry_service import TimeEntryService

router = APIRouter()


async def _is_manager_or_admin(db: AsyncSession, user_id: str) -> bool:
    """Return True if the user has Manager or Admin role in any company."""
    result = await db.execute(
        select(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, Role.name.in_(["Manager", "Admin"]))
    )
    return result.first() is not None


@router.post("/clock-in", response_model=TimeEntryResponse, status_code=201)
async def clock_in(
    payload: ClockInRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TimeEntryService(db)
    try:
        entry = await svc.clock_in(
            employee_id=current_user.id,
            company_id=payload.company_id,
            location_id=payload.location_id,
            timestamp=payload.timestamp,
        )
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return entry


@router.post("/clock-out", response_model=TimeEntryResponse, status_code=200)
async def clock_out(
    payload: ClockOutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TimeEntryService(db)
    try:
        entry = await svc.clock_out(
            employee_id=current_user.id,
            timestamp=payload.timestamp,
        )
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return entry


@router.get("", response_model=PaginatedResponse)
async def list_time_entries(
    employee_id: Optional[str] = None,
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Employees may only see their own entries
    if not await _is_manager_or_admin(db, current_user.id):
        employee_id = current_user.id

    svc = TimeEntryService(db)
    result = await svc.get_entries(
        employee_id=employee_id,
        company_id=company_id,
        status=status,
        page=page,
        size=size,
    )
    result["items"] = [TimeEntryResponse.model_validate(e) for e in result["items"]]
    return result


@router.get("/{entry_id}", response_model=TimeEntryResponse)
async def get_time_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TimeEntryService(db)
    entry = await svc.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    if not await _is_manager_or_admin(db, current_user.id):
        if entry.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    return entry


@router.post("/{entry_id}/correction", response_model=CorrectionResponse, status_code=201)
async def submit_correction(
    entry_id: str,
    payload: CorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TimeEntryService(db)
    try:
        correction = await svc.submit_correction(
            entry_id=entry_id,
            requested_by=current_user.id,
            payload=payload,
        )
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return correction


@router.put(
    "/{entry_id}/correction/{correction_id}",
    response_model=CorrectionResponse,
    dependencies=[Depends(require_role("Manager", "Admin"))],
)
async def review_correction(
    entry_id: str,
    correction_id: str,
    payload: CorrectionReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = TimeEntryService(db)
    try:
        correction = await svc.review_correction(
            entry_id=entry_id,
            correction_id=correction_id,
            reviewed_by=current_user.id,
            payload=payload,
        )
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return correction
