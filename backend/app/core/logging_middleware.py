"""
Structured JSON logging middleware.

Every request produces a single log line:
  {"timestamp": ..., "level": ..., "request_id": ..., "user_id": ...,
   "method": ..., "path": ..., "status": ..., "duration_ms": ...}

5XX responses additionally log the full traceback under "error".
The request_id is also returned in the X-Request-ID response header.
"""

import json
import logging
import time
import traceback
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("workforce.access")


class RequestIDLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Attempt to extract user_id from JWT claims already parsed by deps
        # It won't be available at middleware level unless already decoded,
        # so we store it on request.state and read it back after the route runs.
        request.state.user_id = None

        start = time.perf_counter()
        exc_text: str | None = None

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            exc_text = traceback.format_exc()
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            _emit(
                request_id=request_id,
                user_id=getattr(request.state, "user_id", None),
                method=request.method,
                path=request.url.path,
                status=500,
                duration_ms=duration_ms,
                error=exc_text,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        status = response.status_code

        if status >= 500:
            # Capture body for 5XX enrichment (streaming-safe best-effort)
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk
            try:
                body_json = json.loads(body_bytes)
                error_detail = body_json.get("detail", body_bytes.decode(errors="replace"))
            except Exception:
                error_detail = body_bytes.decode(errors="replace")

            _emit(
                request_id=request_id,
                user_id=getattr(request.state, "user_id", None),
                method=request.method,
                path=request.url.path,
                status=status,
                duration_ms=duration_ms,
                error=error_detail,
            )
            # Rebuild response with consumed body
            response = Response(
                content=body_bytes,
                status_code=status,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        else:
            _emit(
                request_id=request_id,
                user_id=getattr(request.state, "user_id", None),
                method=request.method,
                path=request.url.path,
                status=status,
                duration_ms=duration_ms,
            )

        response.headers["X-Request-ID"] = request_id
        return response


def _emit(
    *,
    request_id: str,
    user_id: str | None,
    method: str,
    path: str,
    status: int,
    duration_ms: float,
    error: str | None = None,
) -> None:
    level = "ERROR" if status >= 500 else "WARNING" if status >= 400 else "INFO"
    record: dict = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": level,
        "request_id": request_id,
        "user_id": user_id,
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": duration_ms,
    }
    if error is not None:
        record["error"] = error

    log_fn = logger.error if level == "ERROR" else logger.warning if level == "WARNING" else logger.info
    log_fn(json.dumps(record))
