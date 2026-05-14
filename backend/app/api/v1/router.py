from fastapi import APIRouter
from app.api.v1.endpoints import health
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import companies
from app.api.v1.endpoints import locations

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
