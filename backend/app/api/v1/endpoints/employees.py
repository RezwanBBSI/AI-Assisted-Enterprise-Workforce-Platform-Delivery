from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.models.user_role import UserRole
from app.schemas.auth import EmployeeResponse, EmployeeRoleInfo
from app.schemas.company import PaginatedResponse

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")


def _to_employee_response(user: User) -> EmployeeResponse:
    roles = [
        EmployeeRoleInfo(company_id=ur.company_id, role_name=ur.role.name)
        for ur in user.user_roles
    ]
    return EmployeeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        roles=roles,
    )


@router.get("", response_model=PaginatedResponse)
async def list_employees(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(_manager_or_admin)],
    company_id: str | None = Query(None, description="Filter by company ID"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    base_query = (
        select(User)
        .join(UserRole, UserRole.user_id == User.id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .distinct()
    )
    count_query = (
        select(func.count())
        .select_from(User)
        .join(UserRole, UserRole.user_id == User.id)
    )

    if company_id:
        base_query = base_query.where(UserRole.company_id == company_id)
        count_query = count_query.where(UserRole.company_id == company_id)

    total = (await db.execute(count_query)).scalar_one()
    users = (
        await db.execute(base_query.offset((page - 1) * size).limit(size))
    ).scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        size=size,
        items=[_to_employee_response(u) for u in users],
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(_manager_or_admin)],
) -> EmployeeResponse:
    result = await db.execute(
        select(User)
        .where(User.id == employee_id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    return _to_employee_response(user)
