"""
Tests for PunchValidationService — targets 100% branch coverage.
"""
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions import PunchError
from app.core.utils import now_utc
from app.services.punch_validation_service import PunchValidationService


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_db(open_entry=None):
    """Return a mock AsyncSession whose execute().scalar_one_or_none() returns open_entry."""
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none = MagicMock(return_value=open_entry)
    execute_result = AsyncMock(return_value=scalar_result)
    db = MagicMock()
    db.execute = execute_result
    return db


def _past(seconds=30):
    return now_utc() - timedelta(seconds=seconds)


def _future(seconds=60):
    return now_utc() + timedelta(seconds=seconds)


def _open_entry(clock_in_offset_seconds=120):
    entry = MagicMock()
    entry.clock_in = now_utc() - timedelta(seconds=clock_in_offset_seconds)
    return entry


# ── validate_clock_in ─────────────────────────────────────────────────────────

class TestValidateClockIn:
    async def test_future_timestamp_raises_422(self):
        db = _make_db(open_entry=None)
        with pytest.raises(PunchError) as exc_info:
            await PunchValidationService.validate_clock_in(db, "uid", _future())
        assert exc_info.value.status_code == 422

    async def test_already_open_raises_409(self):
        db = _make_db(open_entry=_open_entry())
        with pytest.raises(PunchError) as exc_info:
            await PunchValidationService.validate_clock_in(db, "uid", _past())
        assert exc_info.value.status_code == 409

    async def test_valid_clock_in_passes(self):
        db = _make_db(open_entry=None)
        # Should not raise
        await PunchValidationService.validate_clock_in(db, "uid", _past())


# ── validate_clock_out ────────────────────────────────────────────────────────

class TestValidateClockOut:
    async def test_no_open_entry_raises_404(self):
        db = _make_db()
        with pytest.raises(PunchError) as exc_info:
            await PunchValidationService.validate_clock_out(db, "uid", _past(), None)
        assert exc_info.value.status_code == 404

    async def test_future_timestamp_raises_422(self):
        db = _make_db()
        with pytest.raises(PunchError) as exc_info:
            await PunchValidationService.validate_clock_out(db, "uid", _future(), _open_entry())
        assert exc_info.value.status_code == 422

    async def test_clock_out_before_clock_in_raises_422(self):
        db = _make_db()
        entry = _open_entry(clock_in_offset_seconds=10)  # clock_in = now - 10s
        clock_out = now_utc() - timedelta(seconds=60)     # clock_out = now - 60s (before clock_in)
        with pytest.raises(PunchError) as exc_info:
            await PunchValidationService.validate_clock_out(db, "uid", clock_out, entry)
        assert exc_info.value.status_code == 422

    async def test_valid_clock_out_passes(self):
        db = _make_db()
        entry = _open_entry(clock_in_offset_seconds=120)
        clock_out = now_utc() - timedelta(seconds=10)
        # Should not raise
        await PunchValidationService.validate_clock_out(db, "uid", clock_out, entry)
