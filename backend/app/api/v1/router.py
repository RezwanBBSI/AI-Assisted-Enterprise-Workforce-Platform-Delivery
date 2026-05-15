from fastapi import APIRouter
from app.api.v1.endpoints import attendance
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import companies
from app.api.v1.endpoints import employees
from app.api.v1.endpoints import health
from app.api.v1.endpoints import locations
from app.api.v1.endpoints import time_entries

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(time_entries.router, prefix="/time-entries", tags=["time-entries"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
