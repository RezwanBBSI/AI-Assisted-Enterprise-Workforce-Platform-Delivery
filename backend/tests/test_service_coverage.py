"""
Service-layer unit tests targeting uncovered branches for Sprint 6 coverage goal.

These tests call service classes directly (not via HTTP) to hit branches
that the integration tests don't reach.
"""
import pytest
from datetime import date, datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PunchError
from app.models.attendance_record import AttendanceRecord
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.company_policy import CompanyPolicy
from app.models.leave_balance import LeaveBalance
from app.models.leave_request import LeaveRequest
from app.models.shift_schedule import ShiftSchedule
from app.models.time_entry import TimeEntry
from app.services.leave_service import LeaveBalanceService, LeaveService, LeaveValidationService
from app.services.policy_service import PolicyService
from app.services.report_service import ReportService
from app.services.schedule_service import ScheduleService
from app.schemas.scheduling import (
    LeaveRequestCreate,
    LeaveReviewRequest,
    PolicyUpdate,
    ShiftCreate,
    ShiftUpdate,
)


# ── helpers ────────────────────────────────────────────────────────────────────

async def _make_company(db: AsyncSession, name: str = "Cov Co") -> str:
    c = Company(name=name)
    db.add(c)
    await db.flush()
    return str(c.id)


# ═══════════════════════════════════════════════════════════════════════════════
# ReportService — hit every uncovered branch
# ═══════════════════════════════════════════════════════════════════════════════

