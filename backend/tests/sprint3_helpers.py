"""
Shared Sprint 3 fixture: extends Sprint 2 seed with a LeaveBalance
and default CompanyPolicy entries for testing.
"""
from datetime import datetime

from app.models.leave_balance import LeaveBalance
from app.models.company_policy import CompanyPolicy
from tests.sprint2_helpers import _seed_sprint2


async def _seed_sprint3(db_session, client) -> dict:
    """Extend _seed_sprint2 context with leave balance and policies."""
    ctx = await _seed_sprint2(db_session, client)

    employee_id = ctx["users"]["Employee"]
    company_id = ctx["company_id"]
    year = datetime.utcnow().year

    # Leave balance: 10 PTO, 5 sick, 5 comp
    balance = LeaveBalance(
        employee_id=employee_id,
        company_id=company_id,
        year=year,
        pto_total=10.0,
        pto_used=0.0,
        sick_total=5.0,
        sick_used=0.0,
        comp_earned=5.0,
        comp_used=0.0,
    )
    db_session.add(balance)

    # Default policies
    for key, value in [
        ("core_hours_start", '"09:00"'),
        ("core_hours_end", '"17:00"'),
    ]:
        db_session.add(CompanyPolicy(
            company_id=company_id,
            policy_key=key,
            policy_value=value,
        ))

    await db_session.commit()

    ctx["balance_id"] = balance.id
    ctx["year"] = year
    return ctx


__all__ = ["_seed_sprint3"]
