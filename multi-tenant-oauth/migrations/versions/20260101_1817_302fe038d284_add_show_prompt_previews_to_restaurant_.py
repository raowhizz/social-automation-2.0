"""add show_prompt_previews to restaurant_profile

Revision ID: 302fe038d284
Revises: a8e22ca0f2d5
Create Date: 2026-01-01 18:17:53.171154

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '302fe038d284'
down_revision = 'a8e22ca0f2d5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add show_prompt_previews column to restaurant_profiles table
    op.add_column(
        'restaurant_profiles',
        sa.Column('show_prompt_previews', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    # Remove show_prompt_previews column
    op.drop_column('restaurant_profiles', 'show_prompt_previews')