class TestReportServiceUnit:
    """Direct service calls, not HTTP, to reach every branch."""

    async def test_compliance_report_with_violations(self, db_session: AsyncSession):
        from app.models.compliance_violation import ComplianceViolation
        company_id = await _make_company(db_session, "RC Co")
        dt = datetime(2026, 7, 1, 10, 0)
        v1 = ComplianceViolation(
            company_id=company_id,
            employee_id="emp1",
            violation_type="missing_punch",
            description="Open punch on 2026-07-01",
            occurred_at=dt,
            resolved=False,
        )
        v2 = ComplianceViolation(
            company_id=company_id,
            employee_id="emp1",
            violation_type="missing_punch",
            description="Open punch resolved",
            occurred_at=dt,
            resolved=True,
        )
        v3 = ComplianceViolation(
            company_id=company_id,
            employee_id="emp1",
            violation_type="mandatory_break",
            description="No break on long shift",
            occurred_at=dt,
            resolved=False,
        )
        db_session.add_all([v1, v2, v3])
        await db_session.commit()

        svc = ReportService(db_session)
        result = await svc.compliance_report(
            company_id, date(2026, 7, 1), date(2026, 7, 7)
        )
        assert result.total_violations == 3
        assert result.unresolved == 2
        assert result.by_type["missing_punch"] == 2
        assert result.by_type["mandatory_break"] == 1

    async def test_attendance_exceptions_with_absent_and_late(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "Att Co")
        db_session.add_all([
            AttendanceRecord(employee_id="e1", company_id=company_id, date=date(2026, 7, 1), status="absent"),
            AttendanceRecord(employee_id="e1", company_id=company_id, date=date(2026, 7, 2), status="late"),
            AttendanceRecord(employee_id="e1", company_id=company_id, date=date(2026, 7, 3), status="present"),
        ])
        await db_session.commit()

        svc = ReportService(db_session)
        result = await svc.attendance_exceptions(company_id, date(2026, 7, 1), date(2026, 7, 7))
        assert result.total == 2
        statuses = {i.status for i in result.items}
        assert "absent" in statuses
        assert "late" in statuses

    async def test_audit_trail_with_all_filters(self, db_session: AsyncSession):
        db_session.add(AuditLog(
            entity_type="shift_schedule",
            entity_id="s1",
            action="shift_created",
            performed_by="user1",
            performed_at=datetime(2026, 7, 3, 12, 0),
            details="{}",
        ))
        await db_session.commit()

        svc = ReportService(db_session)
        # Filter by entity_type
        r = await svc.audit_trail(entity_type="shift_schedule")
        assert r.total >= 1

        # Filter by date range (hits both start_date and end_date branches)
        r2 = await svc.audit_trail(
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 7),
        )
        assert r2.total >= 1

        # No results with far-future range
        r3 = await svc.audit_trail(
            start_date=date(2030, 1, 1),
            end_date=date(2030, 1, 7),
        )
        assert r3.total == 0

    async def test_operational_report_with_absences_and_late(self, db_session: AsyncSession):
        from app.models.timesheet import Timesheet
        company_id = await _make_company(db_session, "Op Co")

        # Add absences and late arrivals to hit all counter branches
        db_session.add_all([
            AttendanceRecord(employee_id="e1", company_id=company_id, date=date(2026, 7, 1), status="absent"),
            AttendanceRecord(employee_id="e2", company_id=company_id, date=date(2026, 7, 2), status="late"),
            AttendanceRecord(employee_id="e3", company_id=company_id, date=date(2026, 7, 3), status="present"),
        ])
        await db_session.commit()

        svc = ReportService(db_session)
        result = await svc.operational_report(company_id, date(2026, 7, 1), date(2026, 7, 7))
        assert result.total_absences == 1
        assert result.total_late_arrivals == 1
        assert result.total_employees == 0  # no timesheets

    async def test_crosscheck_no_time_entry(self, db_session: AsyncSession):
        """Shift with no matching time entry → 'no_time_entry' discrepancy."""
        company_id = await _make_company(db_session, "CC1 Co")
        db_session.add(ShiftSchedule(
            employee_id="emp-cc1",
            company_id=company_id,
            location_id=None,
            shift_date=date(2026, 7, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),  # 8-hr shift
            break_minutes=30,
        ))
        await db_session.commit()

        svc = ReportService(db_session)
        result = await svc.crosscheck(company_id, date(2026, 7, 1), date(2026, 7, 7))
        assert result.total_discrepancies == 1
        assert result.entries[0].issue == "no_time_entry"
        assert result.entries[0].actual_hours is None

    async def test_crosscheck_hours_mismatch(self, db_session: AsyncSession):
        """Shift 8 hrs, actual 3 hrs → 'hours_mismatch'."""
        company_id = await _make_company(db_session, "CC2 Co")
        db_session.add(ShiftSchedule(
            employee_id="emp-cc2",
            company_id=company_id,
            location_id=None,
            shift_date=date(2026, 7, 2),
            shift_start=time(8, 0),
            shift_end=time(16, 0),  # 8 hrs
            break_minutes=30,
        ))
        db_session.add(TimeEntry(
            employee_id="emp-cc2",
            company_id=company_id,
            location_id=None,
            clock_in=datetime(2026, 7, 2, 8, 0),
            clock_out=datetime(2026, 7, 2, 11, 0),  # 3 hrs
            status="closed",
            break_minutes=0,
        ))
        await db_session.commit()

        svc = ReportService(db_session)
        result = await svc.crosscheck(company_id, date(2026, 7, 2), date(2026, 7, 2))
        assert result.total_discrepancies == 1
        assert result.entries[0].issue == "hours_mismatch"
        assert result.entries[0].actual_hours == pytest.approx(3.0)

    async def test_crosscheck_matching_entry_no_discrepancy(self, db_session: AsyncSession):
        """Shift matches actual time entry → no discrepancy (covers OK branch)."""
        company_id = await _make_company(db_session, "CC3 Co")
        db_session.add(ShiftSchedule(
            employee_id="emp-cc3",
            company_id=company_id,
            location_id=None,
            shift_date=date(2026, 7, 3),
            shift_start=time(9, 0),
            shift_end=time(17, 0),  # 8 hrs
            break_minutes=30,
        ))
        db_session.add(TimeEntry(
            employee_id="emp-cc3",
            company_id=company_id,
            location_id=None,
            clock_in=datetime(2026, 7, 3, 9, 0),
            clock_out=datetime(2026, 7, 3, 17, 0),  # exact match
            status="closed",
            break_minutes=30,
        ))
        await db_session.commit()

        svc = ReportService(db_session)
        result = await svc.crosscheck(company_id, date(2026, 7, 3), date(2026, 7, 3))
        assert result.total_discrepancies == 0

    async def test_crosscheck_open_entry_zero_hours(self, db_session: AsyncSession):
        """Shift with open entry (no clock_out) → 0 actual_hours → mismatch."""
        company_id = await _make_company(db_session, "CC4 Co")
        db_session.add(ShiftSchedule(
            employee_id="emp-cc4",
            company_id=company_id,
            location_id=None,
            shift_date=date(2026, 7, 4),
            shift_start=time(9, 0),
            shift_end=time(18, 0),  # 9 hrs
            break_minutes=60,
        ))
        db_session.add(TimeEntry(
            employee_id="emp-cc4",
            company_id=company_id,
            location_id=None,
            clock_in=datetime(2026, 7, 4, 9, 0),
            clock_out=None,  # open → 0 hrs
            status="closed",
            break_minutes=0,
        ))
        await db_session.commit()

        svc = ReportService(db_session)
        result = await svc.crosscheck(company_id, date(2026, 7, 4), date(2026, 7, 4))
        assert result.entries[0].actual_hours == pytest.approx(0.0)

    async def test_crosscheck_overnight_shift(self, db_session: AsyncSession):
        """Overnight shift (end < start) is handled via +1 day logic."""
        company_id = await _make_company(db_session, "CC5 Co")
        db_session.add(ShiftSchedule(
            employee_id="emp-cc5",
            company_id=company_id,
            location_id=None,
            shift_date=date(2026, 7, 5),
            shift_start=time(22, 0),
            shift_end=time(6, 0),   # 8-hr overnight
            break_minutes=30,
        ))
        await db_session.commit()

        svc = ReportService(db_session)
        result = await svc.crosscheck(company_id, date(2026, 7, 5), date(2026, 7, 5))
        # No matching entry → no_time_entry
        assert result.entries[0].issue == "no_time_entry"
        assert result.entries[0].scheduled_hours == pytest.approx(8.0)


