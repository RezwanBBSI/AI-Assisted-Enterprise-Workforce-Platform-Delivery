"""
Integration tests for /api/v1/schedules endpoints.
"""
import pytest
from datetime import date, timedelta

from tests.sprint3_helpers import _seed_sprint3


@pytest.fixture()
async def ctx(db_session, client):
    return await _seed_sprint3(db_session, client)


def _auth(ctx, role):
    return {"Authorization": f"Bearer {ctx['tokens'][role]}"}


def _shift_payload(ctx, start="09:00:00", end="17:00:00", break_minutes=60, offset_days=1):
    shift_date = date.today() + timedelta(days=offset_days)
    return {
        "employee_id": ctx["users"]["Employee"],
        "company_id": ctx["company_id"],
        "location_id": ctx["location_id"],
        "shift_date": shift_date.isoformat(),
        "shift_start": start,
        "shift_end": end,
        "break_minutes": break_minutes,
    }


# ── Create ────────────────────────────────────────────────────────────────────

class TestCreateShift:
    async def test_manager_can_create(self, ctx, client):
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 201
        assert r.json()["employee_id"] == ctx["users"]["Employee"]

    async def test_employee_cannot_create(self, ctx, client):
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403

    async def test_unauthenticated_returns_401(self, ctx, client):
        r = await client.post("/api/v1/schedules", json=_shift_payload(ctx))
        assert r.status_code == 401

    # ── Break enforcement ─────────────────────────────────────────────────────

    async def test_short_shift_no_break_ok(self, ctx, client):
        """5hr shift, 0 min break → should pass (≤6hr rule)."""
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx, start="09:00:00", end="14:00:00", break_minutes=0),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 201

    async def test_7hr_shift_no_break_returns_422(self, ctx, client):
        """7hr shift, 0 min break → 422 (needs ≥30 min)."""
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx, start="09:00:00", end="16:00:00", break_minutes=0, offset_days=2),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 422

    async def test_7hr_shift_30min_break_ok(self, ctx, client):
        """7hr shift, 30 min break → should pass."""
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx, start="09:00:00", end="16:00:00", break_minutes=30, offset_days=3),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 201

    async def test_9hr_shift_no_break_returns_422(self, ctx, client):
        """9hr shift, 0 min break → 422 (needs ≥60 min)."""
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx, start="08:00:00", end="17:00:00", break_minutes=0, offset_days=4),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 422

    async def test_9hr_shift_60min_break_ok(self, ctx, client):
        """9hr shift, 60 min break → should pass."""
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx, start="08:00:00", end="17:00:00", break_minutes=60, offset_days=5),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 201


# ── List ──────────────────────────────────────────────────────────────────────

class TestListShifts:
    async def _create(self, ctx, client, offset_days=1):
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx, offset_days=offset_days),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_employee_sees_own_only(self, ctx, client):
        await self._create(ctx, client)
        r = await client.get("/api/v1/schedules", headers=_auth(ctx, "Employee"))
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(s["employee_id"] == ctx["users"]["Employee"] for s in items)

    async def test_manager_sees_all(self, ctx, client):
        await self._create(ctx, client)
        r = await client.get("/api/v1/schedules", headers=_auth(ctx, "Manager"))
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# ── Update / Delete ───────────────────────────────────────────────────────────

class TestUpdateDeleteShift:
    async def _create(self, ctx, client):
        r = await client.post(
            "/api/v1/schedules",
            json=_shift_payload(ctx),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_manager_can_update(self, ctx, client):
        shift_id = await self._create(ctx, client)
        r = await client.put(
            f"/api/v1/schedules/{shift_id}",
            json={"break_minutes": 45},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["break_minutes"] == 45

    async def test_manager_can_delete(self, ctx, client):
        shift_id = await self._create(ctx, client)
        r = await client.delete(
            f"/api/v1/schedules/{shift_id}",
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 204

    async def test_delete_nonexistent_returns_404(self, ctx, client):
        r = await client.delete(
            "/api/v1/schedules/nonexistent-id",
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 404
