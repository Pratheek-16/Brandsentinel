"""add finding source

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-21 11:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('findings', sa.Column('source', sa.String(), nullable=True, server_default='rule'))


def downgrade():
    op.drop_column('findings', 'source')
