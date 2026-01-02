"""add_generated_by_to_calendar_posts

Revision ID: a8e22ca0f2d5
Revises: 3a4346976245
Create Date: 2025-12-29 16:35:38.597850

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8e22ca0f2d5'
down_revision = '3a4346976245'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add generated_by column to calendar_posts
    op.add_column('calendar_posts', sa.Column('generated_by', sa.String(50), nullable=True, server_default='template'))


def downgrade() -> None:
    # Remove generated_by column from calendar_posts
    op.drop_column('calendar_posts', 'generated_by')
