"""
Integration tests for /api/v1/policies endpoints.
"""
import pytest

from tests.sprint3_helpers import _seed_sprint3


@pytest.fixture()
async def ctx(db_session, client):
    return await _seed_sprint3(db_session, client)


def _auth(ctx, role):
    return {"Authorization": f"Bearer {ctx['tokens'][role]}"}


class TestPolicies:
    async def test_manager_can_list_policies(self, ctx, client):
        r = await client.get(
            "/api/v1/policies",
            params={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        keys = [p["policy_key"] for p in r.json()]
        assert "core_hours_start" in keys

    async def test_admin_can_upsert_policy(self, ctx, client):
        r = await client.put(
            "/api/v1/policies/overtime_threshold",
            params={"company_id": ctx["company_id"]},
            json={"policy_value": "40"},
            headers=_auth(ctx, "Admin"),
        )
        assert r.status_code == 200
        assert r.json()["policy_key"] == "overtime_threshold"
        assert r.json()["policy_value"] == "40"

    async def test_manager_cannot_upsert(self, ctx, client):
        r = await client.put(
            "/api/v1/policies/overtime_threshold",
            params={"company_id": ctx["company_id"]},
            json={"policy_value": "40"},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 403

    async def test_employee_cannot_list(self, ctx, client):
        r = await client.get(
            "/api/v1/policies",
            params={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403
