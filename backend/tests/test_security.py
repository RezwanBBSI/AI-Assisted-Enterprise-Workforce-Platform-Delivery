"""Tests for security utilities (JWT + bcrypt) — 100% branch coverage."""
import time
from datetime import datetime, timedelta, timezone

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── password hashing ──────────────────────────────────────────────────────────

def test_hash_is_not_plaintext():
    h = hash_password("mysecret")
    assert h != "mysecret"


def test_verify_correct_password():
    h = hash_password("correct")
    assert verify_password("correct", h) is True


def test_verify_wrong_password():
    h = hash_password("correct")
    assert verify_password("wrong", h) is False


# ── JWT creation & decoding ───────────────────────────────────────────────────

def test_create_and_decode_token():
    token = create_access_token(subject="user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_create_token_with_extra_claims():
    token = create_access_token(subject="user-456", extra_claims={"role": "Admin"})
    payload = decode_token(token)
    assert payload["role"] == "Admin"


def test_create_token_without_extra_claims():
    # Exercises the None branch of extra_claims
    token = create_access_token(subject="user-789", extra_claims=None)
    payload = decode_token(token)
    assert payload["sub"] == "user-789"


def test_decode_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_token("not.a.valid.token")


def test_decode_expired_token_raises():
    expired = jwt.encode(
        {"sub": "x", "exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    with pytest.raises(JWTError):
        decode_token(expired)
