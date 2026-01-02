"""add_restaurant_intelligence_tables

Revision ID: 761180c2eead
Revises: dcfcaebd1983
Create Date: 2025-12-28 19:47:44.509742

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '761180c2eead'
down_revision = 'dcfcaebd1983'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create restaurant_profiles table
    op.create_table(
        'restaurant_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('cuisine_type', sa.String(100), nullable=True),
        sa.Column('location', sa.JSON(), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('brand_analysis', sa.JSON(), nullable=True),
        sa.Column('sales_insights', sa.JSON(), nullable=True),
        sa.Column('content_strategy', sa.JSON(), nullable=True),
        sa.Column('last_menu_import', sa.DateTime(), nullable=True),
        sa.Column('last_sales_import', sa.DateTime(), nullable=True),
        sa.Column('menu_items_count', sa.Integer(), nullable=True, default=0),
        sa.Column('sales_records_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', name='uq_restaurant_profiles_tenant_id')
    )
    op.create_index('ix_restaurant_profiles_tenant_id', 'restaurant_profiles', ['tenant_id'])

    # Create menu_items table
    op.create_table(
        'menu_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('external_id', sa.String(50), nullable=True),
        sa.Column('category', sa.String(255), nullable=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=True),
        sa.Column('cost', sa.Numeric(10, 2), nullable=True),
        sa.Column('has_modifiers', sa.Boolean(), nullable=True, default=False),
        sa.Column('modifiers', sa.JSON(), nullable=True),
        sa.Column('is_deal', sa.Boolean(), nullable=True, default=False),
        sa.Column('out_of_stock', sa.Boolean(), nullable=True, default=False),
        sa.Column('times_ordered', sa.Integer(), nullable=True, default=0),
        sa.Column('total_revenue', sa.Numeric(10, 2), nullable=True, default=0),
        sa.Column('popularity_rank', sa.Integer(), nullable=True),
        sa.Column('times_posted_about', sa.Integer(), nullable=True, default=0),
        sa.Column('last_featured_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )
    op.create_index('ix_menu_items_tenant_id', 'menu_items', ['tenant_id'])
    op.create_index('ix_menu_items_tenant_category', 'menu_items', ['tenant_id', 'category'])
    op.create_index('ix_menu_items_tenant_popularity', 'menu_items', ['tenant_id', 'popularity_rank'])

    # Create sales_data table
    op.create_table(
        'sales_data',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('order_id', sa.String(50), nullable=True),
        sa.Column('order_date', sa.DateTime(), nullable=False),
        sa.Column('items_ordered', sa.JSON(), nullable=True),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=True),
        sa.Column('tax', sa.Numeric(10, 2), nullable=True),
        sa.Column('tip', sa.Numeric(10, 2), nullable=True),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('customer_name', sa.String(255), nullable=True),
        sa.Column('customer_phone', sa.String(20), nullable=True),
        sa.Column('order_source', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )
    op.create_index('ix_sales_data_tenant_id', 'sales_data', ['tenant_id'])
    op.create_index('ix_sales_data_tenant_date', 'sales_data', ['tenant_id', 'order_date'])
    op.create_index('ix_sales_data_tenant_amount', 'sales_data', ['tenant_id', 'total_amount'])


def downgrade() -> None:
    op.drop_index('ix_sales_data_tenant_amount', table_name='sales_data')
    op.drop_index('ix_sales_data_tenant_date', table_name='sales_data')
    op.drop_index('ix_sales_data_tenant_id', table_name='sales_data')
    op.drop_table('sales_data')

    op.drop_index('ix_menu_items_tenant_popularity', table_name='menu_items')
    op.drop_index('ix_menu_items_tenant_category', table_name='menu_items')
    op.drop_index('ix_menu_items_tenant_id', table_name='menu_items')
    op.drop_table('menu_items')

    op.drop_index('ix_restaurant_profiles_tenant_id', table_name='restaurant_profiles')
    op.drop_table('restaurant_profiles')
