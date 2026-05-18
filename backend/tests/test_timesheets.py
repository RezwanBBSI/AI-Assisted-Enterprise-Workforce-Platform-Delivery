"""
Integration tests for the /api/v1/timesheets endpoints.
Uses sprint4_helpers to seed realistic time entry data.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.sprint4_helpers import _seed_sprint4


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def ctx(db_session, client):
    return await _seed_sprint4(db_session, client)


# ── Generate ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_manager_can_generate_timesheet(ctx, client):
    resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert data["employee_id"] == ctx["users"]["Employee"]
    assert len(data["line_items"]) > 0
    return data["id"]


@pytest.mark.asyncio
async def test_employee_cannot_generate_timesheet(ctx, client):
    resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_generate_rejected(ctx, client):
    resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_generate_invalid_period_rejected(ctx, client):
    resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_end"]),
            "pay_period_end": str(ctx["pay_start"]),  # end before start
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert resp.status_code == 422


# ── List / Get ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_employee_sees_own_timesheets_only(ctx, client):
    # Generate one for the employee
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert gen_resp.status_code == 201

    list_resp = await client.get(
        "/api/v1/timesheets",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert all(i["employee_id"] == ctx["users"]["Employee"] for i in items)


@pytest.mark.asyncio
async def test_manager_can_get_any_timesheet(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]

    get_resp = await client.get(
        f"/api/v1/timesheets/{ts_id}",
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert get_resp.status_code == 200


@pytest.mark.asyncio
async def test_employee_cannot_access_another_employee_timesheet(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Manager"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]

    # Employee tries to get the Manager's timesheet
    get_resp = await client.get(
        f"/api/v1/timesheets/{ts_id}",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    assert get_resp.status_code == 403


@pytest.mark.asyncio
async def test_get_nonexistent_timesheet_returns_404(ctx, client):
    resp = await client.get(
        "/api/v1/timesheets/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert resp.status_code == 404


# ── Submit ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_employee_can_submit_own_timesheet(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]

    submit_resp = await client.put(
        f"/api/v1/timesheets/{ts_id}/submit",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "submitted"


@pytest.mark.asyncio
async def test_double_submit_returns_409(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]
    await client.put(
        f"/api/v1/timesheets/{ts_id}/submit",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    # Submit again
    resp = await client.put(
        f"/api/v1/timesheets/{ts_id}/submit",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_employee_cannot_submit_others_timesheet(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Manager"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/timesheets/{ts_id}/submit",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    assert resp.status_code == 403


# ── Approve ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_manager_can_approve_submitted_timesheet(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]

    await client.put(
        f"/api/v1/timesheets/{ts_id}/submit",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    approve_resp = await client.put(
        f"/api/v1/timesheets/{ts_id}/approve",
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_approve_non_submitted_returns_409(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]

    # Timesheet is still in draft — approve should fail
    resp = await client.put(
        f"/api/v1/timesheets/{ts_id}/approve",
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_employee_cannot_approve(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]

    await client.put(
        f"/api/v1/timesheets/{ts_id}/submit",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    resp = await client.put(
        f"/api/v1/timesheets/{ts_id}/approve",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    assert resp.status_code == 403


# ── Export ────────────────────────────────────────────────────────────────────

async def _generate_and_approve(ctx, client) -> str:
    """Helper: generate → submit → approve a timesheet; return its ID."""
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]
    await client.put(
        f"/api/v1/timesheets/{ts_id}/submit",
        headers={"Authorization": f"Bearer {ctx['tokens']['Employee']}"},
    )
    await client.put(
        f"/api/v1/timesheets/{ts_id}/approve",
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    return ts_id


@pytest.mark.asyncio
async def test_export_csv(ctx, client):
    ts_id = await _generate_and_approve(ctx, client)
    resp = await client.post(
        f"/api/v1/timesheets/{ts_id}/export",
        json={"export_format": "csv"},
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["export"]["export_format"] == "csv"
    assert data["export"]["record_count"] > 0
    # CSV content must have a header row
    assert "rate_type" in data["content"]


@pytest.mark.asyncio
async def test_export_json(ctx, client):
    ts_id = await _generate_and_approve(ctx, client)
    resp = await client.post(
        f"/api/v1/timesheets/{ts_id}/export",
        json={"export_format": "json"},
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["export"]["export_format"] == "json"
    import json as _json
    parsed = _json.loads(data["content"])
    assert "line_items" in parsed
    assert "summary" in parsed


@pytest.mark.asyncio
async def test_export_invalid_format_rejected(ctx, client):
    ts_id = await _generate_and_approve(ctx, client)
    resp = await client.post(
        f"/api/v1/timesheets/{ts_id}/export",
        json={"export_format": "xml"},
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_export_unapproved_timesheet_rejected(ctx, client):
    gen_resp = await client.post(
        "/api/v1/timesheets/generate",
        json={
            "employee_id": ctx["users"]["Employee"],
            "company_id": ctx["company_id"],
            "pay_period_start": str(ctx["pay_start"]),
            "pay_period_end": str(ctx["pay_end"]),
        },
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    ts_id = gen_resp.json()["id"]  # still in draft

    resp = await client.post(
        f"/api/v1/timesheets/{ts_id}/export",
        json={"export_format": "csv"},
        headers={"Authorization": f"Bearer {ctx['tokens']['Manager']}"},
    )
    assert resp.status_code == 409
