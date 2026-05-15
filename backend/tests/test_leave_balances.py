"""
Integration tests for /api/v1/leave-balances endpoints.
"""
import pytest

from tests.sprint3_helpers import _seed_sprint3


@pytest.fixture()
async def ctx(db_session, client):
    return await _seed_sprint3(db_session, client)


def _auth(ctx, role):
    return {"Authorization": f"Bearer {ctx['tokens'][role]}"}


class TestLeaveBalances:
    async def test_employee_gets_own_balance(self, ctx, client):
        r = await client.get(
            f"/api/v1/leave-balances/{ctx['users']['Employee']}",
            params={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["pto_total"] == 10.0
        assert data["sick_total"] == 5.0
        assert data["comp_earned"] == 5.0

    async def test_manager_can_get_any_balance(self, ctx, client):
        r = await client.get(
            f"/api/v1/leave-balances/{ctx['users']['Employee']}",
            params={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200

    async def test_employee_cannot_see_other_employee_balance(self, ctx, client):
        """Employee tries to get Manager's balance — should 403."""
        r = await client.get(
            f"/api/v1/leave-balances/{ctx['users']['Manager']}",
            params={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403

    async def test_no_balance_row_returns_zeros(self, ctx, client):
        """Manager gets their own balance — no row exists yet, should auto-create with zeros."""
        r = await client.get(
            f"/api/v1/leave-balances/{ctx['users']['Manager']}",
            params={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["pto_total"] == 0.0
        assert data["pto_used"] == 0.0
