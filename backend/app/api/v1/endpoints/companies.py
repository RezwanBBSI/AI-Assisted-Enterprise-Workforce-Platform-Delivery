from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_companies(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("Admin"))],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    total_result = await db.execute(select(func.count()).select_from(Company))
    total = total_result.scalar_one()

    result = await db.execute(
        select(Company).offset((page - 1) * size).limit(size)
    )
    companies = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        size=size,
        items=[CompanyResponse.model_validate(c) for c in companies],
    )


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("Admin"))],
) -> Company:
    company = Company(name=payload.name)
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company
