from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import now_utc
from app.models.company_policy import CompanyPolicy
from app.schemas.scheduling import PolicyUpdate


class PolicyService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_policies(self, company_id: str) -> list[CompanyPolicy]:
        result = await self._db.execute(
            select(CompanyPolicy).where(CompanyPolicy.company_id == company_id)
        )
        return list(result.scalars().all())

    async def upsert_policy(
        self,
        company_id: str,
        policy_key: str,
        payload: PolicyUpdate,
        updated_by: str,
    ) -> CompanyPolicy:
        result = await self._db.execute(
            select(CompanyPolicy).where(
                CompanyPolicy.company_id == company_id,
                CompanyPolicy.policy_key == policy_key,
            )
        )
        policy = result.scalar_one_or_none()
        if policy is None:
            policy = CompanyPolicy(
                company_id=company_id,
                policy_key=policy_key,
                policy_value=payload.policy_value,
                updated_by=updated_by,
                updated_at=now_utc(),
            )
            self._db.add(policy)
        else:
            policy.policy_value = payload.policy_value
            policy.updated_by = updated_by
            policy.updated_at = now_utc()

        await self._db.commit()
        await self._db.refresh(policy)
        return policy
