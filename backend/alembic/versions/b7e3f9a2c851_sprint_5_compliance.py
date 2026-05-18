"""sprint_5_compliance_violations

Revision ID: b7e3f9a2c851
Revises: 3f7a91c4d82e
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7e3f9a2c851'
down_revision = '3f7a91c4d82e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'compliance_violations',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('employee_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('violation_type', sa.String(32), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_compliance_violations_employee_id', 'compliance_violations', ['employee_id'])
    op.create_index('ix_compliance_violations_company_id', 'compliance_violations', ['company_id'])
    op.create_index('ix_compliance_violations_violation_type', 'compliance_violations', ['violation_type'])


def downgrade() -> None:
    op.drop_index('ix_compliance_violations_violation_type', table_name='compliance_violations')
    op.drop_index('ix_compliance_violations_company_id', table_name='compliance_violations')
    op.drop_index('ix_compliance_violations_employee_id', table_name='compliance_violations')
    op.drop_table('compliance_violations')
