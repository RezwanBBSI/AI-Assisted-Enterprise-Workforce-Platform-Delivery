from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.scheduling import PolicyResponse, PolicyUpdate
from app.services.policy_service import PolicyService

router = APIRouter()

_manager_or_admin = require_role("Manager", "Admin")
_admin_only = require_role("Admin")


@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    current_user: Annotated[User, Depends(_manager_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: str = Query(..., description="Company ID"),
) -> list[PolicyResponse]:
    svc = PolicyService(db)
    policies = await svc.list_policies(company_id)
    return [PolicyResponse.model_validate(p) for p in policies]


@router.put("/{policy_key}", response_model=PolicyResponse)
async def upsert_policy(
    policy_key: str,
    payload: PolicyUpdate,
    current_user: Annotated[User, Depends(_admin_only)],
    db: Annotated[AsyncSession, Depends(get_db)],
    company_id: str = Query(..., description="Company ID"),
) -> PolicyResponse:
    svc = PolicyService(db)
    policy = await svc.upsert_policy(
        company_id=company_id,
        policy_key=policy_key,
        payload=payload,
        updated_by=current_user.id,
    )
    return PolicyResponse.model_validate(policy)
