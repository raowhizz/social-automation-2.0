"""Post history model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class PostHistory(Base):
    """Social media post audit log."""

    __tablename__ = "post_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )
    social_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("social_accounts.id"),
        nullable=False,
        index=True,
    )

    # Platform
    platform = Column(String(50), nullable=False)
    platform_post_id = Column(String(255))

    # Content
    caption = Column(Text)
    image_url = Column(Text)
    campaign_name = Column(String(255), index=True)
    item_name = Column(String(255))

    # Status
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )
    posted_at = Column(DateTime)
    scheduled_for = Column(DateTime)
    error_message = Column(Text)

    # Engagement metrics (likes, comments, shares, etc.)
    engagement_metrics = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="posts")
    social_account = relationship("SocialAccount", back_populates="posts")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'published', 'failed', 'deleted', 'scheduled')",
            name="check_post_status",
        ),
        Index("idx_post_history_posted_date", "tenant_id", "posted_at"),
    )

    def __repr__(self):
        return f"<PostHistory {self.platform} - {self.status} ({self.campaign_name})>"
