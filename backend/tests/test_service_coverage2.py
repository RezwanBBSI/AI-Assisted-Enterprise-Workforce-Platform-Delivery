"""
Sprint 6 — Part 2: coverage tests for time_entry_service, compliance_service,
and payroll_service (TimesheetService).
"""
import pytest
from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PunchError
from app.models.company import Company
from app.models.leave_balance import LeaveBalance
from app.models.leave_request import LeaveRequest
from app.models.shift_schedule import ShiftSchedule
from app.models.time_entry import TimeEntry
from app.models.timesheet import Timesheet
from app.services.compliance_service import ComplianceService, ComplianceValidationService
from app.services.time_entry_service import AttendanceService, TimeEntryService
from app.services.payroll_service import TimesheetService
from app.schemas.time_entry import CorrectionRequest, CorrectionReviewRequest


# ── helpers ───────────────────────────────────────────────────────────────────

async def _co(db: AsyncSession, name: str = "Test Co") -> str:
    c = Company(name=name)
    db.add(c)
    await db.flush()
    return str(c.id)


# ═══════════════════════════════════════════════════════════════════════════════
# ComplianceValidationService — static helpers (100% branch target)
# ═══════════════════════════════════════════════════════════════════════════════

class TestComplianceValidationUnit:
    # _policy_float

    def test_policy_float_missing_key_returns_default(self):
        assert ComplianceValidationService._policy_float({}, "key", 99.0) == 99.0

    def test_policy_float_valid_value(self):
        assert ComplianceValidationService._policy_float({"key": "42.5"}, "key", 0.0) == 42.5

    def test_policy_float_invalid_value_returns_default(self):
        assert ComplianceValidationService._policy_float({"key": "notanumber"}, "key", 7.0) == 7.0

    # check_missing_punch

    def test_check_missing_punch_no_violations(self):
        """Entry with clock_out → no violation."""
        e = TimeEntry(
            employee_id="emp1", company_id="co1",
            clock_in=datetime(2026, 6, 2, 9, 0),
            clock_out=datetime(2026, 6, 2, 17, 0),
            status="closed",
        )
        result = ComplianceValidationService.check_missing_punch([e], date(2026, 6, 7))
        assert result == []

    def test_check_missing_punch_open_before_period_end(self):
        """Open entry whose clock_in is within the period → violation."""
        e = TimeEntry(
            employee_id="emp1", company_id="co1",
            clock_in=datetime(2026, 6, 2, 9, 0),
            clock_out=None,
            status="open",
        )
        result = ComplianceValidationService.check_missing_punch([e], date(2026, 6, 7))
        assert len(result) == 1
        assert result[0]["violation_type"] == "missing_punch"

    def test_check_missing_punch_open_after_period_end(self):
        """Open entry clocked in AFTER the period end → not a violation yet."""
        e = TimeEntry(
            employee_id="emp1", company_id="co1",
            clock_in=datetime(2026, 6, 10, 9, 0),  # after period end 2026-06-07
            clock_out=None,
            status="open",
        )
        result = ComplianceValidationService.check_missing_punch([e], date(2026, 6, 7))
        assert result == []

    # check_max_hours

    def test_check_max_hours_within_limit(self):
        ts = Timesheet(
            employee_id="emp1", company_id="co1",
            pay_period_start=date(2026, 6, 1), pay_period_end=date(2026, 6, 7),
            total_regular_hrs=40.0, total_ot_hrs=0.0, status="draft",
        )
        result = ComplianceValidationService.check_max_hours([ts], {"max_hours_per_week": "60"})
        assert result == []

    def test_check_max_hours_exceeded(self):
        ts = Timesheet(
            employee_id="emp1", company_id="co1",
            pay_period_start=date(2026, 6, 1), pay_period_end=date(2026, 6, 7),
            total_regular_hrs=50.0, total_ot_hrs=15.0, status="draft",
        )
        result = ComplianceValidationService.check_max_hours([ts], {"max_hours_per_week": "60"})
        assert len(result) == 1
        assert result[0]["violation_type"] == "max_hours"

    def test_check_max_hours_uses_default_when_policy_missing(self):
        """No policy → default 60 hrs max."""
        ts = Timesheet(
            employee_id="emp1", company_id="co1",
            pay_period_start=date(2026, 6, 1), pay_period_end=date(2026, 6, 7),
            total_regular_hrs=61.0, total_ot_hrs=0.0, status="draft",
        )
        result = ComplianceValidationService.check_max_hours([ts], {})
        assert len(result) == 1

    def test_check_max_hours_none_values_treated_as_zero(self):
        ts = Timesheet(
            employee_id="emp1", company_id="co1",
            pay_period_start=date(2026, 6, 1), pay_period_end=date(2026, 6, 7),
            total_regular_hrs=None, total_ot_hrs=None, status="draft",
        )
        result = ComplianceValidationService.check_max_hours([ts], {"max_hours_per_week": "60"})
        assert result == []

    # check_mandatory_break

    def test_check_mandatory_break_short_shift(self):
        shift = ShiftSchedule(
            employee_id="emp1", company_id="co1",
            shift_date=date(2026, 6, 1),
            shift_start=time(9, 0),
            shift_end=time(14, 0),   # 5 hrs → no minimum break
            break_minutes=0,
        )
        result = ComplianceValidationService.check_mandatory_break([shift])
        assert result == []

    def test_check_mandatory_break_long_shift_no_break(self):
        shift = ShiftSchedule(
            employee_id="emp1", company_id="co1",
            shift_date=date(2026, 6, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),   # 8 hrs, no break → violation
            break_minutes=0,
        )
        result = ComplianceValidationService.check_mandatory_break([shift])
        assert len(result) == 1
        assert result[0]["violation_type"] == "mandatory_break"

    def test_check_mandatory_break_long_shift_with_break(self):
        shift = ShiftSchedule(
            employee_id="emp1", company_id="co1",
            shift_date=date(2026, 6, 1),
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            break_minutes=30,
        )
        result = ComplianceValidationService.check_mandatory_break([shift])
        assert result == []

    def test_check_mandatory_break_overnight_shift(self):
        """Overnight: end_dt <= start_dt → +1 day."""
        shift = ShiftSchedule(
            employee_id="emp1", company_id="co1",
            shift_date=date(2026, 6, 1),
            shift_start=time(22, 0),
            shift_end=time(6, 0),   # 8 hrs overnight → violation if no break
            break_minutes=0,
        )
        result = ComplianceValidationService.check_mandatory_break([shift])
        assert len(result) == 1

    def test_check_mandatory_break_shift_date_as_datetime(self):
        """shift_date can be a datetime instance → branch for isinstance check."""
        shift = ShiftSchedule(
            employee_id="emp1", company_id="co1",
            shift_date=datetime(2026, 6, 1, 0, 0),  # datetime, not date
            shift_start=time(9, 0),
            shift_end=time(17, 0),
            break_minutes=0,
        )
        result = ComplianceValidationService.check_mandatory_break([shift])
        assert len(result) == 1

    # check_ot_threshold

    def test_check_ot_threshold_zero_threshold_skip(self):
        """threshold=0 (default) → always skip."""
        ts = Timesheet(
            employee_id="emp1", company_id="co1",
            pay_period_start=date(2026, 6, 1), pay_period_end=date(2026, 6, 7),
            total_regular_hrs=40.0, total_ot_hrs=20.0, status="draft",
        )
        result = ComplianceValidationService.check_ot_threshold([ts], {})
        assert result == []

    def test_check_ot_threshold_negative_policy_skip(self):
        result = ComplianceValidationService.check_ot_threshold(
            [], {"ot_alert_threshold": "-1"}
        )
        assert result == []

    def test_check_ot_threshold_exceeded(self):
        ts = Timesheet(
            employee_id="emp1", company_id="co1",
            pay_period_start=date(2026, 6, 1), pay_period_end=date(2026, 6, 7),
            total_regular_hrs=40.0, total_ot_hrs=15.0, status="draft",
        )
        result = ComplianceValidationService.check_ot_threshold(
            [ts], {"ot_alert_threshold": "10"}
        )
        assert len(result) == 1
        assert result[0]["violation_type"] == "ot_threshold"

    def test_check_ot_threshold_not_exceeded(self):
        ts = Timesheet(
            employee_id="emp1", company_id="co1",
            pay_period_start=date(2026, 6, 1), pay_period_end=date(2026, 6, 7),
            total_regular_hrs=40.0, total_ot_hrs=5.0, status="draft",
        )
        result = ComplianceValidationService.check_ot_threshold(
            [ts], {"ot_alert_threshold": "10"}
        )
        assert result == []

    def test_check_ot_threshold_none_ot_treated_as_zero(self):
        ts = Timesheet(
            employee_id="emp1", company_id="co1",
            pay_period_start=date(2026, 6, 1), pay_period_end=date(2026, 6, 7),
            total_regular_hrs=40.0, total_ot_hrs=None, status="draft",
        )
        result = ComplianceValidationService.check_ot_threshold(
            [ts], {"ot_alert_threshold": "10"}
        )
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# ComplianceService — async service paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestComplianceServiceUnit:
    async def test_run_validation_with_ot_threshold_violation(self, db_session: AsyncSession):
        company_id = await _co(db_session, "CSV Co")

        # Policy with low OT threshold
        from app.models.company_policy import CompanyPolicy
        db_session.add(CompanyPolicy(
            company_id=company_id,
            policy_key="ot_alert_threshold",
            policy_value="5",
            updated_by="admin",
        ))

        # Timesheet with OT > threshold
        ts = Timesheet(
            employee_id="cvc-emp1",
            company_id=company_id,
            pay_period_start=date(2026, 7, 1),
            pay_period_end=date(2026, 7, 7),
            total_regular_hrs=40.0,
            total_ot_hrs=10.0,  # > 5 threshold
            status="approved",
        )
        db_session.add(ts)
        await db_session.commit()

        svc = ComplianceService(db_session)
        result = await svc.run_validation(
            company_id, date(2026, 7, 1), date(2026, 7, 7), "admin-1"
        )
        assert result.violations_created >= 1
        types = {v.violation_type for v in result.violations}
        assert "ot_threshold" in types

    async def test_run_validation_with_max_hours_violation(self, db_session: AsyncSession):
        company_id = await _co(db_session, "CSV2 Co")

        from app.models.company_policy import CompanyPolicy
        db_session.add(CompanyPolicy(
            company_id=company_id,
            policy_key="max_hours_per_week",
            policy_value="40",
            updated_by="admin",
        ))
        ts = Timesheet(
            employee_id="cvc2-emp1",
            company_id=company_id,
            pay_period_start=date(2026, 7, 1),
            pay_period_end=date(2026, 7, 7),
            total_regular_hrs=45.0,
            total_ot_hrs=0.0,
            status="approved",
        )
        db_session.add(ts)
        await db_session.commit()

        svc = ComplianceService(db_session)
        result = await svc.run_validation(
            company_id, date(2026, 7, 1), date(2026, 7, 7), "admin-1"
        )
        assert result.violations_created >= 1
        types = {v.violation_type for v in result.violations}
        assert "max_hours" in types

    async def test_list_violations_with_filters(self, db_session: AsyncSession):
        company_id = await _co(db_session, "CSV3 Co")
        svc = ComplianceService(db_session)
        # Run validation to seed violations
        te = TimeEntry(
            employee_id="cvc3-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 2, 9, 0),
            clock_out=None,
            status="open",
        )
        db_session.add(te)
        await db_session.commit()
        await svc.run_validation(company_id, date(2026, 7, 1), date(2026, 7, 7), "admin")

        result = await svc.list_violations(
            company_id, violation_type="missing_punch", resolved=False
        )
        assert result.total >= 1
        for item in result.items:
            assert item.violation_type == "missing_punch"
            assert item.resolved is False

    async def test_list_violations_employee_filter(self, db_session: AsyncSession):
        company_id = await _co(db_session, "CSV4 Co")
        svc = ComplianceService(db_session)
        te = TimeEntry(
            employee_id="cvc4-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 2, 9, 0),
            clock_out=None,
            status="open",
        )
        db_session.add(te)
        await db_session.commit()
        await svc.run_validation(company_id, date(2026, 7, 1), date(2026, 7, 7), "admin")

        r1 = await svc.list_violations(company_id, employee_id="cvc4-emp")
        assert r1.total >= 1
        r2 = await svc.list_violations(company_id, employee_id="other-emp")
        assert r2.total == 0

    async def test_resolve_already_resolved_raises(self, db_session: AsyncSession):
        from app.models.compliance_violation import ComplianceViolation
        company_id = await _co(db_session, "CSV5 Co")
        v = ComplianceViolation(
            employee_id="emp1",
            company_id=company_id,
            violation_type="missing_punch",
            description="test",
            occurred_at=datetime(2026, 7, 1, 9, 0),
            resolved=True,
        )
        db_session.add(v)
        await db_session.commit()

        svc = ComplianceService(db_session)
        with pytest.raises(PunchError, match="already resolved"):
            await svc.resolve(str(v.id), "admin", "notes")

    async def test_resolve_not_found_raises(self, db_session: AsyncSession):
        svc = ComplianceService(db_session)
        with pytest.raises(PunchError, match="not found"):
            await svc.resolve("nonexistent-id", "admin", "notes")

    async def test_resolve_success(self, db_session: AsyncSession):
        from app.models.compliance_violation import ComplianceViolation
        company_id = await _co(db_session, "CSV6 Co")
        v = ComplianceViolation(
            employee_id="emp1",
            company_id=company_id,
            violation_type="missing_punch",
            description="test",
            occurred_at=datetime(2026, 7, 1, 9, 0),
            resolved=False,
        )
        db_session.add(v)
        await db_session.commit()

        svc = ComplianceService(db_session)
        result = await svc.resolve(str(v.id), "admin", "Fixed it")
        assert result.resolved is True
        assert result.resolved_by == "admin"


