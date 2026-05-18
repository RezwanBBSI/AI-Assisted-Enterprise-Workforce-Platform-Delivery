"""
Integration tests for /api/v1/compliance endpoints.
Sprint 5: compliance validation and violation management.
"""
import pytest

from tests.sprint5_helpers import _seed_sprint5


@pytest.fixture()
async def ctx(db_session, client):
    return await _seed_sprint5(db_session, client)


def _auth(ctx, role):
    return {"Authorization": f"Bearer {ctx['tokens'][role]}"}


def _run_payload(ctx):
    return {
        "company_id": ctx["company_id"],
        "pay_period_start": ctx["s5_pay_start"].isoformat(),
        "pay_period_end": ctx["s5_pay_end"].isoformat(),
    }


# ── POST /compliance/validate ────────────────────────────────────────────────

class TestRunValidation:
    async def test_finds_missing_punch(self, ctx, client):
        r = await client.post(
            "/api/v1/compliance/validate",
            json=_run_payload(ctx),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        types = [v["violation_type"] for v in data["violations"]]
        assert "missing_punch" in types

    async def test_finds_mandatory_break(self, ctx, client):
        r = await client.post(
            "/api/v1/compliance/validate",
            json=_run_payload(ctx),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        types = [v["violation_type"] for v in r.json()["violations"]]
        assert "mandatory_break" in types

    async def test_empty_period_returns_zero(self, ctx, client):
        """A period with no matching data creates no violations."""
        r = await client.post(
            "/api/v1/compliance/validate",
            json={
                "company_id": ctx["company_id"],
                "pay_period_start": "2020-01-01",
                "pay_period_end": "2020-01-07",
            },
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["violations_created"] == 0

    async def test_employee_cannot_validate(self, ctx, client):
        r = await client.post(
            "/api/v1/compliance/validate",
            json=_run_payload(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403

    async def test_unauthenticated_returns_401(self, ctx, client):
        r = await client.post("/api/v1/compliance/validate", json=_run_payload(ctx))
        assert r.status_code == 401


# ── GET /compliance/violations ───────────────────────────────────────────────

class TestListViolations:
    @pytest.fixture(autouse=True)
    async def _seed_violations(self, ctx, client):
        """Run validation first so violations exist."""
        await client.post(
            "/api/v1/compliance/validate",
            json=_run_payload(ctx),
            headers=_auth(ctx, "Manager"),
        )

    async def test_list_all_violations(self, ctx, client):
        r = await client.get(
            "/api/v1/compliance/violations",
            params={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 2

    async def test_filter_by_type(self, ctx, client):
        r = await client.get(
            "/api/v1/compliance/violations",
            params={"company_id": ctx["company_id"], "violation_type": "missing_punch"},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["violation_type"] == "missing_punch"

    async def test_filter_by_resolved_false(self, ctx, client):
        r = await client.get(
            "/api/v1/compliance/violations",
            params={"company_id": ctx["company_id"], "resolved": "false"},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["resolved"] is False

    async def test_employee_cannot_list(self, ctx, client):
        r = await client.get(
            "/api/v1/compliance/violations",
            params={"company_id": ctx["company_id"]},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403


# ── PUT /compliance/violations/{id} ─────────────────────────────────────────

class TestResolveViolation:
    @pytest.fixture()
    async def violation_id(self, ctx, client):
        """Run validation and return the first violation ID."""
        r = await client.post(
            "/api/v1/compliance/validate",
            json=_run_payload(ctx),
            headers=_auth(ctx, "Manager"),
        )
        return r.json()["violations"][0]["id"]

    async def test_resolve_violation(self, ctx, client, violation_id):
        r = await client.put(
            f"/api/v1/compliance/violations/{violation_id}",
            json={"resolution_notes": "Corrected by manager"},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["resolved"] is True
        assert data["resolution_notes"] == "Corrected by manager"

    async def test_double_resolve_returns_409(self, ctx, client, violation_id):
        headers = _auth(ctx, "Manager")
        await client.put(
            f"/api/v1/compliance/violations/{violation_id}",
            json={"resolution_notes": "First resolve"},
            headers=headers,
        )
        r = await client.put(
            f"/api/v1/compliance/violations/{violation_id}",
            json={"resolution_notes": "Second resolve"},
            headers=headers,
        )
        assert r.status_code == 409

    async def test_nonexistent_violation_returns_404(self, ctx, client):
        r = await client.put(
            "/api/v1/compliance/violations/nonexistent-id",
            json={"resolution_notes": "Won't work"},
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 404

    async def test_employee_cannot_resolve(self, ctx, client, violation_id):
        r = await client.put(
            f"/api/v1/compliance/violations/{violation_id}",
            json={"resolution_notes": "Unauthorized attempt"},
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403
