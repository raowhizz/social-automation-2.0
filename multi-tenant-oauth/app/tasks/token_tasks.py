"""
Celery tasks for token management and maintenance.
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.models.base import SessionLocal
from app.models import OAuthState
from app.services import TokenService
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.token_tasks.refresh_expiring_tokens")
def refresh_expiring_tokens():
    """
    Background task to refresh tokens expiring soon.

    Runs periodically (configured in Celery Beat schedule).
    Refreshes all tokens expiring within TOKEN_REFRESH_THRESHOLD_DAYS.

    Returns:
        Dictionary with refresh statistics
    """
    logger.info("Starting token refresh task")

    db: Session = SessionLocal()
    try:
        token_service = TokenService()

        # Refresh expiring tokens
        stats = token_service.refresh_expiring_tokens(db)

        logger.info(
            f"Token refresh task completed - "
            f"Total: {stats['total']}, "
            f"Success: {stats['success']}, "
            f"Failed: {stats['failed']}"
        )

        # Log errors if any
        if stats["errors"]:
            logger.error(f"Token refresh errors: {stats['errors']}")

        return stats

    except Exception as e:
        logger.error(f"Token refresh task failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.token_tasks.cleanup_expired_states")
def cleanup_expired_states():
    """
    Background task to cleanup expired OAuth state tokens.

    Runs periodically (configured in Celery Beat schedule).
    Deletes state tokens older than their expiration time.

    Returns:
        Number of states deleted
    """
    logger.info("Starting OAuth state cleanup task")

    db: Session = SessionLocal()
    try:
        # Delete expired states
        deleted_count = (
            db.query(OAuthState)
            .filter(OAuthState.expires_at < datetime.utcnow())
            .delete(synchronize_session=False)
        )

        db.commit()

        logger.info(f"OAuth state cleanup completed - Deleted: {deleted_count} expired states")

        return {"deleted": deleted_count}

    except Exception as e:
        logger.error(f"OAuth state cleanup task failed: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.token_tasks.refresh_single_token")
def refresh_single_token(token_id: str):
    """
    Refresh a single OAuth token.

    Args:
        token_id: OAuth token UUID

    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Refreshing single token: {token_id}")

    db: Session = SessionLocal()
    try:
        token_service = TokenService()
        success = token_service.refresh_token(db, token_id)

        if success:
            logger.info(f"Token refreshed successfully: {token_id}")
        else:
            logger.warning(f"Token refresh failed: {token_id}")

        return success

    except Exception as e:
        logger.error(f"Token refresh task failed for {token_id}: {e}", exc_info=True)
        raise
    finally:
        db.close()
