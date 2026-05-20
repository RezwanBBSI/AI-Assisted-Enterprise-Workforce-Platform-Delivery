from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.models.user import User
from sqlalchemy import select

from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse, UserRoleInfo
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    try:
        return await AuthService(db).register(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("30/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user = await AuthService(db).authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = AuthService.issue_token(user)
    return TokenResponse(access_token=token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_user)],
) -> TokenResponse:
    token = AuthService.issue_token(current_user)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    rows = await db.execute(
        select(UserRole, Role)
        .join(Role, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    roles = [
        UserRoleInfo(company_id=ur.company_id, role_name=role.name)
        for ur, role in rows.all()
    ]
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        roles=roles,
    )
