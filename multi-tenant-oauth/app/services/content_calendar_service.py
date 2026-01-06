"""Content Calendar Service - Generate monthly post calendars with strategic distribution."""

from typing import Dict, List, Any
import uuid
import calendar
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
import logging
import requests

from app.models import (
    ContentCalendar,
    CalendarPost,
    RestaurantProfile,
    MenuItem,
    SocialAccount,
)
from app.services.post_suggestion_service import PostSuggestionService
from app.services.token_service import TokenService

logger = logging.getLogger(__name__)


class GenerationStep:
    """Represents a single step in the calendar generation process."""

    def __init__(self, step_number: int, name: str, description: str):
        self.step_number = step_number
        self.name = name
        self.description = description
        self.status = "pending"  # pending, active, completed, failed
        self.started_at = None
        self.completed_at = None
        self.duration_ms = 0
        self.request = None
        self.response = None
        self.error = None
        self.metadata = {}

    def start(self):
        """Mark step as started."""
        self.status = "active"
        self.started_at = datetime.utcnow()

    def complete(self, response_data=None):
        """Mark step as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
        if response_data:
            self.response = response_data

    def fail(self, error_message: str):
        """Mark step as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error = error_message
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_number": self.step_number,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "request": self.request,
            "response": self.response,
            "error": self.error,
            "metadata": self.metadata,
        }


class GenerationLogger:
    """Tracks all steps during calendar generation."""

    def __init__(self):
        self.steps = []
        self.current_step = None
        self.started_at = datetime.utcnow()
        self.completed_at = None
        self.total_duration_ms = 0
        self.total_cost = 0.0
        self.total_tokens = 0

    def add_step(self, name: str, description: str) -> GenerationStep:
        """Add a new step."""
        step = GenerationStep(
            step_number=len(self.steps) + 1,
            name=name,
            description=description
        )
        self.steps.append(step)
        self.current_step = step
        step.start()
        return step

    def complete_current_step(self, response_data=None):
        """Complete the current step."""
        if self.current_step:
            self.current_step.complete(response_data)

    def fail_current_step(self, error_message: str):
        """Fail the current step."""
        if self.current_step:
            self.current_step.fail(error_message)

    def finalize(self):
        """Finalize the generation log."""
        self.completed_at = datetime.utcnow()
        delta = self.completed_at - self.started_at
        self.total_duration_ms = int(delta.total_seconds() * 1000)

    def to_dict(self) -> Dict[str, Any]:
        """Convert log to dictionary."""
        return {
            "steps": [step.to_dict() for step in self.steps],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_ms": self.total_duration_ms,
            "total_cost": round(self.total_cost, 4),
            "total_tokens": self.total_tokens,
            "total_steps": len(self.steps),
            "completed_steps": len([s for s in self.steps if s.status == "completed"]),
            "failed_steps": len([s for s in self.steps if s.status == "failed"]),
        }


