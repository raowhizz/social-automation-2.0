"""OAuth state model for CSRF protection."""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from .base import Base


class OAuthState(Base):
    """OAuth state tokens for CSRF protection."""

    __tablename__ = "oauth_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_token = Column(String(255), unique=True, nullable=False, index=True)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # Metadata
    return_url = Column(Text)
    ip_address = Column(INET)
    user_agent = Column(Text)

    # Expiration (default: 10 minutes)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(minutes=10),
        index=True,
    )
    used = Column(Boolean, default=False, index=True)
    used_at = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", back_populates="oauth_states")

    # Indexes
    __table_args__ = (
        Index(
            "idx_oauth_state_expires",
            "expires_at",
            postgresql_where=(used == False),
        ),
    )

    @property
    def is_expired(self):
        """Check if state token is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """Check if state token is valid (not used and not expired)."""
        return not self.used and not self.is_expired

    def __repr__(self):
        return f"<OAuthState {self.state_token[:8]}... (used={self.used})>"
