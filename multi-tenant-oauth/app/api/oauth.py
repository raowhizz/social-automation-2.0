"""OAuth flow API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.models.base import get_db
from app.services import OAuthService
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/oauth", tags=["oauth"])
logger = get_logger(__name__)


class AuthorizeRequest(BaseModel):
    """OAuth authorization request."""

    tenant_id: str
    return_url: Optional[str] = None


class AuthorizeResponse(BaseModel):
    """OAuth authorization response."""

    authorization_url: str
    state: str


@router.post("/facebook/authorize", response_model=AuthorizeResponse)
def authorize_facebook(
    request: Request,
    auth_request: AuthorizeRequest,
    db: Session = Depends(get_db),
):
    """
    Generate Facebook OAuth authorization URL.

    Args:
        request: FastAPI request
        auth_request: Authorization request data
        db: Database session

    Returns:
        Authorization URL and state token

    Raises:
        HTTPException: If tenant not found or error occurs
    """
    logger.info(f"Generating Facebook OAuth URL for tenant: {auth_request.tenant_id}")

    try:
        oauth_service = OAuthService()

        # Get client IP and user agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        authorization_url, state = oauth_service.generate_authorization_url(
            db=db,
            tenant_id=auth_request.tenant_id,
            return_url=auth_request.return_url,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(f"Authorization URL generated for tenant: {auth_request.tenant_id}")

        return AuthorizeResponse(
            authorization_url=authorization_url,
            state=state,
        )

    except ValueError as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in authorization: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/facebook/callback")
def oauth_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Facebook"),
    state: str = Query(..., description="State token for CSRF protection"),
    error: Optional[str] = Query(None, description="Error from Facebook"),
    error_description: Optional[str] = Query(None, description="Error description"),
    db: Session = Depends(get_db),
):
    """
    Handle Facebook OAuth callback.

    Args:
        request: FastAPI request
        code: Authorization code from Facebook
        state: State token for CSRF protection
        error: Error from Facebook (if authorization failed)
        error_description: Error description
        db: Database session

    Returns:
        Redirect to return URL or success page

    Raises:
        HTTPException: If callback processing fails
    """
    logger.info(f"Received OAuth callback with state: {state[:8]}...")

    # Check for errors from Facebook
    if error:
        logger.error(f"Facebook OAuth error: {error} - {error_description}")
        raise HTTPException(
            status_code=400,
            detail=f"Facebook authorization failed: {error_description or error}",
        )

    try:
        oauth_service = OAuthService()

        # Get client IP and user agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Process callback
        result = oauth_service.handle_callback(
            db=db,
            code=code,
            state=state,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(
            f"OAuth callback successful - Tenant: {result['tenant_id']}, "
            f"Pages connected: {result['pages_connected']}"
        )

        # Redirect to return URL or default success page
        return_url = result.get("return_url") or "/"

        # Add success query parameters
        redirect_url = f"{return_url}?oauth_success=true&accounts={result['pages_connected']}"

        return RedirectResponse(url=redirect_url)

    except ValueError as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/accounts/{social_account_id}")
def disconnect_account(
    social_account_id: str,
    tenant_id: str = Query(..., description="Tenant ID"),
    db: Session = Depends(get_db),
):
    """
    Disconnect a social media account.

    Args:
        social_account_id: Social account UUID
        tenant_id: Tenant UUID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If account not found or error occurs
    """
    logger.info(f"Disconnecting social account: {social_account_id} for tenant: {tenant_id}")

    try:
        oauth_service = OAuthService()

        success = oauth_service.disconnect_account(
            db=db,
            social_account_id=social_account_id,
            tenant_id=tenant_id,
        )

        if success:
            logger.info(f"Social account disconnected successfully: {social_account_id}")
            return {"message": "Account disconnected successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to disconnect account")

    except ValueError as e:
        logger.error(f"Disconnect error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in disconnect: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
