"""
Integration tests for /api/v1/leave-requests endpoints.
"""
import pytest
from datetime import date, timedelta

from tests.sprint3_helpers import _seed_sprint3


@pytest.fixture()
async def ctx(db_session, client):
    return await _seed_sprint3(db_session, client)


def _auth(ctx, role):
    return {"Authorization": f"Bearer {ctx['tokens'][role]}"}


def _leave_payload(ctx, leave_type="pto", days=1.0, offset_days=7):
    start = date.today() + timedelta(days=offset_days)
    end = start + timedelta(days=int(days) - 1)
    return {
        "company_id": ctx["company_id"],
        "leave_type": leave_type,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days_requested": days,
        "reason": "Test leave",
    }


# ── Submit ────────────────────────────────────────────────────────────────────

class TestSubmitLeave:
    async def test_employee_can_submit(self, ctx, client):
        r = await client.post(
            "/api/v1/leave-requests",
            json=_leave_payload(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["status"] == "pending"
        assert data["leave_type"] == "pto"

    async def test_over_balance_returns_422(self, ctx, client):
        r = await client.post(
            "/api/v1/leave-requests",
            json=_leave_payload(ctx, days=99.0),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 422

    async def test_end_before_start_returns_422(self, ctx, client):
        payload = {
            "company_id": ctx["company_id"],
            "leave_type": "pto",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() - timedelta(days=1)).isoformat(),
            "days_requested": 1.0,
        }
        r = await client.post(
            "/api/v1/leave-requests",
            json=payload,
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 422

    async def test_unpaid_leave_no_balance_check(self, ctx, client):
        """unpaid leave should always succeed regardless of balance."""
        r = await client.post(
            "/api/v1/leave-requests",
            json=_leave_payload(ctx, leave_type="unpaid", days=50.0),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201

    async def test_unauthenticated_returns_401(self, ctx, client):
        r = await client.post("/api/v1/leave-requests", json=_leave_payload(ctx))
        assert r.status_code == 401


# ── List ──────────────────────────────────────────────────────────────────────

class TestListLeave:
    async def _submit(self, ctx, client):
        r = await client.post(
            "/api/v1/leave-requests",
            json=_leave_payload(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_employee_sees_own_only(self, ctx, client):
        await self._submit(ctx, client)
        r = await client.get(
            "/api/v1/leave-requests",
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 200
        items = r.json()["items"]
        assert all(item["employee_id"] == ctx["users"]["Employee"] for item in items)

    async def test_manager_sees_all(self, ctx, client):
        await self._submit(ctx, client)
        r = await client.get(
            "/api/v1/leave-requests",
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["total"] >= 1


# ── Review ────────────────────────────────────────────────────────────────────

class TestReviewLeave:
    async def _submit(self, ctx, client):
        r = await client.post(
            "/api/v1/leave-requests",
            json=_leave_payload(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_manager_can_approve(self, ctx, client):
        req_id = await self._submit(ctx, client)
        r = await client.put(
            f"/api/v1/leave-requests/{req_id}/review",
            json={"approve": True, "review_comment": "Approved"},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    async def test_manager_can_deny(self, ctx, client):
        req_id = await self._submit(ctx, client)
        r = await client.put(
            f"/api/v1/leave-requests/{req_id}/review",
            json={"approve": False, "review_comment": "Denied"},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "denied"

    async def test_double_review_returns_409(self, ctx, client):
        req_id = await self._submit(ctx, client)
        await client.put(
            f"/api/v1/leave-requests/{req_id}/review",
            json={"approve": True},
            headers=_auth(ctx, "Manager"),
        )
        r = await client.put(
            f"/api/v1/leave-requests/{req_id}/review",
            json={"approve": False},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 409

    async def test_employee_cannot_review(self, ctx, client):
        req_id = await self._submit(ctx, client)
        r = await client.put(
            f"/api/v1/leave-requests/{req_id}/review",
            json={"approve": True},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403


# ── Cancel ────────────────────────────────────────────────────────────────────

class TestCancelLeave:
    async def _submit(self, ctx, client):
        r = await client.post(
            "/api/v1/leave-requests",
            json=_leave_payload(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 201
        return r.json()["id"]

    async def test_employee_can_cancel_pending(self, ctx, client):
        req_id = await self._submit(ctx, client)
        r = await client.put(
            f"/api/v1/leave-requests/{req_id}/cancel",
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "cancelled"

    async def test_cannot_cancel_approved(self, ctx, client):
        req_id = await self._submit(ctx, client)
        await client.put(
            f"/api/v1/leave-requests/{req_id}/review",
            json={"approve": True},
            headers=_auth(ctx, "Manager"),
        )
        r = await client.put(
            f"/api/v1/leave-requests/{req_id}/cancel",
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 409
