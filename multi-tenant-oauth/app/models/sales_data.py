"""SalesData model for storing order history and sales analytics."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import Base


class SalesData(Base):
    """Sales/order history model for trend analysis."""

    __tablename__ = "sales_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Order information
    order_id = Column(String(50))  # External order ID from POS
    order_date = Column(DateTime, nullable=False)
    items_ordered = Column(JSONB)  # Array of {name, quantity, price, modifiers}

    # Pricing breakdown
    subtotal = Column(Numeric(10, 2))
    tax = Column(Numeric(10, 2))
    tip = Column(Numeric(10, 2))
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Customer information (optional)
    customer_name = Column(String(255))
    customer_phone = Column(String(20))

    # Order metadata
    order_source = Column(String(50))  # e.g., "online", "phone", "walk-in"
    status = Column(String(50))  # e.g., "completed", "cancelled", "refunded"

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="sales_data")

    # Indexes for analytics queries
    __table_args__ = (
        Index("ix_sales_data_tenant_id", "tenant_id"),
        Index("ix_sales_data_tenant_date", "tenant_id", "order_date"),
        Index("ix_sales_data_tenant_amount", "tenant_id", "total_amount"),
    )

    def __repr__(self):
        return f"<SalesData order={self.order_id} (date={self.order_date}, total=${self.total_amount})>"
