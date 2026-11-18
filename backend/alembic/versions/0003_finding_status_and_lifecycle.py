"""finding status and lifecycle fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-18 20:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0003_finding_status'
down_revision = '0002_extra_tables'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Safely add columns if not already present
    with op.batch_alter_table('findings') as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(), nullable=False, server_default='open'))
        batch_op.add_column(sa.Column('selected_replacement', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('decided_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('decided_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('dismissal_reason', sa.Text(), nullable=True))

def downgrade() -> None:
    with op.batch_alter_table('findings') as batch_op:
        batch_op.drop_column('dismissal_reason')
        batch_op.drop_column('decided_at')
        batch_op.drop_column('decided_by')
        batch_op.drop_column('selected_replacement')
        batch_op.drop_column('status')
