"""Social accounts API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.models.base import get_db
from app.models import SocialAccount
from app.services import TokenService
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])
logger = get_logger(__name__)


class SocialAccountResponse(BaseModel):
    """Social account response."""

    id: str
    platform: str
    platform_account_id: str
    platform_username: Optional[str]
    account_name: Optional[str]
    account_type: Optional[str]
    is_active: bool
    connected_at: str

    class Config:
        from_attributes = True


class TokenHealthResponse(BaseModel):
    """Token health response."""

    tenant_id: str
    total_accounts: int
    active_tokens: int
    expiring_soon: int
    expired: int
    healthy: int
    accounts_by_platform: dict


@router.get("/connected", response_model=List[SocialAccountResponse])
def get_connected_accounts(
    tenant_id: str = Query(..., description="Tenant ID"),
    platform: Optional[str] = Query(None, description="Filter by platform (facebook, instagram)"),
    db: Session = Depends(get_db),
):
    """
    Get list of connected social accounts for a tenant.

    Args:
        tenant_id: Tenant UUID
        platform: Optional platform filter
        db: Database session

    Returns:
        List of connected social accounts

    Raises:
        HTTPException: If error occurs
    """
    logger.info(f"Fetching connected accounts for tenant: {tenant_id}")

    try:
        query = db.query(SocialAccount).filter(
            SocialAccount.tenant_id == tenant_id,
            SocialAccount.is_active == True,
        )

        if platform:
            query = query.filter(SocialAccount.platform == platform)

        accounts = query.order_by(SocialAccount.connected_at.desc()).all()

        logger.info(f"Found {len(accounts)} connected accounts for tenant: {tenant_id}")

        return [
            SocialAccountResponse(
                id=str(account.id),
                platform=account.platform,
                platform_account_id=account.platform_account_id,
                platform_username=account.platform_username,
                account_name=account.account_name,
                account_type=account.account_type,
                is_active=account.is_active,
                connected_at=account.connected_at.isoformat(),
            )
            for account in accounts
        ]

    except Exception as e:
        logger.error(f"Error fetching connected accounts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/token-health", response_model=TokenHealthResponse)
def get_token_health(
    tenant_id: str = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db),
):
    """
    Get token health status for a tenant.

    Args:
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        Token health statistics

    Raises:
        HTTPException: If error occurs
    """
    logger.info(f"Fetching token health for tenant: {tenant_id}")

    try:
        token_service = TokenService()
        health = token_service.get_tenant_token_health(db=db, tenant_id=tenant_id)

        logger.info(f"Token health retrieved for tenant: {tenant_id}")

        return TokenHealthResponse(**health)

    except Exception as e:
        logger.error(f"Error fetching token health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