# ═══════════════════════════════════════════════════════════════════════════════
# TimeEntryService — all service paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestTimeEntryServiceUnit:
    async def test_clock_in_creates_attendance_record(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TES Co")
        svc = TimeEntryService(db_session)
        ts = datetime.utcnow() - timedelta(hours=1)
        entry = await svc.clock_in(
            "tes-emp1", company_id, None,
            timestamp=ts,
        )
        assert entry.status == "open"
        assert entry.clock_out is None

    async def test_clock_in_reuses_existing_attendance_record(self, db_session: AsyncSession):
        """When an AR already exists for the same date, no duplicate is created."""
        from app.models.attendance_record import AttendanceRecord
        company_id = await _co(db_session, "TES2 Co")
        today = datetime.utcnow().date()
        # Pre-create AR for today
        db_session.add(AttendanceRecord(
            employee_id="tes-emp2",
            company_id=company_id,
            date=today,
            status="present",
        ))
        await db_session.commit()

        ts = datetime.utcnow() - timedelta(minutes=30)
        svc = TimeEntryService(db_session)
        entry = await svc.clock_in(
            "tes-emp2", company_id, None,
            timestamp=ts,
        )
        assert entry.status == "open"

    async def test_clock_out_success(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TES3 Co")
        svc = TimeEntryService(db_session)
        ts_in = datetime.utcnow() - timedelta(hours=2)
        ts_out = datetime.utcnow() - timedelta(minutes=5)
        await svc.clock_in("tes-emp3", company_id, None, timestamp=ts_in)
        entry = await svc.clock_out("tes-emp3", timestamp=ts_out)
        assert entry.status == "closed"
        assert entry.clock_out is not None

    async def test_get_entries_with_filters(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TES4 Co")
        svc = TimeEntryService(db_session)
        ts_in = datetime.utcnow() - timedelta(hours=1)
        await svc.clock_in("tes-emp4", company_id, None, timestamp=ts_in)

        result = await svc.get_entries(
            employee_id="tes-emp4",
            company_id=company_id,
            status="open",
        )
        assert result["total"] == 1

    async def test_get_entries_no_match(self, db_session: AsyncSession):
        svc = TimeEntryService(db_session)
        result = await svc.get_entries(employee_id="nobody")
        assert result["total"] == 0

    async def test_get_entry_not_found(self, db_session: AsyncSession):
        svc = TimeEntryService(db_session)
        result = await svc.get_entry("nonexistent")
        assert result is None

    async def test_submit_correction_entry_not_found(self, db_session: AsyncSession):
        svc = TimeEntryService(db_session)
        with pytest.raises(PunchError, match="not found"):
            await svc.submit_correction(
                "nonexistent", "emp1",
                CorrectionRequest(
                    new_clock_in=datetime(2026, 7, 1, 9, 0),
                    reason="typo",
                ),
            )

    async def test_submit_correction_wrong_employee(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TES5 Co")
        entry = TimeEntry(
            employee_id="owner-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 1, 9, 0),
            status="closed",
        )
        db_session.add(entry)
        await db_session.commit()

        svc = TimeEntryService(db_session)
        with pytest.raises(PunchError, match="Cannot submit"):
            await svc.submit_correction(
                str(entry.id), "other-emp",
                CorrectionRequest(
                    new_clock_in=datetime(2026, 7, 1, 9, 30),
                    reason="typo",
                ),
            )

    async def test_submit_correction_success(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TES6 Co")
        entry = TimeEntry(
            employee_id="tes6-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 1, 9, 0),
            clock_out=datetime(2026, 7, 1, 17, 0),
            status="closed",
        )
        db_session.add(entry)
        await db_session.commit()

        svc = TimeEntryService(db_session)
        correction = await svc.submit_correction(
            str(entry.id), "tes6-emp",
            CorrectionRequest(
                new_clock_in=datetime(2026, 7, 1, 8, 0),
                new_clock_out=datetime(2026, 7, 1, 16, 0),
                reason="wrong time",
            ),
        )
        assert correction.status == "pending"

    async def test_submit_correction_no_clock_out(self, db_session: AsyncSession):
        """Correction with no new_clock_out (covers None branch)."""
        company_id = await _co(db_session, "TES7 Co")
        entry = TimeEntry(
            employee_id="tes7-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 1, 9, 0),
            status="open",
        )
        db_session.add(entry)
        await db_session.commit()

        svc = TimeEntryService(db_session)
        correction = await svc.submit_correction(
            str(entry.id), "tes7-emp",
            CorrectionRequest(
                new_clock_in=datetime(2026, 7, 1, 8, 30),
                new_clock_out=None,
                reason="early start",
            ),
        )
        assert correction.new_clock_out is None

    async def test_review_correction_not_found(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TES8 Co")
        entry = TimeEntry(
            employee_id="tes8-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 1, 9, 0),
            status="closed",
        )
        db_session.add(entry)
        await db_session.commit()

        svc = TimeEntryService(db_session)
        with pytest.raises(PunchError, match="Correction not found"):
            await svc.review_correction(
                str(entry.id), "nonexistent-corr", "reviewer",
                CorrectionReviewRequest(approve=True),
            )

    async def test_review_correction_approve(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TES9 Co")
        entry = TimeEntry(
            employee_id="tes9-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 1, 9, 0),
            clock_out=datetime(2026, 7, 1, 17, 0),
            status="closed",
        )
        db_session.add(entry)
        await db_session.commit()

        svc = TimeEntryService(db_session)
        correction = await svc.submit_correction(
            str(entry.id), "tes9-emp",
            CorrectionRequest(
                new_clock_in=datetime(2026, 7, 1, 8, 0),
                new_clock_out=datetime(2026, 7, 1, 16, 0),
                reason="earlier",
            ),
        )
        result = await svc.review_correction(
            str(entry.id), str(correction.id), "manager",
            CorrectionReviewRequest(approve=True),
        )
        assert result.status == "approved"
        await db_session.refresh(entry)
        assert entry.status == "corrected"

    async def test_review_correction_deny(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TES10 Co")
        entry = TimeEntry(
            employee_id="tes10-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 1, 9, 0),
            clock_out=datetime(2026, 7, 1, 17, 0),
            status="closed",
        )
        db_session.add(entry)
        await db_session.commit()

        svc = TimeEntryService(db_session)
        correction = await svc.submit_correction(
            str(entry.id), "tes10-emp",
            CorrectionRequest(
                new_clock_in=datetime(2026, 7, 1, 8, 0),
                reason="wrong",
            ),
        )
        result = await svc.review_correction(
            str(entry.id), str(correction.id), "manager",
            CorrectionReviewRequest(approve=False),
        )
        assert result.status == "denied"

    async def test_review_correction_already_reviewed(self, db_session: AsyncSession):
        from app.models.time_correction import TimeCorrection
        company_id = await _co(db_session, "TES11 Co")
        entry = TimeEntry(
            employee_id="tes11-emp",
            company_id=company_id,
            clock_in=datetime(2026, 7, 1, 9, 0),
            status="closed",
        )
        db_session.add(entry)
        await db_session.commit()

        corr = TimeCorrection(
            time_entry_id=entry.id,
            requested_by="tes11-emp",
            reason="test",
            original_clock_in=entry.clock_in,
            new_clock_in=datetime(2026, 7, 1, 8, 0),
            status="approved",  # already reviewed
        )
        db_session.add(corr)
        await db_session.commit()

        svc = TimeEntryService(db_session)
        with pytest.raises(PunchError, match="already been reviewed"):
            await svc.review_correction(
                str(entry.id), str(corr.id), "manager",
                CorrectionReviewRequest(approve=True),
            )


# ═══════════════════════════════════════════════════════════════════════════════
# AttendanceService
# ═══════════════════════════════════════════════════════════════════════════════

class TestAttendanceServiceUnit:
    async def test_get_attendance_with_filters(self, db_session: AsyncSession):
        from app.models.attendance_record import AttendanceRecord
        company_id = await _co(db_session, "AS Co")
        db_session.add(AttendanceRecord(
            employee_id="as-emp1",
            company_id=company_id,
            date=date(2026, 7, 1),
            status="present",
        ))
        await db_session.commit()

        svc = AttendanceService(db_session)
        result = await svc.get_attendance(company_id=company_id, employee_id="as-emp1")
        assert result["total"] == 1

    async def test_get_attendance_no_filters(self, db_session: AsyncSession):
        svc = AttendanceService(db_session)
        result = await svc.get_attendance()
        assert result["total"] == 0

    async def test_get_missing_punches_without_company(self, db_session: AsyncSession):
        """Open entry older than 24 hours → missing punch."""
        company_id = await _co(db_session, "MP Co")
        old_dt = datetime.utcnow() - timedelta(hours=25)
        db_session.add(TimeEntry(
            employee_id="mp-emp1",
            company_id=company_id,
            clock_in=old_dt,
            status="open",
        ))
        await db_session.commit()

        svc = AttendanceService(db_session)
        results = await svc.get_missing_punches()
        assert len(results) >= 1

    async def test_get_missing_punches_with_company_filter(self, db_session: AsyncSession):
        company_id = await _co(db_session, "MP2 Co")
        old_dt = datetime.utcnow() - timedelta(hours=25)
        db_session.add(TimeEntry(
            employee_id="mp2-emp1",
            company_id=company_id,
            clock_in=old_dt,
            status="open",
        ))
        await db_session.commit()

        svc = AttendanceService(db_session)
        results = await svc.get_missing_punches(company_id=company_id)
        assert len(results) >= 1

        other_results = await svc.get_missing_punches(company_id="other-co")
        assert len(other_results) == 0

    async def test_get_missing_punches_recent_entry_not_included(self, db_session: AsyncSession):
        """Entry clocked in less than 24 hours ago → not a missing punch."""
        company_id = await _co(db_session, "MP3 Co")
        recent_dt = datetime.utcnow() - timedelta(hours=1)
        db_session.add(TimeEntry(
            employee_id="mp3-emp1",
            company_id=company_id,
            clock_in=recent_dt,
            status="open",
        ))
        await db_session.commit()

        svc = AttendanceService(db_session)
        results = await svc.get_missing_punches(company_id=company_id)
        assert len(results) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# TimesheetService — generate, submit, approve, export error paths
# ═══════════════════════════════════════════════════════════════════════════════

class TestTimesheetServiceUnit:
    async def _seed_timesheet(
        self, db: AsyncSession, status: str = "draft", suffix: str = ""
    ) -> tuple[str, str, str]:
        label = suffix or status
        company_id = await _co(db, f"TS Co {label}")
        emp_id = f"ts-emp-{label}"
        ts = Timesheet(
            employee_id=emp_id,
            company_id=company_id,
            pay_period_start=date(2026, 7, 1),
            pay_period_end=date(2026, 7, 7),
            status=status,
            total_regular_hrs=40.0,
            total_ot_hrs=0.0,
        )
        db.add(ts)
        await db.commit()
        return str(ts.id), company_id, emp_id

    async def test_generate_invalid_dates(self, db_session: AsyncSession):
        company_id = await _co(db_session, "TG Co")
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="pay_period_end"):
            await svc.generate(
                "emp1", company_id,
                date(2026, 7, 7), date(2026, 7, 1),  # end before start
                "admin",
            )

    async def test_generate_with_no_entries(self, db_session: AsyncSession):
        """Generate timesheet for employee with no time entries → empty draft."""
        company_id = await _co(db_session, "TG2 Co")
        svc = TimesheetService(db_session)
        ts = await svc.generate(
            "tg2-emp", company_id,
            date(2026, 7, 1), date(2026, 7, 7),
            "admin",
        )
        assert ts.status == "draft"
        assert ts.total_regular_hrs == 0.0

    async def test_list_timesheets_with_filters(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "draft", "list")
        svc = TimesheetService(db_session)
        result = await svc.list_timesheets(
            employee_id=emp_id,
            company_id=company_id,
            status="draft",
        )
        assert result["total"] == 1

    async def test_get_timesheet_not_found(self, db_session: AsyncSession):
        svc = TimesheetService(db_session)
        result = await svc.get_timesheet("nonexistent")
        assert result is None

    async def test_submit_not_found(self, db_session: AsyncSession):
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="not found"):
            await svc.submit("nonexistent", "emp1")

    async def test_submit_wrong_employee(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "draft", "A")
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="own timesheets"):
            await svc.submit(ts_id, "wrong-emp")

    async def test_submit_not_draft_raises(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "submitted", "B")
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="draft timesheets"):
            await svc.submit(ts_id, emp_id)

    async def test_submit_success(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "draft", "C")
        svc = TimesheetService(db_session)
        ts = await svc.submit(ts_id, emp_id)
        assert ts.status == "submitted"

    async def test_approve_not_found(self, db_session: AsyncSession):
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="not found"):
            await svc.approve("nonexistent", "admin")

    async def test_approve_not_submitted_raises(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "draft", "D")
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="submitted timesheets"):
            await svc.approve(ts_id, "admin")

    async def test_approve_success(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "submitted", "E")
        svc = TimesheetService(db_session)
        ts = await svc.approve(ts_id, "admin")
        assert ts.status == "approved"

    async def test_export_not_found(self, db_session: AsyncSession):
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="not found"):
            await svc.export("nonexistent", "csv", "admin")

    async def test_export_not_approved_raises(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "draft", "F")
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="approved timesheets"):
            await svc.export(ts_id, "csv", "admin")

    async def test_export_invalid_format_raises(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "approved", "G")
        svc = TimesheetService(db_session)
        with pytest.raises(PunchError, match="export_format"):
            await svc.export(ts_id, "xml", "admin")

    async def test_export_csv(self, db_session: AsyncSession):
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "approved", "H")
        svc = TimesheetService(db_session)
        pe, content = await svc.export(ts_id, "csv", "admin")
        assert "timesheet_id" in content  # CSV header

    async def test_export_json(self, db_session: AsyncSession):
        import json as json_mod
        ts_id, company_id, emp_id = await self._seed_timesheet(db_session, "approved", "I")
        svc = TimesheetService(db_session)
        pe, content = await svc.export(ts_id, "json", "admin")
        data = json_mod.loads(content)
        assert "line_items" in data