class ContentCalendarService:
    """Generate and manage monthly content calendars."""

    def __init__(self):
        """Initialize content calendar service."""
        self.suggestion_service = PostSuggestionService()
        self.token_service = TokenService()

    async def generate_monthly_calendar(
        self,
        db: Session,
        tenant_id: str,
        year: int,
        month: int,
        posts_count: int = 25,
    ) -> Dict[str, Any]:
        """
        Generate a monthly content calendar with strategically distributed posts.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            year: Calendar year
            month: Calendar month (1-12)
            posts_count: Number of posts to generate (default 25)

        Returns:
            Dict with calendar and posts data
        """
        try:
            # Check if calendar already exists
            existing = db.query(ContentCalendar).filter(
                ContentCalendar.tenant_id == uuid.UUID(tenant_id),
                ContentCalendar.year == year,
                ContentCalendar.month == month,
            ).first()

            if existing:
                return {
                    "success": False,
                    "error": f"Calendar for {year}-{month:02d} already exists. Delete it first to regenerate."
                }

            # Get restaurant profile for context
            profile = db.query(RestaurantProfile).filter(
                RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
            ).first()

            if not profile:
                return {
                    "success": False,
                    "error": "Restaurant profile not found. Please complete setup first."
                }

            # Create calendar
            content_calendar = ContentCalendar(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                year=year,
                month=month,
                status="draft",
                total_posts=0,
                generated_at=datetime.utcnow(),
            )
            db.add(content_calendar)
            db.flush()  # Get calendar ID

            # Generate posts
            posts = await self._generate_calendar_posts(
                db,
                tenant_id,
                content_calendar.id,
                year,
                month,
                posts_count,
                profile,
            )

            # Update calendar totals
            content_calendar.total_posts = len(posts)
            db.commit()

            logger.info(f"Generated calendar {content_calendar.id} with {len(posts)} posts for {year}-{month:02d}")

            return {
                "success": True,
                "calendar_id": str(content_calendar.id),
                "year": year,
                "month": month,
                "total_posts": len(posts),
                "posts": [self._serialize_post(post) for post in posts],
            }

        except Exception as e:
            logger.error(f"Error generating monthly calendar: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def generate_monthly_calendar_with_logs(
        self,
        db: Session,
        tenant_id: str,
        year: int,
        month: int,
        posts_count: int = 25,
    ) -> Dict[str, Any]:
        """
        Generate monthly calendar with detailed logging of all steps.

        This method provides complete transparency into the generation process,
        logging every AI request, response, and step.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            year: Calendar year
            month: Calendar month (1-12)
            posts_count: Number of posts to generate

        Returns:
            Dict with calendar data and generation_log
        """
        gen_log = GenerationLogger()

        try:
            # Step 1: Check existing calendar
            step = gen_log.add_step("check_existing", "⏳ Checking for existing calendar...")
            existing = db.query(ContentCalendar).filter(
                ContentCalendar.tenant_id == uuid.UUID(tenant_id),
                ContentCalendar.year == year,
                ContentCalendar.month == month,
            ).first()

            if existing:
                step.fail(f"Calendar for {year}-{month:02d} already exists")
                gen_log.finalize()
                return {
                    "success": False,
                    "error": f"Calendar for {year}-{month:02d} already exists. Delete it first to regenerate.",
                    "generation_log": gen_log.to_dict()
                }

            step.complete({"message": f"✓ No existing calendar found for {year}-{month:02d}"})
            step.metadata["current_status"] = "✓ Ready to generate new calendar"

            # Step 2: Load restaurant profile
            step = gen_log.add_step("load_profile", "⏳ Loading restaurant profile...")
            profile = db.query(RestaurantProfile).filter(
                RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
            ).first()

            if not profile:
                step.fail("Restaurant profile not found")
                gen_log.finalize()
                return {
                    "success": False,
                    "error": "Restaurant profile not found. Please complete setup first.",
                    "generation_log": gen_log.to_dict()
                }

            step.complete({
                "restaurant_name": profile.name or "Unknown",
                "cuisine": profile.cuisine_type,
                "has_brand_analysis": bool(profile.brand_analysis),
                "has_sales_insights": bool(profile.sales_insights)
            })
            step.metadata["current_status"] = f"✓ Loaded profile: {profile.name or 'Unknown'}"

            # Step 3: Load menu items
            step = gen_log.add_step("load_menu", "⏳ Fetching menu items...")
            menu_items = db.query(MenuItem).filter(
                MenuItem.tenant_id == uuid.UUID(tenant_id)
            ).all()

            step.complete({"menu_items_count": len(menu_items)})
            step.metadata["current_status"] = f"✓ Loaded {len(menu_items)} menu items"

            # Step 4: Create calendar record
            step = gen_log.add_step("create_calendar", "⏳ Creating calendar record...")
            content_calendar = ContentCalendar(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                year=year,
                month=month,
                status="draft",
                total_posts=0,
                generated_at=datetime.utcnow(),
            )
            db.add(content_calendar)
            db.flush()

            step.complete({"calendar_id": str(content_calendar.id)})
            step.metadata["current_status"] = f"✓ Calendar record created for {calendar.month_name[month]} {year}"

            # Step 5: Generate posts with detailed logging
            step = gen_log.add_step("generate_posts", f"⏳ Generating {posts_count} posts...")
            step.metadata["current_status"] = "⏳ Starting post generation..."

            # Call the existing _generate_calendar_posts method
            # We'll pass the logger so it can add substeps
            posts = await self._generate_calendar_posts_with_logging(
                db,
                tenant_id,
                content_calendar.id,
                year,
                month,
                posts_count,
                profile,
                gen_log
            )

            step.complete({"posts_generated": len(posts)})
            step.metadata["current_status"] = f"✓ Generated {len(posts)} posts"

            # Step 6: Save calendar
            step = gen_log.add_step("save_calendar", "⏳ Saving calendar to database...")
            content_calendar.total_posts = len(posts)
            db.commit()

            step.complete({"total_posts": len(posts)})
            step.metadata["current_status"] = f"✓ Calendar saved with {len(posts)} posts"

            # Finalize logging
            gen_log.finalize()

            logger.info(f"Generated calendar with logs: {len(posts)} posts in {gen_log.total_duration_ms}ms")

            return {
                "success": True,
                "calendar_id": str(content_calendar.id),
                "year": year,
                "month": month,
                "total_posts": len(posts),
                "posts": [self._serialize_post(post) for post in posts],
                "generation_log": gen_log.to_dict()
            }

        except Exception as e:
            logger.error(f"Error generating calendar with logs: {e}")
            if gen_log.current_step:
                gen_log.fail_current_step(str(e))
            gen_log.finalize()
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "generation_log": gen_log.to_dict()
            }

    async def _generate_calendar_posts_with_logging(
        self,
        db: Session,
        tenant_id: str,
        calendar_id: uuid.UUID,
        year: int,
        month: int,
        posts_count: int,
        profile: RestaurantProfile,
        gen_log: GenerationLogger
    ) -> List[CalendarPost]:
        """
        Generate posts with detailed logging for each post.

        This is a wrapper around _generate_calendar_posts that adds logging.
        """
        # Clear any previous OpenAI calls
        self.suggestion_service.openai_calls = []

        # Call the original method
        posts = await self._generate_calendar_posts(
            db, tenant_id, calendar_id, year, month, posts_count, profile
        )

        # Retrieve OpenAI calls made during generation
        openai_calls = self.suggestion_service.openai_calls

        # Add logging for each post with OpenAI request/response data
        for i, post in enumerate(posts, 1):
            post_date = post.scheduled_date.strftime("%b %d") if post.scheduled_date else f"Post {i}"

            # Get corresponding OpenAI call if available
            openai_data = openai_calls[i-1] if i <= len(openai_calls) else None

            gen_log.steps[-1].metadata[f"post_{i}"] = {
                "date": post_date,
                "caption_preview": post.post_text[:50] + "..." if len(post.post_text) > 50 else post.post_text,
                "status": "✓ Generated"
            }

            # Add OpenAI request/response data if available
            if openai_data:
                gen_log.steps[-1].metadata[f"post_{i}_openai"] = openai_data

            # Update current status for progress display
            gen_log.steps[-1].metadata["current_status"] = f"✓ Generated post {i}/{posts_count}: {post_date}"
            gen_log.steps[-1].metadata["next_status"] = f"⏳ Generating post {i+1}/{posts_count}..." if i < posts_count else "✓ All posts generated!"

        # Store full OpenAI data in the step for easy access
        if openai_calls:
            gen_log.steps[-1].request = {"openai_calls": openai_calls}
            gen_log.steps[-1].response = {"total_calls": len(openai_calls)}

        return posts

    async def _generate_calendar_posts(
        self,
        db: Session,
        tenant_id: str,
        calendar_id: uuid.UUID,
        year: int,
        month: int,
        posts_count: int,
        profile: RestaurantProfile,
    ) -> List[CalendarPost]:
        """Generate posts for the calendar with strategic distribution."""
        posts = []

        # Get month details
        month_days = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)

        # Get sales insights for strategic scheduling
        sales_insights = profile.sales_insights or {}
        sales_patterns = sales_insights.get('sales_patterns', {})
        slowest_days = sales_patterns.get('slowest_days', [])
        busiest_days = sales_patterns.get('busiest_days', [])

        # Generate varied suggestions
        suggestions_result = await self.suggestion_service.generate_suggestions(
            db, tenant_id, count=posts_count
        )

        if not suggestions_result.get('success'):
            logger.warning(f"Failed to generate suggestions: {suggestions_result.get('error')}")
            return posts

        suggestions = suggestions_result.get('suggestions', [])

        # Distribute posts across the month using hybrid scheduling
        # This respects target_day preferences while ensuring even distribution
        post_schedule = self._smart_day_distribution(suggestions, year, month)

        for suggestion, day_number in post_schedule:
            post_date = date(year, month, day_number)
            day_name = post_date.strftime('%A')

            # Determine optimal posting time based on post type and day
            post_time = self._get_optimal_posting_time(
                suggestion.get('type'),
                day_name,
                slowest_days,
                busiest_days,
            )

            # Get image for post (hybrid: assets first, then AI)
            asset_id, image_url = await self.suggestion_service._get_post_image(
                db=db,
                tenant_id=tenant_id,
                post_type=suggestion.get('type', 'general'),
                featured_items=suggestion.get('featured_items', []),
                post_text=suggestion.get('post_text', ''),
                profile=profile,
            )

            # Create calendar post
            calendar_post = CalendarPost(
                id=uuid.uuid4(),
                calendar_id=calendar_id,
                tenant_id=uuid.UUID(tenant_id),
                post_type=suggestion.get('type', 'general'),
                title=suggestion.get('title', 'Untitled Post'),
                post_text=suggestion.get('post_text', ''),
                scheduled_date=post_date,
                scheduled_time=post_time,
                platform="both",  # Default to both platforms
                status="draft",
                image_url=image_url,
                asset_id=asset_id,
                featured_items=suggestion.get('featured_items', []),
                hashtags=suggestion.get('hashtags', []),
                call_to_action=suggestion.get('call_to_action'),
                reason=suggestion.get('reason'),
                generated_by=suggestion.get('generated_by', 'template'),
            )

            posts.append(calendar_post)
            db.add(calendar_post)

        db.flush()
        return posts

    def _calculate_posting_schedule(self, month_days: int, posts_count: int) -> List[int]:
        """
        Calculate which days to post on for even distribution.

        Args:
            month_days: Number of days in the month
            posts_count: Number of posts to distribute

        Returns:
            List of day numbers (1-31) to post on
        """
        if posts_count >= month_days:
            # Post every day
            return list(range(1, month_days + 1))

        # Distribute posts evenly across the month
        interval = month_days / posts_count
        days = []

        for i in range(posts_count):
            day = int((i * interval) + 1)
            if day > month_days:
                day = month_days
            if day not in days:
                days.append(day)

        return sorted(days)

    def _smart_day_distribution(
        self,
        suggestions: List[Dict[str, Any]],
        year: int,
        month: int
    ) -> List[tuple[Dict[str, Any], int]]:
        """
        Hybrid scheduling: Respect target_day preferences while ensuring even distribution.

        Args:
            suggestions: List of post suggestions with target_day field
            year: Year for the calendar
            month: Month number (1-12)

        Returns:
            List of (suggestion, day_number) tuples
        """
        import calendar
        from collections import defaultdict

        # Get number of days in month
        month_days = calendar.monthrange(year, month)[1]

        # Build map of day names to day numbers in the month
        # E.g., {"Monday": [1, 8, 15, 22, 29], "Tuesday": [2, 9, 16, 23, 30], ...}
        day_name_to_numbers = defaultdict(list)
        for day_num in range(1, month_days + 1):
            day_date = date(year, month, day_num)
            day_name = day_date.strftime('%A')
            day_name_to_numbers[day_name].append(day_num)

        # Group suggestions by their target_day
        target_day_groups = defaultdict(list)
        for suggestion in suggestions:
            target_day = suggestion.get('target_day', 'Monday')  # Default to Monday if not specified
            target_day_groups[target_day].append(suggestion)

        # Distribute posts to specific days
        result = []
        used_days = set()

        # Process each target day group
        for target_day, posts in target_day_groups.items():
            available_days = [d for d in day_name_to_numbers[target_day] if d not in used_days]

            if not available_days:
                # Fallback: target day is full, use adjacent days
                # Try next day, then previous day
                fallback_days = []
                for offset in [1, -1, 2, -2, 3, -3]:
                    fallback_date = date(year, month, 1) + timedelta(days=offset)
                    if fallback_date.month == month:
                        fallback_day_name = fallback_date.strftime('%A')
                        fallback_days.extend([d for d in day_name_to_numbers[fallback_day_name] if d not in used_days])
                available_days = fallback_days[:len(posts)]

            # Distribute posts across available days of this type
            # If we have 3 posts and 4 Fridays, space them out: use Fridays 1, 2, 4 (skip 3)
            num_posts = len(posts)
            num_available = len(available_days)

            if num_available >= num_posts:
                # Space posts evenly across available days
                if num_posts == 1:
                    # Single post: use the middle occurrence
                    selected_days = [available_days[num_available // 2]]
                else:
                    # Multiple posts: distribute evenly
                    step = num_available / num_posts
                    selected_days = [available_days[int(i * step)] for i in range(num_posts)]
            else:
                # More posts than available days - use all available days
                selected_days = available_days

            # Assign posts to days
            for i, post in enumerate(posts):
                if i < len(selected_days):
                    day_num = selected_days[i]
                    result.append((post, day_num))
                    used_days.add(day_num)
                else:
                    # Fallback: find any unused day
                    for day_num in range(1, month_days + 1):
                        if day_num not in used_days:
                            result.append((post, day_num))
                            used_days.add(day_num)
                            break

        # Sort by day number to maintain chronological order
        result.sort(key=lambda x: x[1])

        return result

    def _get_optimal_posting_time(
        self,
        post_type: str,
        day_name: str,
        slowest_days: List[str],
        busiest_days: List[str],
    ) -> time:
        """
        Determine optimal posting time based on post type and day.

        Args:
            post_type: Type of post
            day_name: Day of week name
            slowest_days: List of slowest days
            busiest_days: List of busiest days

        Returns:
            Time object for posting
        """
        # Promotional posts on slow days - post early (10 AM)
        if post_type == "promotional" or day_name in slowest_days:
            return time(10, 0)

        # Weekend driver posts on Friday - post late afternoon (5 PM)
        if post_type == "weekend_traffic" or day_name == "Friday":
            return time(17, 0)

        # Product showcase - dinner time (6 PM)
        if post_type == "product_showcase":
            return time(18, 0)

        # Engagement posts - mid-day for better engagement (12 PM)
        if post_type == "engagement":
            return time(12, 0)

        # Customer appreciation - afternoon (3 PM)
        if post_type == "customer_appreciation":
            return time(15, 0)

        # Default: lunch time (12 PM)
        return time(12, 0)

    def _serialize_post(self, post: CalendarPost) -> Dict[str, Any]:
        """Serialize calendar post to dict."""
        return {
            "id": str(post.id),
            "post_type": post.post_type,
            "title": post.title,
            "post_text": post.post_text,
            "scheduled_date": post.scheduled_date.isoformat(),
            "scheduled_time": post.scheduled_time.isoformat(),
            "platform": post.platform,
            "status": post.status,
            "image_url": post.image_url,
            "asset_id": str(post.asset_id) if post.asset_id else None,
            "featured_items": post.featured_items,
            "hashtags": post.hashtags,
            "call_to_action": post.call_to_action,
            "reason": post.reason,
            "generated_by": post.generated_by,
        }

    async def get_calendar(
        self,
        db: Session,
        tenant_id: str,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Get calendar for a specific month."""
        try:
            content_calendar = db.query(ContentCalendar).filter(
                ContentCalendar.tenant_id == uuid.UUID(tenant_id),
                ContentCalendar.year == year,
                ContentCalendar.month == month,
            ).first()

            if not content_calendar:
                return {
                    "success": False,
                    "error": f"No calendar found for {year}-{month:02d}"
                }

            posts = db.query(CalendarPost).filter(
                CalendarPost.calendar_id == content_calendar.id
            ).order_by(CalendarPost.scheduled_date, CalendarPost.scheduled_time).all()

            return {
                "success": True,
                "calendar": {
                    "id": str(content_calendar.id),
                    "year": content_calendar.year,
                    "month": content_calendar.month,
                    "status": content_calendar.status,
                    "total_posts": content_calendar.total_posts,
                    "approved_posts": content_calendar.approved_posts,
                    "published_posts": content_calendar.published_posts,
                },
                "posts": [self._serialize_post(post) for post in posts],
            }

        except Exception as e:
            logger.error(f"Error getting calendar: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def approve_calendar(
        self,
        db: Session,
        calendar_id: str,
    ) -> Dict[str, Any]:
        """Approve all posts in a calendar."""
        try:
            content_calendar = db.query(ContentCalendar).filter(
                ContentCalendar.id == uuid.UUID(calendar_id)
            ).first()

            if not content_calendar:
                return {
                    "success": False,
                    "error": "Calendar not found"
                }

            # Approve all draft posts
            posts = db.query(CalendarPost).filter(
                CalendarPost.calendar_id == uuid.UUID(calendar_id),
                CalendarPost.status == "draft"
            ).all()

            for post in posts:
                post.status = "approved"

            content_calendar.status = "approved"
            content_calendar.approved_at = datetime.utcnow()
            content_calendar.approved_posts = len(posts)

            db.commit()

            logger.info(f"Approved calendar {calendar_id} with {len(posts)} posts")

            return {
                "success": True,
                "calendar_id": calendar_id,
                "approved_posts": len(posts),
            }

        except Exception as e:
            logger.error(f"Error approving calendar: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def update_post(
        self,
        db: Session,
        post_id: str,
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a calendar post."""
        try:
            post = db.query(CalendarPost).filter(
                CalendarPost.id == uuid.UUID(post_id)
            ).first()

            if not post:
                return {
                    "success": False,
                    "error": "Post not found"
                }

            # Update fields
            if 'post_text' in updates:
                post.post_text = updates['post_text']
            if 'title' in updates:
                post.title = updates['title']
            if 'scheduled_date' in updates:
                post.scheduled_date = datetime.fromisoformat(updates['scheduled_date']).date()
            if 'scheduled_time' in updates:
                # Parse time string (format: HH:MM or HH:MM:SS)
                time_str = updates['scheduled_time']
                post.scheduled_time = datetime.strptime(time_str, '%H:%M:%S' if time_str.count(':') == 2 else '%H:%M').time()
            if 'platform' in updates:
                post.platform = updates['platform']
            if 'hashtags' in updates:
                post.hashtags = updates['hashtags']
            if 'status' in updates:
                post.status = updates['status']

            post.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Updated calendar post {post_id}")

            return {
                "success": True,
                "post": self._serialize_post(post),
            }

        except Exception as e:
            logger.error(f"Error updating post: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def delete_post(
        self,
        db: Session,
        post_id: str,
    ) -> Dict[str, Any]:
        """Delete a calendar post."""
        try:
            post = db.query(CalendarPost).filter(
                CalendarPost.id == uuid.UUID(post_id)
            ).first()

            if not post:
                return {
                    "success": False,
                    "error": "Post not found"
                }

            calendar_id = post.calendar_id
            db.delete(post)

            # Update calendar totals
            content_calendar = db.query(ContentCalendar).filter(
                ContentCalendar.id == calendar_id
            ).first()

            if content_calendar:
                content_calendar.total_posts = db.query(CalendarPost).filter(
                    CalendarPost.calendar_id == calendar_id
                ).count()

            db.commit()

            logger.info(f"Deleted calendar post {post_id}")

            return {
                "success": True,
                "post_id": post_id,
            }

        except Exception as e:
            logger.error(f"Error deleting post: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def delete_calendar(
        self,
        db: Session,
        tenant_id: str,
        year: int,
        month: int,
    ) -> Dict[str, Any]:
        """Delete an entire calendar and all its posts."""
        try:
            content_calendar = db.query(ContentCalendar).filter(
                ContentCalendar.tenant_id == uuid.UUID(tenant_id),
                ContentCalendar.year == year,
                ContentCalendar.month == month,
            ).first()

            if not content_calendar:
                return {
                    "success": False,
                    "error": f"No calendar found for {year}-{month:02d}"
                }

            # Delete all posts in the calendar (CASCADE should handle this, but being explicit)
            db.query(CalendarPost).filter(
                CalendarPost.calendar_id == content_calendar.id
            ).delete()

            # Delete the calendar
            db.delete(content_calendar)
            db.commit()

            logger.info(f"Deleted calendar for {year}-{month:02d} (tenant {tenant_id})")

            return {
                "success": True,
                "message": f"Calendar for {year}-{month:02d} deleted successfully",
            }

        except Exception as e:
            logger.error(f"Error deleting calendar: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    def publish_calendar_post(
        self,
        db: Session,
        post_id: str,
    ) -> Dict[str, Any]:
        """
        Publish a calendar post to social media.

        Args:
            db: Database session
            post_id: Post UUID

        Returns:
            Dict with success status and results
        """
        try:
            post = db.query(CalendarPost).filter(
                CalendarPost.id == uuid.UUID(post_id)
            ).first()

            if not post:
                return {
                    "success": False,
                    "error": "Post not found"
                }

            if post.status != "approved":
                return {
                    "success": False,
                    "error": f"Post status is '{post.status}', must be 'approved' to publish"
                }

            # Get OAuth tokens
            platforms_to_post = []
            if post.platform == "both":
                platforms_to_post = ["facebook", "instagram"]
            else:
                platforms_to_post = [post.platform]

            results = []
            all_succeeded = True

            for platform in platforms_to_post:
                try:
                    # Get OAuth token
                    access_token = self.token_service.get_active_token(
                        db=db,
                        tenant_id=str(post.tenant_id),
                        platform=platform,
                    )

                    if not access_token:
                        raise Exception(f"No active OAuth token found for {platform}")

                    # Get social account
                    social_account = (
                        db.query(SocialAccount)
                        .filter(
                            SocialAccount.tenant_id == post.tenant_id,
                            SocialAccount.platform == platform,
                        )
                        .first()
                    )

                    if not social_account:
                        raise Exception(f"No social account found for {platform}")

                    # Build caption with hashtags
                    caption = post.post_text
                    if post.hashtags:
                        hashtags_str = " ".join([f"#{tag}" if not tag.startswith("#") else tag for tag in post.hashtags])
                        caption = f"{caption}\n\n{hashtags_str}"

                    # Resolve image URL (prioritize direct URL over asset_id)
                    # Direct URLs (like S3) should always take precedence over asset URLs (may be ngrok)
                    image_url = post.image_url
                    if not image_url and post.asset_id:
                        # Fallback to asset if no direct URL
                        asset = db.query(BrandAsset).filter(BrandAsset.id == post.asset_id).first()
                        if asset:
                            image_url = asset.file_url

                    # Post to platform
                    if platform == "facebook":
                        platform_post_id = self._post_to_facebook(
                            page_id=social_account.platform_account_id,
                            access_token=access_token,
                            caption=caption,
                            image_url=image_url,
                        )
                        results.append({"platform": platform, "post_id": platform_post_id})
                    elif platform == "instagram":
                        if not image_url:
                            raise Exception("Instagram posts require an image")
                        platform_post_id = self._post_to_instagram(
                            instagram_account_id=social_account.platform_account_id,
                            access_token=access_token,
                            caption=caption,
                            image_url=image_url,
                        )
                        results.append({"platform": platform, "post_id": platform_post_id})

                except Exception as e:
                    all_succeeded = False
                    results.append({"platform": platform, "error": str(e)})
                    logger.error(f"Failed to post to {platform}: {e}")

            # Update post status
            if all_succeeded:
                post.status = "published"
                post.published_at = datetime.utcnow()
                # Store the first platform post ID (or combine them)
                if results:
                    post.platform_post_id = results[0].get("post_id")
            else:
                post.status = "failed"
                error_messages = [r.get("error") for r in results if "error" in r]
                post.error_message = "; ".join(error_messages)

            # Store engagement metrics placeholder
            post.engagement_metrics = {
                "published_to": [r.get("platform") for r in results if "post_id" in r],
                "published_at": datetime.utcnow().isoformat(),
            }

            db.commit()

            logger.info(f"Published calendar post {post_id} to {len([r for r in results if 'post_id' in r])} platform(s)")

            return {
                "success": all_succeeded,
                "post_id": post_id,
                "results": results,
                "status": post.status,
            }

        except Exception as e:
            logger.error(f"Error publishing calendar post: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    def _post_to_facebook(
        self,
        page_id: str,
        access_token: str,
        caption: str,
        image_url: str = None,
    ) -> str:
        """Post to Facebook and return post ID."""
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"

        data = {
            "message": caption,
            "access_token": access_token,
        }

        if image_url:
            url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
            data["url"] = image_url
            data["caption"] = caption
            del data["message"]

        response = requests.post(url, data=data)
        result = response.json()

        if "id" in result:
            return result["id"]
        elif "error" in result:
            raise Exception(result["error"].get("message", "Unknown error"))
        else:
            raise Exception("Failed to post to Facebook")

    def _post_to_instagram(
        self,
        instagram_account_id: str,
        access_token: str,
        caption: str,
        image_url: str,
    ) -> str:
        """Post to Instagram and return media ID."""
        # Step 1: Create container
        container_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}/media"
        container_data = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        }

        response = requests.post(container_url, data=container_data)
        result = response.json()

        if "id" not in result:
            error = result.get("error", {})
            raise Exception(
                error.get("message", "Failed to create Instagram container")
            )

        container_id = result["id"]

        # Step 2: Publish container
        publish_url = (
            f"https://graph.facebook.com/v18.0/{instagram_account_id}/media_publish"
        )
        publish_data = {
            "creation_id": container_id,
            "access_token": access_token,
        }

        response = requests.post(publish_url, data=publish_data)
        result = response.json()

        if "id" in result:
            return result["id"]
        elif "error" in result:
            raise Exception(
                result["error"].get("message", "Failed to publish Instagram post")
            )
        else:
            raise Exception("Failed to publish to Instagram")
