from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.location import Location
from app.models.user import User
from app.schemas.company import LocationCreate, LocationResponse, PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
async def list_locations(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("Admin", "Manager"))],
    company_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse:
    query = select(Location)
    count_query = select(func.count()).select_from(Location)
    if company_id:
        query = query.where(Location.company_id == company_id)
        count_query = count_query.where(Location.company_id == company_id)

    total = (await db.execute(count_query)).scalar_one()
    items = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        size=size,
        items=[LocationResponse.model_validate(loc) for loc in items],
    )


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: LocationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role("Admin", "Manager"))],
) -> Location:
    location = Location(
        company_id=payload.company_id,
        name=payload.name,
        timezone=payload.timezone,
    )
    db.add(location)
    await db.commit()
    await db.refresh(location)
    return location
