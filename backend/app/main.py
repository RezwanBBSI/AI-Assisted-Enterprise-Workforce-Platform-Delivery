from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine
from app.core.limiter import limiter
from app.api.v1.router import api_router

# ── Rate limiter ──────────────────────────────────────────────────────────────
# limiter is defined in app/core/limiter.py to avoid circular imports


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

# ── Attach rate limiter to app state ─────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Content-Type enforcement middleware ───────────────────────────────────────

_WRITE_METHODS = {"POST", "PUT", "PATCH"}
_EXEMPT_PATHS = {"/health", f"{settings.API_V1_STR}/health"}


@app.middleware("http")
async def enforce_json_content_type(request: Request, call_next) -> Response:
    """Reject POST/PUT/PATCH requests that don't declare application/json."""
    if request.method in _WRITE_METHODS and request.url.path not in _EXEMPT_PATHS:
        ct = request.headers.get("content-type", "")
        if ct and "application/json" not in ct:
            return Response(
                content='{"detail": "Content-Type must be application/json"}',
                status_code=415,
                media_type="application/json",
            )
    return await call_next(request)
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
