"""Background tasks for content calendar auto-publishing."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.tasks.celery_app import celery_app
from app.models.base import SessionLocal
from app.models import CalendarPost
from app.services.content_calendar_service import ContentCalendarService

logger = logging.getLogger(__name__)


@celery_app.task(name="publish_due_calendar_posts")
def publish_due_calendar_posts():
    """
    Periodic task to publish calendar posts that are due.
    Runs every minute to check for approved posts scheduled for now or earlier.
    """
    db = SessionLocal()
    try:
        # Get current datetime
        now = datetime.utcnow()

        # Find approved posts that are due (scheduled_date + scheduled_time <= now)
        due_posts = (
            db.query(CalendarPost)
            .filter(
                CalendarPost.status == "approved",
                CalendarPost.scheduled_date <= now.date(),
            )
            .all()
        )

        # Filter by time as well (since we can't easily query date + time in SQLAlchemy)
        posts_to_publish = []
        for post in due_posts:
            scheduled_datetime = datetime.combine(post.scheduled_date, post.scheduled_time)
            if scheduled_datetime <= now:
                posts_to_publish.append(post)

        if not posts_to_publish:
            logger.info(f"No calendar posts due for publishing at {now}")
            return {"published": 0, "failed": 0}

        logger.info(f"Found {len(posts_to_publish)} calendar posts to publish")

        # Publish each post
        calendar_service = ContentCalendarService()
        published_count = 0
        failed_count = 0

        for post in posts_to_publish:
            try:
                result = calendar_service.publish_calendar_post(db, str(post.id))
                if result.get('success'):
                    published_count += 1
                    logger.info(f"Published calendar post {post.id}: {post.title}")
                else:
                    failed_count += 1
                    logger.error(f"Failed to publish calendar post {post.id}: {result.get('error')}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Exception publishing calendar post {post.id}: {e}")

        return {
            "published": published_count,
            "failed": failed_count,
            "total_checked": len(posts_to_publish)
        }

    except Exception as e:
        logger.error(f"Error in publish_due_calendar_posts task: {e}")
        return {"error": str(e)}
    finally:
        db.close()