# ═══════════════════════════════════════════════════════════════════════════════
# LeaveValidationService — static branches
# ═══════════════════════════════════════════════════════════════════════════════

class TestLeaveValidationService:
    def test_dates_valid(self):
        LeaveValidationService.validate_leave_dates(date(2026, 7, 1), date(2026, 7, 5))

    def test_dates_same_day_valid(self):
        LeaveValidationService.validate_leave_dates(date(2026, 7, 1), date(2026, 7, 1))

    def test_dates_invalid(self):
        with pytest.raises(PunchError, match="end_date"):
            LeaveValidationService.validate_leave_dates(date(2026, 7, 5), date(2026, 7, 1))

    def test_balance_none_unpaid_zero_days_ok(self):
        """balance=None, type=unpaid → never raises regardless of days."""
        LeaveValidationService.validate_leave_balance(None, "unpaid", 5.0)

    def test_balance_none_pto_raises(self):
        """balance=None, type=pto, days>0 → raises."""
        with pytest.raises(PunchError, match="Insufficient pto balance"):
            LeaveValidationService.validate_leave_balance(None, "pto", 1.0)

    def test_balance_none_sick_zero_days_ok(self):
        """balance=None, days=0 → no raise (0 days requested is OK)."""
        LeaveValidationService.validate_leave_balance(None, "sick", 0.0)

    def test_balance_pto_sufficient(self):
        b = LeaveBalance(pto_total=10.0, pto_used=2.0, sick_total=0, sick_used=0,
                         comp_earned=0, comp_used=0)
        LeaveValidationService.validate_leave_balance(b, "pto", 5.0)

    def test_balance_pto_insufficient(self):
        b = LeaveBalance(pto_total=3.0, pto_used=2.0, sick_total=0, sick_used=0,
                         comp_earned=0, comp_used=0)
        with pytest.raises(PunchError, match="Insufficient pto balance"):
            LeaveValidationService.validate_leave_balance(b, "pto", 5.0)

    def test_balance_sick_sufficient(self):
        b = LeaveBalance(pto_total=0, pto_used=0, sick_total=5.0, sick_used=0,
                         comp_earned=0, comp_used=0)
        LeaveValidationService.validate_leave_balance(b, "sick", 2.0)

    def test_balance_sick_insufficient(self):
        b = LeaveBalance(pto_total=0, pto_used=0, sick_total=1.0, sick_used=1.0,
                         comp_earned=0, comp_used=0)
        with pytest.raises(PunchError, match="Insufficient sick balance"):
            LeaveValidationService.validate_leave_balance(b, "sick", 1.0)

    def test_balance_comp_sufficient(self):
        b = LeaveBalance(pto_total=0, pto_used=0, sick_total=0, sick_used=0,
                         comp_earned=8.0, comp_used=0)
        LeaveValidationService.validate_leave_balance(b, "comp", 3.0)

    def test_balance_comp_insufficient(self):
        b = LeaveBalance(pto_total=0, pto_used=0, sick_total=0, sick_used=0,
                         comp_earned=1.0, comp_used=1.0)
        with pytest.raises(PunchError, match="Insufficient comp balance"):
            LeaveValidationService.validate_leave_balance(b, "comp", 1.0)

    def test_balance_unpaid_skips_check(self):
        b = LeaveBalance(pto_total=0, pto_used=0, sick_total=0, sick_used=0,
                         comp_earned=0, comp_used=0)
        LeaveValidationService.validate_leave_balance(b, "unpaid", 99.0)


