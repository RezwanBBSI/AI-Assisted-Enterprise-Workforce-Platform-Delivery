from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.core.exceptions import PunchError
from app.models.user import User
from app.schemas.company import PaginatedResponse
from app.schemas.compliance import (
    ComplianceRunRequest,
    ComplianceRunResult,
    ComplianceViolationResponse,
    ViolationResolveRequest,
)
from app.services.compliance_service import ComplianceService

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")


# ── Run validation ────────────────────────────────────────────────────────────

@router.post("/validate", response_model=ComplianceRunResult)
async def run_compliance_validation(
    payload: ComplianceRunRequest,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComplianceRunResult:
    svc = ComplianceService(db)
    return await svc.run_validation(
        company_id=payload.company_id,
        pay_period_start=payload.pay_period_start,
        pay_period_end=payload.pay_period_end,
        validated_by=current_user.id,
    )


# ── List violations ───────────────────────────────────────────────────────────

@router.get("/violations", response_model=PaginatedResponse)
async def list_violations(
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: str = Query(...),
    employee_id: Optional[str] = Query(None),
    violation_type: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    svc = ComplianceService(db)
    return await svc.list_violations(
        company_id=company_id,
        employee_id=employee_id,
        violation_type=violation_type,
        resolved=resolved,
        page=page,
        size=size,
    )


# ── Resolve violation ─────────────────────────────────────────────────────────

@router.put("/violations/{violation_id}", response_model=ComplianceViolationResponse)
async def resolve_violation(
    violation_id: str,
    payload: ViolationResolveRequest,
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComplianceViolationResponse:
    svc = ComplianceService(db)
    try:
        return await svc.resolve(
            violation_id=violation_id,
            resolved_by=current_user.id,
            resolution_notes=payload.resolution_notes,
        )
    except PunchError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
