"""
Integration tests for /api/v1/time-entries endpoints.
"""
import pytest
from datetime import timedelta

from app.core.utils import now_utc
from tests.sprint2_helpers import _seed_sprint2


@pytest.fixture()
async def ctx(db_session, client):
    return await _seed_sprint2(db_session, client)


def _auth(ctx, role):
    return {"Authorization": f"Bearer {ctx['tokens'][role]}"}


# ── Clock-in ──────────────────────────────────────────────────────────────────

class TestClockIn:
    async def test_employee_can_clock_in(self, ctx, client):
        r = await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "open"
        assert data["clock_out"] is None

    async def test_clock_in_with_location(self, ctx, client):
        r = await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"], "location_id": ctx["location_id"]},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201
        assert r.json()["location_id"] == ctx["location_id"]

    async def test_double_clock_in_returns_409(self, ctx, client):
        headers = _auth(ctx, "Employee")
        payload = {"company_id": ctx["company_id"]}
        r1 = await client.post("/api/v1/time-entries/clock-in", json=payload, headers=headers)
        assert r1.status_code == 201
        r2 = await client.post("/api/v1/time-entries/clock-in", json=payload, headers=headers)
        assert r2.status_code == 409

    async def test_future_clock_in_returns_422(self, ctx, client):
        future_ts = (now_utc() + timedelta(hours=1)).isoformat()
        r = await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"], "timestamp": future_ts},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 422

    async def test_unauthenticated_clock_in_returns_401(self, ctx, client):
        r = await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
        )
        assert r.status_code == 401


# ── Clock-out ─────────────────────────────────────────────────────────────────

class TestClockOut:
    async def _clock_in(self, ctx, client):
        r = await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201
        return r.json()

    async def test_employee_can_clock_out(self, ctx, client):
        await self._clock_in(ctx, client)
        r = await client.post(
            "/api/v1/time-entries/clock-out",
            json={},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "closed"

    async def test_clock_out_without_open_entry_returns_404(self, ctx, client):
        r = await client.post(
            "/api/v1/time-entries/clock-out",
            json={},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 404


# ── List / get entries ────────────────────────────────────────────────────────

class TestListEntries:
    async def test_employee_sees_own_entries_only(self, ctx, client):
        # Clock in as Employee
        ci = await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        assert ci.status_code == 201

        r = await client.get("/api/v1/time-entries", headers=_auth(ctx, "Employee"))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1

    async def test_manager_can_see_all_entries(self, ctx, client):
        # Create entry as employee
        await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        r = await client.get("/api/v1/time-entries", headers=_auth(ctx, "Manager"))
        assert r.status_code == 200

    async def test_get_entry_by_id(self, ctx, client):
        ci = await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        entry_id = ci.json()["id"]
        r = await client.get(f"/api/v1/time-entries/{entry_id}", headers=_auth(ctx, "Employee"))
        assert r.status_code == 200
        assert r.json()["id"] == entry_id

    async def test_employee_cannot_see_other_entry(self, ctx, client):
        # Admin creates an entry
        ci = await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Admin"),
        )
        entry_id = ci.json()["id"]
        # Employee tries to get it
        r = await client.get(f"/api/v1/time-entries/{entry_id}", headers=_auth(ctx, "Employee"))
        assert r.status_code == 403

    async def test_get_nonexistent_entry_returns_404(self, ctx, client):
        r = await client.get(
            "/api/v1/time-entries/00000000-0000-0000-0000-000000000000",
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 404


# ── Corrections ───────────────────────────────────────────────────────────────

class TestCorrections:
    async def _closed_entry(self, ctx, client):
        await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        co = await client.post(
            "/api/v1/time-entries/clock-out",
            json={},
            headers=_auth(ctx, "Employee"),
        )
        return co.json()

    async def test_employee_can_submit_correction(self, ctx, client):
        entry = await self._closed_entry(ctx, client)
        from app.core.utils import now_utc
        past = (now_utc() - timedelta(hours=2)).isoformat()
        r = await client.post(
            f"/api/v1/time-entries/{entry['id']}/correction",
            json={"reason": "missed punch", "new_clock_in": past},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201
        assert r.json()["status"] == "pending"

    async def test_manager_can_approve_correction(self, ctx, client):
        entry = await self._closed_entry(ctx, client)
        past = (now_utc() - timedelta(hours=2)).isoformat()
        correction = await client.post(
            f"/api/v1/time-entries/{entry['id']}/correction",
            json={"reason": "missed", "new_clock_in": past},
            headers=_auth(ctx, "Employee"),
        )
        cid = correction.json()["id"]

        r = await client.put(
            f"/api/v1/time-entries/{entry['id']}/correction/{cid}",
            json={"approve": True},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    async def test_employee_cannot_review_correction(self, ctx, client):
        entry = await self._closed_entry(ctx, client)
        past = (now_utc() - timedelta(hours=2)).isoformat()
        correction = await client.post(
            f"/api/v1/time-entries/{entry['id']}/correction",
            json={"reason": "oops", "new_clock_in": past},
            headers=_auth(ctx, "Employee"),
        )
        cid = correction.json()["id"]
        r = await client.put(
            f"/api/v1/time-entries/{entry['id']}/correction/{cid}",
            json={"approve": True},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403
