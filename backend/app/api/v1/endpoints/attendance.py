from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.company import PaginatedResponse
from app.schemas.time_entry import AttendanceResponse, TimeEntryResponse
from app.services.time_entry_service import AttendanceService

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")


@router.get(
    "",
    response_model=PaginatedResponse,
    dependencies=[Depends(_manager_or_admin)],
)
async def list_attendance(
    company_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    svc = AttendanceService(db)
    result = await svc.get_attendance(
        company_id=company_id,
        employee_id=employee_id,
        page=page,
        size=size,
    )
    result["items"] = [AttendanceResponse.model_validate(e) for e in result["items"]]
    return result


@router.get(
    "/missing-punches",
    response_model=list[TimeEntryResponse],
    dependencies=[Depends(_manager_or_admin)],
)
async def missing_punches(
    company_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = AttendanceService(db)
    return await svc.get_missing_punches(company_id=company_id)