# ═══════════════════════════════════════════════════════════════════════════════
# LeaveService — async service paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestLeaveServiceUnit:
    async def _company_and_user(self, db: AsyncSession):
        c = Company(name="LV Co")
        db.add(c)
        await db.flush()
        return str(c.id), "lv-emp-1"

    async def test_submit_pto_success(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)

        # Give the employee some PTO
        bal = LeaveBalance(
            employee_id=emp_id, company_id=company_id, year=2026,
            pto_total=10.0, pto_used=0, sick_total=5.0, sick_used=0,
            comp_earned=0, comp_used=0,
        )
        db_session.add(bal)
        await db_session.commit()

        svc = LeaveService(db_session)
        req = await svc.submit(
            emp_id, company_id,
            LeaveRequestCreate(
                company_id=company_id,
                leave_type="pto",
                start_date=date(2026, 7, 1),
                end_date=date(2026, 7, 3),
                days_requested=3.0,
            ),
        )
        assert req.status == "pending"
        assert req.days_requested == 3.0

    async def test_submit_invalid_dates_raises(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        svc = LeaveService(db_session)
        with pytest.raises(PunchError, match="end_date"):
            await svc.submit(
                emp_id, company_id,
                LeaveRequestCreate(
                    company_id=company_id,
                    leave_type="pto",
                    start_date=date(2026, 7, 5),
                    end_date=date(2026, 7, 1),
                    days_requested=3.0,
                ),
            )

    async def test_submit_insufficient_balance_raises(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        svc = LeaveService(db_session)
        # No balance row → 0 PTO
        with pytest.raises(PunchError, match="Insufficient pto balance"):
            await svc.submit(
                emp_id, company_id,
                LeaveRequestCreate(
                    company_id=company_id,
                    leave_type="pto",
                    start_date=date(2026, 7, 1),
                    end_date=date(2026, 7, 3),
                    days_requested=3.0,
                ),
            )

    async def test_list_requests_filters(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        db_session.add(LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="pto", start_date=date(2026, 7, 1), end_date=date(2026, 7, 2),
            days_requested=2.0, status="pending",
        ))
        await db_session.commit()

        svc = LeaveService(db_session)
        result = await svc.list_requests(employee_id=emp_id, company_id=company_id, status="pending")
        assert result["total"] == 1
        assert result["items"][0].status == "pending"

        result2 = await svc.list_requests(status="approved")
        assert result2["total"] == 0

    async def test_review_approve_pto_deducts_balance(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)

        bal = LeaveBalance(
            employee_id=emp_id, company_id=company_id, year=2026,
            pto_total=10.0, pto_used=0, sick_total=5.0, sick_used=0,
            comp_earned=4.0, comp_used=0,
        )
        db_session.add(bal)
        req = LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="pto", start_date=date(2026, 7, 1), end_date=date(2026, 7, 2),
            days_requested=2.0, status="pending",
        )
        db_session.add(req)
        await db_session.commit()

        svc = LeaveService(db_session)
        updated = await svc.review(
            str(req.id), "reviewer-1",
            LeaveReviewRequest(approve=True, review_comment="OK"),
        )
        assert updated.status == "approved"

        await db_session.refresh(bal)
        assert bal.pto_used == 2.0

    async def test_review_approve_sick_deducts_balance(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        bal = LeaveBalance(
            employee_id=emp_id, company_id=company_id, year=2026,
            pto_total=10.0, pto_used=0, sick_total=5.0, sick_used=0,
            comp_earned=0, comp_used=0,
        )
        db_session.add(bal)
        req = LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="sick", start_date=date(2026, 7, 1), end_date=date(2026, 7, 1),
            days_requested=1.0, status="pending",
        )
        db_session.add(req)
        await db_session.commit()

        svc = LeaveService(db_session)
        await svc.review(str(req.id), "reviewer-1", LeaveReviewRequest(approve=True))
        await db_session.refresh(bal)
        assert bal.sick_used == 1.0

    async def test_review_approve_comp_deducts_balance(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        bal = LeaveBalance(
            employee_id=emp_id, company_id=company_id, year=2026,
            pto_total=0, pto_used=0, sick_total=0, sick_used=0,
            comp_earned=8.0, comp_used=0,
        )
        db_session.add(bal)
        req = LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="comp", start_date=date(2026, 7, 1), end_date=date(2026, 7, 2),
            days_requested=2.0, status="pending",
        )
        db_session.add(req)
        await db_session.commit()

        svc = LeaveService(db_session)
        await svc.review(str(req.id), "reviewer-1", LeaveReviewRequest(approve=True))
        await db_session.refresh(bal)
        assert bal.comp_used == 2.0

    async def test_review_deny(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        req = LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="pto", start_date=date(2026, 7, 1), end_date=date(2026, 7, 1),
            days_requested=1.0, status="pending",
        )
        db_session.add(req)
        await db_session.commit()

        svc = LeaveService(db_session)
        result = await svc.review(
            str(req.id), "reviewer-1", LeaveReviewRequest(approve=False, review_comment="No")
        )
        assert result.status == "denied"

    async def test_review_not_found_raises(self, db_session: AsyncSession):
        svc = LeaveService(db_session)
        with pytest.raises(PunchError, match="not found"):
            await svc.review("nonexistent-id", "r1", LeaveReviewRequest(approve=True))

    async def test_review_already_reviewed_raises(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        req = LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="pto", start_date=date(2026, 7, 1), end_date=date(2026, 7, 1),
            days_requested=1.0, status="approved",
        )
        db_session.add(req)
        await db_session.commit()

        svc = LeaveService(db_session)
        with pytest.raises(PunchError, match="already been reviewed"):
            await svc.review(str(req.id), "r1", LeaveReviewRequest(approve=True))

    async def test_cancel_success(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        req = LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="pto", start_date=date(2026, 7, 1), end_date=date(2026, 7, 1),
            days_requested=1.0, status="pending",
        )
        db_session.add(req)
        await db_session.commit()

        svc = LeaveService(db_session)
        result = await svc.cancel(str(req.id), emp_id)
        assert result.status == "cancelled"

    async def test_cancel_not_found_raises(self, db_session: AsyncSession):
        svc = LeaveService(db_session)
        with pytest.raises(PunchError, match="not found"):
            await svc.cancel("nonexistent-id", "emp1")

    async def test_cancel_wrong_employee_raises(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        req = LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="pto", start_date=date(2026, 7, 1), end_date=date(2026, 7, 1),
            days_requested=1.0, status="pending",
        )
        db_session.add(req)
        await db_session.commit()

        svc = LeaveService(db_session)
        with pytest.raises(PunchError, match="Cannot cancel"):
            await svc.cancel(str(req.id), "wrong-employee")

    async def test_cancel_non_pending_raises(self, db_session: AsyncSession):
        company_id, emp_id = await self._company_and_user(db_session)
        req = LeaveRequest(
            employee_id=emp_id, company_id=company_id,
            leave_type="pto", start_date=date(2026, 7, 1), end_date=date(2026, 7, 1),
            days_requested=1.0, status="approved",
        )
        db_session.add(req)
        await db_session.commit()

        svc = LeaveService(db_session)
        with pytest.raises(PunchError, match="Only pending"):
            await svc.cancel(str(req.id), emp_id)

    async def test_get_or_create_balance_creates_new(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "LB Co")
        svc = LeaveBalanceService(db_session)
        bal = await svc.get_balance("new-emp", company_id, 2026)
        assert bal.pto_total == 0
        assert bal.year == 2026

    async def test_get_or_create_balance_returns_existing(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "LB2 Co")
        existing = LeaveBalance(
            employee_id="lbe-1", company_id=company_id, year=2026,
            pto_total=5.0, pto_used=0, sick_total=0, sick_used=0,
            comp_earned=0, comp_used=0,
        )
        db_session.add(existing)
        await db_session.commit()

        svc = LeaveBalanceService(db_session)
        bal = await svc.get_balance("lbe-1", company_id, 2026)
        assert bal.pto_total == 5.0


# ═══════════════════════════════════════════════════════════════════════════════
# PolicyService — upsert (create and update branches)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPolicyServiceUnit:
    async def test_upsert_creates_new_policy(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "PS Co")
        svc = PolicyService(db_session)
        p = await svc.upsert_policy(
            company_id, "overtime_threshold",
            PolicyUpdate(policy_value="40"), "admin-1",
        )
        assert p.policy_value == "40"
        assert p.policy_key == "overtime_threshold"

    async def test_upsert_updates_existing_policy(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "PS2 Co")
        svc = PolicyService(db_session)
        # Create first
        await svc.upsert_policy(company_id, "overtime_threshold",
                                 PolicyUpdate(policy_value="40"), "admin-1")
        # Update
        p = await svc.upsert_policy(company_id, "overtime_threshold",
                                     PolicyUpdate(policy_value="45"), "admin-2")
        assert p.policy_value == "45"
        assert p.updated_by == "admin-2"

    async def test_list_policies_empty(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "PS3 Co")
        svc = PolicyService(db_session)
        result = await svc.list_policies(company_id)
        assert result == []

    async def test_list_policies_with_entries(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "PS4 Co")
        svc = PolicyService(db_session)
        await svc.upsert_policy(company_id, "key1", PolicyUpdate(policy_value="v1"), "admin-1")
        await svc.upsert_policy(company_id, "key2", PolicyUpdate(policy_value="v2"), "admin-1")
        result = await svc.list_policies(company_id)
        assert len(result) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# ScheduleService — break validation + CRUD error paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestScheduleServiceUnit:
    def test_validate_break_under_6hrs_no_break_needed(self):
        # 5-hr shift, 0 break → OK
        ScheduleService._validate_break(time(9, 0), time(14, 0), 0)

    def test_validate_break_6_to_8hrs_needs_30min(self):
        # 7-hr shift, 20 min break → error
        with pytest.raises(PunchError, match="30 minutes break"):
            ScheduleService._validate_break(time(9, 0), time(16, 0), 20)

    def test_validate_break_6_to_8hrs_sufficient(self):
        ScheduleService._validate_break(time(9, 0), time(16, 0), 30)

    def test_validate_break_over_8hrs_needs_60min(self):
        # 9-hr shift, 30 min break → error
        with pytest.raises(PunchError, match="60 minutes break"):
            ScheduleService._validate_break(time(9, 0), time(18, 0), 30)

    def test_validate_break_over_8hrs_sufficient(self):
        ScheduleService._validate_break(time(9, 0), time(18, 0), 60)

    def test_validate_break_overnight_shift(self):
        # 10-hr overnight, 60 min → OK
        ScheduleService._validate_break(time(22, 0), time(8, 0), 60)

    async def test_list_shifts_with_all_filters(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "SS Co")
        db_session.add(ShiftSchedule(
            employee_id="ss-emp",
            company_id=company_id,
            location_id=None,
            shift_date=date(2026, 7, 1),
            shift_start=time(9, 0),
            shift_end=time(14, 0),
            break_minutes=0,
        ))
        await db_session.commit()

        svc = ScheduleService(db_session)
        result = await svc.list_shifts(
            employee_id="ss-emp",
            company_id=company_id,
            date_from=date(2026, 6, 30),
            date_to=date(2026, 7, 2),
        )
        assert result["total"] == 1

    async def test_get_shift_not_found(self, db_session: AsyncSession):
        svc = ScheduleService(db_session)
        result = await svc.get_shift("nonexistent-id")
        assert result is None

    async def test_update_shift_not_found_raises(self, db_session: AsyncSession):
        svc = ScheduleService(db_session)
        with pytest.raises(PunchError, match="Shift not found"):
            await svc.update("nonexistent-id", ShiftUpdate(), "admin")

    async def test_update_shift_partial_fields(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "SS2 Co")
        shift = ShiftSchedule(
            employee_id="ss2-emp",
            company_id=company_id,
            location_id=None,
            shift_date=date(2026, 7, 1),
            shift_start=time(9, 0),
            shift_end=time(14, 0),  # 5 hrs
            break_minutes=0,
        )
        db_session.add(shift)
        await db_session.commit()

        svc = ScheduleService(db_session)
        updated = await svc.update(
            str(shift.id),
            ShiftUpdate(shift_date=date(2026, 7, 10)),
            "admin",
        )
        assert updated.shift_date == date(2026, 7, 10)

    async def test_delete_shift(self, db_session: AsyncSession):
        company_id = await _make_company(db_session, "SS3 Co")
        shift = ShiftSchedule(
            employee_id="ss3-emp",
            company_id=company_id,
            location_id=None,
            shift_date=date(2026, 7, 1),
            shift_start=time(9, 0),
            shift_end=time(14, 0),
            break_minutes=0,
        )
        db_session.add(shift)
        await db_session.commit()

        svc = ScheduleService(db_session)
        await svc.delete(str(shift.id), "admin")

        result = await svc.get_shift(str(shift.id))
        assert result is None

    async def test_delete_not_found_raises(self, db_session: AsyncSession):
        svc = ScheduleService(db_session)
        with pytest.raises(PunchError, match="Shift not found"):
            await svc.delete("nonexistent-id", "admin")
