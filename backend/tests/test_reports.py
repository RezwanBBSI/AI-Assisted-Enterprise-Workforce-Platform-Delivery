"""
Integration tests for /api/v1/reports endpoints.
Sprint 5: compliance reports, attendance exceptions, audit trail,
          operational report, and crosscheck.
"""
import pytest

from tests.sprint5_helpers import _seed_sprint5


@pytest.fixture()
async def ctx(db_session, client):
    return await _seed_sprint5(db_session, client)


def _auth(ctx, role):
    return {"Authorization": f"Bearer {ctx['tokens'][role]}"}


def _pay_params(ctx):
    return {
        "company_id": ctx["company_id"],
        "pay_period_start": ctx["s5_pay_start"].isoformat(),
        "pay_period_end": ctx["s5_pay_end"].isoformat(),
    }


# ── GET /reports/compliance ──────────────────────────────────────────────────

class TestComplianceReport:
    @pytest.fixture(autouse=True)
    async def _seed_violations(self, ctx, client):
        await client.post(
            "/api/v1/compliance/validate",
            json={
                "company_id": ctx["company_id"],
                "pay_period_start": ctx["s5_pay_start"].isoformat(),
                "pay_period_end": ctx["s5_pay_end"].isoformat(),
            },
            headers=_auth(ctx, "Manager"),
        )

    async def test_compliance_report_happy_path(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/compliance",
            params=_pay_params(ctx),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total_violations"] >= 2
        assert "by_type" in data
        assert isinstance(data["violations"], list)

    async def test_compliance_report_empty_period(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/compliance",
            params={
                "company_id": ctx["company_id"],
                "pay_period_start": "2020-01-01",
                "pay_period_end": "2020-01-07",
            },
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["total_violations"] == 0

    async def test_employee_cannot_access_compliance_report(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/compliance",
            params=_pay_params(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403


# ── GET /reports/attendance-exceptions ──────────────────────────────────────

class TestAttendanceExceptions:
    async def test_attendance_exceptions_happy_path(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/attendance-exceptions",
            params={
                "company_id": ctx["company_id"],
                "start_date": ctx["s5_pay_start"].isoformat(),
                "end_date": ctx["s5_pay_end"].isoformat(),
            },
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2  # absent + late
        statuses = {item["status"] for item in data["items"]}
        assert "absent" in statuses
        assert "late" in statuses

    async def test_attendance_exceptions_empty(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/attendance-exceptions",
            params={
                "company_id": ctx["company_id"],
                "start_date": "2020-01-01",
                "end_date": "2020-01-07",
            },
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["total"] == 0

    async def test_employee_cannot_access_att_exceptions(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/attendance-exceptions",
            params={
                "company_id": ctx["company_id"],
                "start_date": ctx["s5_pay_start"].isoformat(),
                "end_date": ctx["s5_pay_end"].isoformat(),
            },
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403


# ── GET /reports/audit-trail ─────────────────────────────────────────────────

class TestAuditTrail:
    async def test_admin_can_access_audit_trail(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/audit-trail",
            headers=_auth(ctx, "Admin"),
        )
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data

    async def test_manager_cannot_access_audit_trail(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/audit-trail",
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 403

    async def test_filter_by_entity_type(self, ctx, client):
        """Seed a compliance violation then filter audit trail by entity_type."""
        # Run validation to produce a compliance_validation audit log entry
        await client.post(
            "/api/v1/compliance/validate",
            json={
                "company_id": ctx["company_id"],
                "pay_period_start": ctx["s5_pay_start"].isoformat(),
                "pay_period_end": ctx["s5_pay_end"].isoformat(),
            },
            headers=_auth(ctx, "Manager"),
        )
        r = await client.get(
            "/api/v1/reports/audit-trail",
            params={"entity_type": "compliance_validation"},
            headers=_auth(ctx, "Admin"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["entity_type"] == "compliance_validation"


# ── GET /reports/operational ──────────────────────────────────────────────────

class TestOperationalReport:
    async def test_operational_report_happy_path(self, ctx, client):
        """Uses Sprint 4 pay period where timesheets were generated."""
        r = await client.get(
            "/api/v1/reports/operational",
            params={
                "company_id": ctx["company_id"],
                "pay_period_start": ctx["pay_start"].isoformat(),
                "pay_period_end": ctx["pay_end"].isoformat(),
            },
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        assert "total_regular_hrs" in data
        assert "total_ot_hrs" in data
        assert "total_absences" in data
        assert "total_late_arrivals" in data

    async def test_operational_report_empty_period(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/operational",
            params={
                "company_id": ctx["company_id"],
                "pay_period_start": "2020-01-01",
                "pay_period_end": "2020-01-07",
            },
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total_regular_hrs"] == 0.0
        assert data["total_employees"] == 0

    async def test_employee_cannot_access_operational(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/operational",
            params=_pay_params(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403


# ── GET /reports/crosscheck ──────────────────────────────────────────────────

class TestCrosscheck:
    async def test_crosscheck_hours_mismatch(self, ctx, client):
        """2026-06-03: shift=9hrs, actual=4hrs → hours_mismatch discrepancy."""
        r = await client.get(
            "/api/v1/reports/crosscheck",
            params=_pay_params(ctx),
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total_discrepancies"] >= 1
        issues = {e["issue"] for e in data["entries"]}
        assert "hours_mismatch" in issues or "no_time_entry" in issues

    async def test_crosscheck_no_discrepancy(self, ctx, client):
        """A period with no shifts → no discrepancies."""
        r = await client.get(
            "/api/v1/reports/crosscheck",
            params={
                "company_id": ctx["company_id"],
                "pay_period_start": "2020-01-01",
                "pay_period_end": "2020-01-07",
            },
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["total_discrepancies"] == 0

    async def test_crosscheck_empty_period(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/crosscheck",
            params={
                "company_id": ctx["company_id"],
                "pay_period_start": "2019-01-01",
                "pay_period_end": "2019-01-07",
            },
            headers=_auth(ctx, "Manager"),
        )
        assert r.status_code == 200
        assert r.json()["total_discrepancies"] == 0

    async def test_employee_cannot_access_crosscheck(self, ctx, client):
        r = await client.get(
            "/api/v1/reports/crosscheck",
            params=_pay_params(ctx),
            headers=_auth(ctx, "Employee"),
        )
        assert r.status_code == 403
