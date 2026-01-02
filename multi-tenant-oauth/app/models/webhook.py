"""Webhook event model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class WebhookEvent(Base):
    """Webhook events from social media platforms."""

    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        index=True,
    )

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)

    # Processing
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime)
    error_message = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Indexes
    __table_args__ = (
        Index("idx_webhook_events_processed", "processed", "created_at"),
    )

    def __repr__(self):
        return f"<WebhookEvent {self.event_type} (processed={self.processed})>"
