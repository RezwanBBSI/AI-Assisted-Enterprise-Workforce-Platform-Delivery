from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Company schemas ───────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str


class CompanyResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Location schemas ──────────────────────────────────────────────────────────

class LocationCreate(BaseModel):
    company_id: str
    name: str
    timezone: str = "UTC"


class LocationResponse(BaseModel):
    id: str
    company_id: str
    name: str
    timezone: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Pagination wrapper ────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list
