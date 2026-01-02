"""add asset_id to menu_items

Revision ID: 3a4346976245
Revises: ee873fe5c1e6
Create Date: 2025-12-29 01:49:51.632157

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '3a4346976245'
down_revision = 'ee873fe5c1e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add asset_id column to menu_items table with foreign key to brand_assets
    op.add_column('menu_items', sa.Column('asset_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_menu_items_asset_id',
        'menu_items',
        'brand_assets',
        ['asset_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key constraint and asset_id column
    op.drop_constraint('fk_menu_items_asset_id', 'menu_items', type_='foreignkey')
    op.drop_column('menu_items', 'asset_id')
