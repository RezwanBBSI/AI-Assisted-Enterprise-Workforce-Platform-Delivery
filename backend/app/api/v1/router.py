from fastapi import APIRouter
from app.api.v1.endpoints import attendance
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import companies
from app.api.v1.endpoints import employees
from app.api.v1.endpoints import health
from app.api.v1.endpoints import leave_balances
from app.api.v1.endpoints import leave_requests
from app.api.v1.endpoints import locations
from app.api.v1.endpoints import policies
from app.api.v1.endpoints import schedules
from app.api.v1.endpoints import time_entries
from app.api.v1.endpoints import timesheets
from app.api.v1.endpoints import compliance
from app.api.v1.endpoints import reports

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(time_entries.router, prefix="/time-entries", tags=["time-entries"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(leave_requests.router, prefix="/leave-requests", tags=["leave-requests"])
api_router.include_router(leave_balances.router, prefix="/leave-balances", tags=["leave-balances"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(timesheets.router, prefix="/timesheets", tags=["timesheets"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
