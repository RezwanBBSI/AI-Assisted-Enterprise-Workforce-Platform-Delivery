from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.exceptions import PunchError
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role
from app.schemas.company import PaginatedResponse
from app.schemas.scheduling import LeaveRequestCreate, LeaveRequestResponse, LeaveReviewRequest
from app.services.leave_service import LeaveService
from sqlalchemy import select

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")


async def _is_manager_or_admin(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(
        select(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, Role.name.in_(["Manager", "Admin"]))
    )
    return result.first() is not None


@router.post("", response_model=LeaveRequestResponse, status_code=201)
async def submit_leave_request(
    payload: LeaveRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeaveRequestResponse:
    svc = LeaveService(db)
    try:
        req = await svc.submit(current_user.id, payload.company_id, payload)
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return LeaveRequestResponse.model_validate(req)


@router.get("", response_model=PaginatedResponse)
async def list_leave_requests(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    is_privileged = await _is_manager_or_admin(db, current_user.id)
    # Employees may only see their own requests
    effective_employee_id = employee_id if is_privileged else current_user.id

    svc = LeaveService(db)
    result = await svc.list_requests(
        employee_id=effective_employee_id,
        company_id=company_id,
        status=status,
        page=page,
        size=size,
    )
    result["items"] = [LeaveRequestResponse.model_validate(r) for r in result["items"]]
    return result


@router.put("/{request_id}/review", response_model=LeaveRequestResponse)
async def review_leave_request(
    request_id: str,
    payload: LeaveReviewRequest,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeaveRequestResponse:
    svc = LeaveService(db)
    try:
        req = await svc.review(request_id, current_user.id, payload)
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return LeaveRequestResponse.model_validate(req)


@router.put("/{request_id}/cancel", response_model=LeaveRequestResponse)
async def cancel_leave_request(
    request_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeaveRequestResponse:
    svc = LeaveService(db)
    try:
        req = await svc.cancel(request_id, current_user.id)
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    return LeaveRequestResponse.model_validate(req)
