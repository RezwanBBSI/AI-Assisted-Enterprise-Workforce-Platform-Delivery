import json
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PunchError
from app.core.utils import now_utc
from app.models.audit_log import AuditLog
from app.models.leave_balance import LeaveBalance
from app.models.leave_request import LeaveRequest
from app.schemas.scheduling import LeaveRequestCreate, LeaveReviewRequest


class LeaveValidationService:
    """Stateless validation — 100% branch coverage required."""

    @staticmethod
    def validate_leave_dates(start: date, end: date) -> None:
        """Raise 422 if end date is before start date."""
        if end < start:
            raise PunchError("end_date must be on or after start_date", 422)

    @staticmethod
    def validate_leave_balance(
        balance: LeaveBalance | None,
        leave_type: str,
        days: float,
    ) -> None:
        """Raise 422 if requested days exceed available balance."""
        if balance is None:
            # No balance row means zero allocation; all types with > 0 days fail.
            if days > 0 and leave_type != "unpaid":
                raise PunchError(
                    f"Insufficient {leave_type} balance (0.0 available)", 422
                )
            return

        if leave_type == "pto":
            available = balance.pto_total - balance.pto_used
        elif leave_type == "sick":
            available = balance.sick_total - balance.sick_used
        elif leave_type == "comp":
            available = balance.comp_earned - balance.comp_used
        else:
            # unpaid — no balance check
            return

        if days > available:
            raise PunchError(
                f"Insufficient {leave_type} balance "
                f"({available:.1f} available, {days:.1f} requested)",
                422,
            )


class LeaveService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def submit(
        self,
        employee_id: str,
        company_id: str,
        payload: LeaveRequestCreate,
    ) -> LeaveRequest:
        LeaveValidationService.validate_leave_dates(payload.start_date, payload.end_date)

        # Check balance
        balance = await self._get_balance_row(
            employee_id, company_id, payload.start_date.year
        )
        LeaveValidationService.validate_leave_balance(
            balance, payload.leave_type, payload.days_requested
        )

        req = LeaveRequest(
            employee_id=employee_id,
            company_id=payload.company_id,
            leave_type=payload.leave_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            days_requested=payload.days_requested,
            reason=payload.reason,
            status="pending",
        )
        self._db.add(req)
        await self._db.flush()

        self._db.add(AuditLog(
            entity_type="leave_request",
            entity_id=req.id,
            action="leave_submitted",
            performed_by=employee_id,
            performed_at=now_utc(),
            details=json.dumps({
                "leave_type": payload.leave_type,
                "days": payload.days_requested,
            }),
        ))

        await self._db.commit()
        await self._db.refresh(req)
        return req

    async def list_requests(
        self,
        employee_id: str | None = None,
        company_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict:
        q = select(LeaveRequest)
        if employee_id:
            q = q.where(LeaveRequest.employee_id == employee_id)
        if company_id:
            q = q.where(LeaveRequest.company_id == company_id)
        if status:
            q = q.where(LeaveRequest.status == status)

        count_result = await self._db.execute(q)
        total = len(count_result.scalars().all())

        items = (
            await self._db.execute(q.offset((page - 1) * size).limit(size))
        ).scalars().all()

        return {"total": total, "page": page, "size": size, "items": list(items)}

    async def review(
        self,
        request_id: str,
        reviewed_by: str,
        payload: LeaveReviewRequest,
    ) -> LeaveRequest:
        result = await self._db.execute(
            select(LeaveRequest).where(LeaveRequest.id == request_id)
        )
        req = result.scalar_one_or_none()
        if req is None:
            raise PunchError("Leave request not found", 404)
        if req.status != "pending":
            raise PunchError("Leave request has already been reviewed", 409)

        req.reviewed_by = reviewed_by
        req.reviewed_at = now_utc()
        req.review_comment = payload.review_comment

        if payload.approve:
            req.status = "approved"
            # Deduct from balance
            balance = await self._get_or_create_balance(
                req.employee_id, req.company_id, req.start_date.year
            )
            if req.leave_type == "pto":
                balance.pto_used += req.days_requested
            elif req.leave_type == "sick":
                balance.sick_used += req.days_requested
            elif req.leave_type == "comp":
                balance.comp_used += req.days_requested
            balance.updated_at = now_utc()
            action = "leave_approved"
        else:
            req.status = "denied"
            action = "leave_denied"

        self._db.add(AuditLog(
            entity_type="leave_request",
            entity_id=request_id,
            action=action,
            performed_by=reviewed_by,
            performed_at=now_utc(),
            details=json.dumps({"approve": payload.approve}),
        ))

        await self._db.commit()
        await self._db.refresh(req)
        return req

    async def cancel(self, request_id: str, employee_id: str) -> LeaveRequest:
        result = await self._db.execute(
            select(LeaveRequest).where(LeaveRequest.id == request_id)
        )
        req = result.scalar_one_or_none()
        if req is None:
            raise PunchError("Leave request not found", 404)
        if req.employee_id != employee_id:
            raise PunchError("Cannot cancel another employee's leave request", 403)
        if req.status != "pending":
            raise PunchError("Only pending requests can be cancelled", 409)

        req.status = "cancelled"
        self._db.add(AuditLog(
            entity_type="leave_request",
            entity_id=request_id,
            action="leave_cancelled",
            performed_by=employee_id,
            performed_at=now_utc(),
            details="{}",
        ))

        await self._db.commit()
        await self._db.refresh(req)
        return req

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_balance_row(
        self, employee_id: str, company_id: str, year: int
    ) -> LeaveBalance | None:
        result = await self._db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.company_id == company_id,
                LeaveBalance.year == year,
            )
        )
        return result.scalar_one_or_none()

    async def _get_or_create_balance(
        self, employee_id: str, company_id: str, year: int
    ) -> LeaveBalance:
        balance = await self._get_balance_row(employee_id, company_id, year)
        if balance is None:
            balance = LeaveBalance(
                employee_id=employee_id,
                company_id=company_id,
                year=year,
            )
            self._db.add(balance)
            await self._db.flush()
        return balance


class LeaveBalanceService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_balance(
        self, employee_id: str, company_id: str, year: int
    ) -> LeaveBalance:
        """Return the balance row; auto-create with zeros if missing."""
        result = await self._db.execute(
            select(LeaveBalance).where(
                LeaveBalance.employee_id == employee_id,
                LeaveBalance.company_id == company_id,
                LeaveBalance.year == year,
            )
        )
        balance = result.scalar_one_or_none()
        if balance is None:
            balance = LeaveBalance(
                employee_id=employee_id,
                company_id=company_id,
                year=year,
            )
            self._db.add(balance)
            await self._db.commit()
            await self._db.refresh(balance)
        return balance
