from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connectivity
    async with engine.begin():
        pass
    yield
    # Shutdown: dispose connection pool
    await engine.dispose()


_description = """
## BBSI Workforce Platform API

### 🔑 Demo Accounts

Use these credentials with `POST /api/v1/auth/login` to get a Bearer token.

| Role | Email | Password |
|------|-------|----------|
| **Admin** | `admin@bbsi.demo` | `Admin1234!` |
| **Manager** | `manager@bbsi.demo` | `Manager1234!` |
| **Employee** | `employee@bbsi.demo` | `Employee1234!` |

> **Tip:** Click **Authorize** (🔒) at the top-right, paste the `access_token` from the login response, and all protected endpoints will include your Bearer token automatically.
"""

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=_description,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}
