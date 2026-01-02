"""add_content_calendar_tables

Revision ID: ee873fe5c1e6
Revises: 761180c2eead
Create Date: 2025-12-28 23:57:00.278403

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee873fe5c1e6'
down_revision = '761180c2eead'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create content_calendars table
    op.create_table(
        'content_calendars',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),  # draft, approved, published
        sa.Column('total_posts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('approved_posts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('published_posts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_content_calendars_tenant_id', 'content_calendars', ['tenant_id'])
    op.create_index('ix_content_calendars_year_month', 'content_calendars', ['year', 'month'])

    # Create calendar_posts table
    op.create_table(
        'calendar_posts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('calendar_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('post_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('post_text', sa.Text(), nullable=False),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('scheduled_time', sa.Time(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),  # facebook, instagram, both
        sa.Column('status', sa.String(50), nullable=False),  # draft, approved, rejected, published, failed
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('asset_id', sa.UUID(), nullable=True),
        sa.Column('featured_items', sa.JSON(), nullable=True),
        sa.Column('hashtags', sa.JSON(), nullable=True),
        sa.Column('call_to_action', sa.String(255), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('platform_post_id', sa.String(255), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('engagement_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['calendar_id'], ['content_calendars.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['brand_assets.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_calendar_posts_calendar_id', 'calendar_posts', ['calendar_id'])
    op.create_index('ix_calendar_posts_tenant_id', 'calendar_posts', ['tenant_id'])
    op.create_index('ix_calendar_posts_scheduled_date', 'calendar_posts', ['scheduled_date'])
    op.create_index('ix_calendar_posts_status', 'calendar_posts', ['status'])


def downgrade() -> None:
    op.drop_index('ix_calendar_posts_status', table_name='calendar_posts')
    op.drop_index('ix_calendar_posts_scheduled_date', table_name='calendar_posts')
    op.drop_index('ix_calendar_posts_tenant_id', table_name='calendar_posts')
    op.drop_index('ix_calendar_posts_calendar_id', table_name='calendar_posts')
    op.drop_table('calendar_posts')

    op.drop_index('ix_content_calendars_year_month', table_name='content_calendars')
    op.drop_index('ix_content_calendars_tenant_id', table_name='content_calendars')
    op.drop_table('content_calendars')
