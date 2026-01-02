"""Calendar Post model for storing scheduled posts in content calendar."""

import uuid
from datetime import datetime, date, time
from sqlalchemy import Column, String, Text, DateTime, Date, Time, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class CalendarPost(Base):
    """Individual post in a content calendar."""

    __tablename__ = "calendar_posts"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    calendar_id = Column(UUID, ForeignKey("content_calendars.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Post content
    post_type = Column(String(50), nullable=False)  # promotional, product_showcase, etc.
    title = Column(String(255), nullable=False)
    post_text = Column(Text, nullable=False)

    # Scheduling
    scheduled_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(Time, nullable=False)
    platform = Column(String(50), nullable=False, default="both")  # facebook, instagram, both

    # Status
    status = Column(String(50), nullable=False, default="draft", index=True)  # draft, approved, rejected, published, failed

    # Media
    image_url = Column(String(500), nullable=True)
    asset_id = Column(UUID, ForeignKey("brand_assets.id", ondelete="SET NULL"), nullable=True)

    # Additional data
    featured_items = Column(JSON, nullable=True)  # List of menu item names
    hashtags = Column(JSON, nullable=True)  # List of hashtags
    call_to_action = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)  # Why this post was suggested
    generated_by = Column(String(50), nullable=True, default="template")  # "openai" or "template" for debugging

    # Publishing results
    platform_post_id = Column(String(255), nullable=True)
    published_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    engagement_metrics = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calendar = relationship("ContentCalendar", back_populates="posts")
    tenant = relationship("Tenant")
    asset = relationship("BrandAsset")

    def __repr__(self):
        return f"<CalendarPost(id={self.id}, title={self.title}, date={self.scheduled_date}, status={self.status})>"
