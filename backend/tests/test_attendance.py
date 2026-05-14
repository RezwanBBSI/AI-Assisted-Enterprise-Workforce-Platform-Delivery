"""
Integration tests for /api/v1/attendance endpoints.
"""
import pytest

from tests.sprint2_helpers import _seed_sprint2


@pytest.fixture()
async def ctx(db_session, client):
    return await _seed_sprint2(db_session, client)


def _auth(ctx, role):
    return {"Authorization": f"Bearer {ctx['tokens'][role]}"}


class TestAttendance:
    async def test_manager_can_list_attendance(self, ctx, client):
        # Create an entry first so attendance record exists
        await client.post(
            "/api/v1/time-entries/clock-in",
            json={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        r = await client.get("/api/v1/attendance", headers=_auth(ctx, "Manager"))
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

    async def test_employee_cannot_list_attendance(self, ctx, client):
        r = await client.get("/api/v1/attendance", headers=_auth(ctx, "Employee"))
        assert r.status_code == 403

    async def test_missing_punches_empty_when_none(self, ctx, client):
        r = await client.get("/api/v1/attendance/missing-punches", headers=_auth(ctx, "Manager"))
        assert r.status_code == 200
        assert r.json() == []

    async def test_unauthenticated_returns_401(self, ctx, client):
        r = await client.get("/api/v1/attendance")
        assert r.status_code == 401
