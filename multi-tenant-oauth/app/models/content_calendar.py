"""Content Calendar model for storing monthly post calendars."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base


class ContentCalendar(Base):
    """Monthly content calendar for a restaurant."""

    __tablename__ = "content_calendars"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Calendar period
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12

    # Status tracking
    status = Column(String(50), nullable=False, default="draft")  # draft, approved, published
    total_posts = Column(Integer, nullable=False, default=0)
    approved_posts = Column(Integer, nullable=False, default=0)
    published_posts = Column(Integer, nullable=False, default=0)

    # Timestamps
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="content_calendars")
    posts = relationship("CalendarPost", back_populates="calendar", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ContentCalendar(id={self.id}, year={self.year}, month={self.month}, status={self.status})>"
