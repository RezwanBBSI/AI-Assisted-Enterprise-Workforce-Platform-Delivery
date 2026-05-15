from datetime import datetime

from pydantic import BaseModel, EmailStr


# ── Request schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Response schemas ─────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployeeRoleInfo(BaseModel):
    company_id: str
    role_name: str

    model_config = {"from_attributes": True}


class EmployeeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    roles: list[EmployeeRoleInfo] = []

    model_config = {"from_attributes": True}
