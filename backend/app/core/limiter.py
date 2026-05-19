"""
Shared rate-limiter instance.

Defined here (not in app/main.py) to avoid circular imports between
main.py → api_router → endpoints/auth.py.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _rate_limit_key(request: Request) -> str:
    """Use X-Real-IP when present (proxy / test override); else real remote addr."""
    return request.headers.get("X-Real-IP") or get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)
