"""Tenant management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.models.base import get_db
from app.models import Tenant, TenantUser
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])
logger = get_logger(__name__)


class TenantCreate(BaseModel):
    """Tenant registration request."""

    slug: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    plan_type: Optional[str] = "basic"


class TenantResponse(BaseModel):
    """Tenant response."""

    id: str
    slug: str
    name: str
    email: Optional[str]
    status: str
    plan_type: str
    created_at: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=TenantResponse)
def register_tenant(tenant_data: TenantCreate, db: Session = Depends(get_db)):
    """
    Register a new restaurant/tenant.

    Args:
        tenant_data: Tenant registration data
        db: Database session

    Returns:
        Created tenant

    Raises:
        HTTPException: If slug already exists
    """
    logger.info(f"Registering new tenant: {tenant_data.slug}")

    # Check if slug already exists
    existing = db.query(Tenant).filter(Tenant.slug == tenant_data.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Tenant with slug '{tenant_data.slug}' already exists")

    # Create tenant
    tenant = Tenant(
        slug=tenant_data.slug,
        name=tenant_data.name,
        email=tenant_data.email,
        phone=tenant_data.phone,
        plan_type=tenant_data.plan_type,
        status="active",
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    logger.info(f"Tenant registered successfully: {tenant.id}")

    return TenantResponse(
        id=str(tenant.id),
        slug=tenant.slug,
        name=tenant.name,
        email=tenant.email,
        status=tenant.status,
        plan_type=tenant.plan_type,
        created_at=tenant.created_at.isoformat(),
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """
    Get tenant details by ID.

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        Tenant details

    Raises:
        HTTPException: If tenant not found
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantResponse(
        id=str(tenant.id),
        slug=tenant.slug,
        name=tenant.name,
        email=tenant.email,
        status=tenant.status,
        plan_type=tenant.plan_type,
        created_at=tenant.created_at.isoformat(),
    )
