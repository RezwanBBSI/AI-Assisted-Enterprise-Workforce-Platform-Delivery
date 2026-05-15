from datetime import date
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
from app.schemas.scheduling import ShiftCreate, ShiftResponse, ShiftUpdate
from app.services.schedule_service import ScheduleService

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")


async def _is_manager_or_admin(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(
        select(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, Role.name.in_(["Manager", "Admin"]))
    )
    return result.first() is not None


@router.post("", response_model=ShiftResponse, status_code=201)
async def create_shift(
    payload: ShiftCreate,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShiftResponse:
    svc = ScheduleService(db)
    try:
        shift = await svc.create(payload, created_by=current_user.id)
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return ShiftResponse.model_validate(shift)


@router.get("", response_model=PaginatedResponse)
async def list_shifts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    is_privileged = await _is_manager_or_admin(db, current_user.id)
    effective_employee_id = employee_id if is_privileged else current_user.id

    svc = ScheduleService(db)
    result = await svc.list_shifts(
        employee_id=effective_employee_id,
        company_id=company_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )
    result["items"] = [ShiftResponse.model_validate(s) for s in result["items"]]
    return result


@router.put("/{shift_id}", response_model=ShiftResponse)
async def update_shift(
    shift_id: str,
    payload: ShiftUpdate,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShiftResponse:
    svc = ScheduleService(db)
    try:
        shift = await svc.update(shift_id, payload, updated_by=current_user.id)
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return ShiftResponse.model_validate(shift)


@router.delete("/{shift_id}", status_code=204)
async def delete_shift(
    shift_id: str,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = ScheduleService(db)
    try:
        await svc.delete(shift_id, deleted_by=current_user.id)
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
