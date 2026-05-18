"""sprint_4_payroll_tables

Revision ID: 3f7a91c4d82e
Revises: 18d82f8dca79
Create Date: 2026-05-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f7a91c4d82e'
down_revision: Union[str, Sequence[str], None] = '18d82f8dca79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create timesheets, payroll_line_items, and payroll_exports tables."""
    op.create_table(
        'timesheets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('employee_id', sa.String(length=36), nullable=False),
        sa.Column('company_id', sa.String(length=36), nullable=False),
        sa.Column('pay_period_start', sa.Date(), nullable=False),
        sa.Column('pay_period_end', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('total_regular_hrs', sa.Float(), nullable=False),
        sa.Column('total_ot_hrs', sa.Float(), nullable=False),
        sa.Column('total_holiday_hrs', sa.Float(), nullable=False),
        sa.Column('total_differential_hrs', sa.Float(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.String(length=36), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['employee_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('timesheets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_timesheets_employee_id'), ['employee_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_timesheets_company_id'), ['company_id'], unique=False)

    op.create_table(
        'payroll_line_items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('timesheet_id', sa.String(length=36), nullable=False),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('hours_worked', sa.Float(), nullable=False),
        sa.Column('rate_type', sa.String(length=24), nullable=False),
        sa.Column('rate_multiplier', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['timesheet_id'], ['timesheets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('payroll_line_items', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_payroll_line_items_timesheet_id'), ['timesheet_id'], unique=False
        )

    op.create_table(
        'payroll_exports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('company_id', sa.String(length=36), nullable=False),
        sa.Column('pay_period_start', sa.Date(), nullable=False),
        sa.Column('pay_period_end', sa.Date(), nullable=False),
        sa.Column('exported_at', sa.DateTime(), nullable=False),
        sa.Column('exported_by', sa.String(length=36), nullable=False),
        sa.Column('export_format', sa.String(length=8), nullable=False),
        sa.Column('record_count', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['exported_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('payroll_exports', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_payroll_exports_company_id'), ['company_id'], unique=False
        )


def downgrade() -> None:
    """Drop Sprint 4 payroll tables."""
    with op.batch_alter_table('payroll_exports', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_payroll_exports_company_id'))
    op.drop_table('payroll_exports')

    with op.batch_alter_table('payroll_line_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_payroll_line_items_timesheet_id'))
    op.drop_table('payroll_line_items')

    with op.batch_alter_table('timesheets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_timesheets_company_id'))
        batch_op.drop_index(batch_op.f('ix_timesheets_employee_id'))
    op.drop_table('timesheets')
