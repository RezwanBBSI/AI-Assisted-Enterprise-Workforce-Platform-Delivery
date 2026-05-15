from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role
from app.schemas.scheduling import LeaveBalanceResponse
from app.services.leave_service import LeaveBalanceService

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")


async def _is_manager_or_admin(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(
        select(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .where(UserRole.user_id == user_id, Role.name.in_(["Manager", "Admin"]))
    )
    return result.first() is not None


@router.get("/{employee_id}", response_model=LeaveBalanceResponse)
async def get_leave_balance(
    employee_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: str = Query(..., description="Company ID to look up balance for"),
    year: Optional[int] = Query(None, description="Year (defaults to current year)"),
) -> LeaveBalanceResponse:
    # Employees may only view their own balance
    is_privileged = await _is_manager_or_admin(db, current_user.id)
    if not is_privileged and current_user.id != employee_id:
        raise HTTPException(status_code=403, detail="Access denied")

    effective_year = year or datetime.utcnow().year
    svc = LeaveBalanceService(db)
    balance = await svc.get_balance(employee_id, company_id, effective_year)
    return LeaveBalanceResponse.model_validate(balance)
