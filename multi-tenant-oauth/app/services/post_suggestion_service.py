"""Post Suggestion Service - Context-aware social media post recommendations."""

from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
from openai import OpenAI
import os
import json

from app.models import RestaurantProfile, MenuItem, SalesData, Tenant, BrandAsset
from app.services.image_service import ImageService
import requests

logger = logging.getLogger(__name__)


class PostSuggestionService:
    """Generate intelligent post suggestions based on restaurant context."""

    def __init__(self):
        """Initialize post suggestion service."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None
        self.image_service = ImageService()
        # Store OpenAI request/response data for logging
        self.openai_calls = []

    # Text length presets
    TEXT_LENGTH_PRESETS = {
        'short': {
            'description': '1-2 sentences',
            'max_chars': 150,
            'max_tokens': 80,
            'sentences': '1-2'
        },
        'medium': {
            'description': '2-3 sentences',
            'max_chars': 280,
            'max_tokens': 150,
            'sentences': '2-3'
        },
        'long': {
            'description': '3-5 sentences',
            'max_chars': 500,
            'max_tokens': 250,
            'sentences': '3-5'
        },
        'extra_long': {
            'description': '5-8 sentences',
            'max_chars': 800,
            'max_tokens': 400,
            'sentences': '5-8'
        }
    }

    async def generate_suggestions(
        self,
        db: Session,
        tenant_id: str,
        count: int = 5,
        text_length: str = 'extra_long',
        return_metadata: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate intelligent post suggestions based on restaurant context.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            count: Number of suggestions to generate
            text_length: Text length preset ('short', 'medium', 'long', 'extra_long')

        Returns:
            Dict with post suggestions
        """
        try:
            # Get restaurant data
            profile = db.query(RestaurantProfile).filter(
                RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
            ).first()

            if not profile:
                return {
                    "success": False,
                    "error": "Restaurant profile not found. Please complete setup first."
                }

            # Get menu items
            menu_items = db.query(MenuItem).filter(
                MenuItem.tenant_id == uuid.UUID(tenant_id)
            ).order_by(MenuItem.popularity_rank.nullslast()).all()

            if not menu_items:
                return {
                    "success": False,
                    "error": "No menu items found. Please import menu first."
                }

            # Generate suggestions
            suggestions = await self._generate_context_aware_suggestions(
                profile, menu_items, count, text_length
            )

            logger.info(f"Generated {len(suggestions)} post suggestions for tenant {tenant_id} with {text_length} length")

            return {
                "success": True,
                "suggestions": suggestions,
                "text_length": text_length,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating post suggestions: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _generate_context_aware_suggestions(
        self,
        profile: RestaurantProfile,
        menu_items: List[MenuItem],
        count: int,
        text_length: str = 'extra_long',
    ) -> List[Dict[str, Any]]:
        """
        Generate context-aware post suggestions.

        Args:
            profile: Restaurant profile with AI analysis
            menu_items: List of menu items
            count: Number of suggestions to generate
            text_length: Text length preset

        Returns:
            List of post suggestions
        """
        suggestions = []

        # Get context from AI analysis
        brand_analysis = profile.brand_analysis or {}
        sales_insights = profile.sales_insights or {}
        content_strategy = profile.content_strategy or {}

        # Extract key information
        brand_voice = brand_analysis.get('brand_personality', {}).get('voice_tone', 'friendly')
        restaurant_name = profile.name or 'Our Restaurant'

        sales_patterns = sales_insights.get('sales_patterns', {})
        slowest_days = sales_patterns.get('slowest_days', [])
        busiest_days = sales_patterns.get('busiest_days', [])

        promo_recommendations = sales_insights.get('promotional_recommendations', [])
        top_sellers = sales_insights.get('item_performance', {}).get('top_sellers', [])

        # Build comprehensive context to pass to all post creation methods
        context = {
            'location': profile.location,
            'cuisine_type': profile.cuisine_type,
            'menu_items': menu_items,
            'top_sellers': top_sellers,
            'slowest_days': slowest_days,
            'busiest_days': busiest_days,
        }

        # Strategy 1: Slow Day Promotion
        if slowest_days and promo_recommendations:
            for promo in promo_recommendations[:1]:  # Take first promotion
                suggestion = await self._create_promotional_post(
                    restaurant_name=restaurant_name,
                    brand_voice=brand_voice,
                    promo=promo,
                    menu_items=menu_items,
                    context=context,
                    text_length=text_length
                )
                if suggestion:
                    suggestions.append(suggestion)

        # Strategy 2: Feature Top Sellers
        if top_sellers:
            for i, top_seller in enumerate(top_sellers[:2]):  # Top 2 sellers
                # Find matching menu item
                matching_item = next(
                    (item for item in menu_items if item.name == top_seller.get('name')),
                    None
                )

                suggestion = await self._create_product_showcase_post(
                    restaurant_name=restaurant_name,
                    brand_voice=brand_voice,
                    item=matching_item or {'name': top_seller.get('name')},
                    is_bestseller=True,
                    rank=i + 1,
                    context=context,
                    text_length=text_length
                )
                if suggestion:
                    suggestions.append(suggestion)

        # Strategy 3: Weekend Traffic Driver
        if busiest_days:
            # Post on Friday to drive weekend traffic
            suggestion = await self._create_weekend_driver_post(
                restaurant_name=restaurant_name,
                brand_voice=brand_voice,
                busiest_day=busiest_days[0],
                menu_items=menu_items[:3],
                context=context,
                text_length=text_length
            )
            if suggestion:
                suggestions.append(suggestion)

        # Strategy 4: Behind the Scenes / Engagement
        suggestion = await self._create_engagement_post(
            restaurant_name=restaurant_name,
            brand_voice=brand_voice,
            profile=profile,
            text_length=text_length
        )
        if suggestion:
            suggestions.append(suggestion)

        # Strategy 5: Customer Appreciation
        suggestion = await self._create_customer_appreciation_post(
            restaurant_name=restaurant_name,
            brand_voice=brand_voice,
            text_length=text_length
        )
        if suggestion:
            suggestions.append(suggestion)

        # Return requested number of suggestions
        return suggestions[:count]

    async def _create_promotional_post(
        self,
        restaurant_name: str,
        brand_voice: str,
        promo: Dict[str, Any],
        menu_items: List[MenuItem],
        context: Optional[Dict[str, Any]] = None,
        text_length: str = 'extra_long',
    ) -> Optional[Dict[str, Any]]:
        """Create a promotional post suggestion."""
        target_day = promo.get('target_day', 'Monday')
        discount = promo.get('suggested_discount', '15% off')
        strategy = promo.get('strategy', 'Special Offer')

        # Use GPT-4 or template
        if self.openai_api_key:
            post_text, generation_source = await self._generate_post_with_ai(
                post_type='promotional',
                context={
                    'restaurant_name': restaurant_name,
                    'brand_voice': brand_voice,
                    'target_day': target_day,
                    'discount': discount,
                    'strategy': strategy,
                    'location': context.get('location') if context else None,
                    'cuisine_type': context.get('cuisine_type') if context else None,
                    'menu_items': context.get('menu_items') if context else None,
                    'top_sellers': context.get('top_sellers') if context else None,
                    'slowest_days': context.get('slowest_days') if context else None,
                    'busiest_days': context.get('busiest_days') if context else None,
                },
                text_length=text_length
            )
        else:
            post_text = self._template_promotional_post(
                restaurant_name, target_day, discount
            )
            generation_source = "template"

        return {
            "type": "promotional",
            "title": f"{strategy} - {target_day} Special",
            "post_text": post_text,
            "target_day": target_day,
            "featured_items": [],
            "recommended_time": "12:00 PM",  # Lunch time
            "reason": promo.get('reason', f'Boost sales on slower {target_day}'),
            "hashtags": ["#FoodDeals", f"#{target_day}Special", "#LocalEats"],
            "call_to_action": "Order now and save!",
            "generated_by": generation_source,
        }

    async def _create_product_showcase_post(
        self,
        restaurant_name: str,
        brand_voice: str,
        item: Any,
        is_bestseller: bool = False,
        rank: int = 1,
        context: Optional[Dict[str, Any]] = None,
        text_length: str = 'extra_long',
    ) -> Optional[Dict[str, Any]]:
        """Create a product showcase post."""
        item_name = item.name if hasattr(item, 'name') else item.get('name', 'Special Item')
        item_description = item.description if hasattr(item, 'description') else item.get('description', '')

        # Use GPT-4 or template
        if self.openai_api_key:
            post_text, generation_source = await self._generate_post_with_ai(
                post_type='product_showcase',
                context={
                    'restaurant_name': restaurant_name,
                    'brand_voice': brand_voice,
                    'item_name': item_name,
                    'description': item_description,
                    'is_bestseller': is_bestseller,
                    'rank': rank,
                    'location': context.get('location') if context else None,
                    'cuisine_type': context.get('cuisine_type') if context else None,
                    'menu_items': context.get('menu_items') if context else None,
                    'top_sellers': context.get('top_sellers') if context else None,
                    'slowest_days': context.get('slowest_days') if context else None,
                    'busiest_days': context.get('busiest_days') if context else None,
                },

                text_length=text_length
            )
        else:
            post_text = self._template_product_showcase_post(
                restaurant_name, item_name, is_bestseller, rank
            )
            generation_source = "template"

        return {
            "type": "product_showcase",
            "title": f"Feature: {item_name}",
            "post_text": post_text,
            "target_day": "Tuesday",  # Good engagement day
            "featured_items": [item_name],
            "recommended_time": "6:00 PM",  # Dinner time
            "reason": f"#{rank} Bestseller - Customer favorite!" if is_bestseller else "Feature popular item",
            "hashtags": ["#Foodie", "#FoodLovers", f"#{item_name.replace(' ', '')}"],
            "call_to_action": "Try it today!",
            "generated_by": generation_source,
        }

    async def _create_weekend_driver_post(
        self,
        restaurant_name: str,
        brand_voice: str,
        busiest_day: str,
        menu_items: List[Any],
        context: Optional[Dict[str, Any]] = None,
        text_length: str = 'extra_long',
    ) -> Optional[Dict[str, Any]]:
        """Create a weekend traffic driver post."""
        featured_items = [item.name for item in menu_items[:3]]

        # Use GPT-4 or template
        if self.openai_api_key:
            post_text, generation_source = await self._generate_post_with_ai(
                post_type='weekend_driver',
                context={
                    'restaurant_name': restaurant_name,
                    'brand_voice': brand_voice,
                    'busiest_day': busiest_day,
                    'featured_items': featured_items,
                    'location': context.get('location') if context else None,
                    'cuisine_type': context.get('cuisine_type') if context else None,
                    'menu_items': context.get('menu_items') if context else None,
                    'top_sellers': context.get('top_sellers') if context else None,
                    'slowest_days': context.get('slowest_days') if context else None,
                    'busiest_days': context.get('busiest_days') if context else None,
                },

                text_length=text_length
            )
        else:
            post_text = self._template_weekend_driver_post(
                restaurant_name, busiest_day, featured_items
            )
            generation_source = "template"

        return {
            "type": "weekend_traffic",
            "title": f"Weekend at {restaurant_name}",
            "post_text": post_text,
            "target_day": "Friday",  # Post Friday for weekend
            "featured_items": featured_items,
            "recommended_time": "5:00 PM",  # After work
            "reason": f"Drive {busiest_day} traffic - your busiest day!",
            "hashtags": ["#WeekendVibes", "#WeekendEats", "#FoodieWeekend"],
            "call_to_action": "See you this weekend!",
            "generated_by": generation_source,
        }

    async def _create_engagement_post(
        self,
        restaurant_name: str,
        brand_voice: str,
        profile: RestaurantProfile,
        text_length: str = 'extra_long',
    ) -> Optional[Dict[str, Any]]:
        """Create an engagement/poll post."""
        cuisine = profile.cuisine_type or "food"

        post_text = f"🤔 Question for our {cuisine} lovers!\n\n"
        post_text += f"What's your go-to order at {restaurant_name}?\n\n"
        post_text += "A) Our signature dishes\n"
        post_text += "B) Try something new each time\n"
        post_text += "C) The same favorite every time\n\n"
        post_text += "Comment below! 👇"

        return {
            "type": "engagement",
            "title": "Customer Engagement Poll",
            "post_text": post_text,
            "target_day": "Wednesday",  # Mid-week engagement
            "featured_items": [],
            "recommended_time": "12:00 PM",
            "reason": "Boost engagement and learn customer preferences",
            "hashtags": ["#FoodiePoll", "#CustomerLove", f"#{cuisine}Lovers"],
            "call_to_action": "Tell us in the comments!",
            "generated_by": "template",
        }

    async def _create_customer_appreciation_post(
        self,
        restaurant_name: str,
        brand_voice: str,
        text_length: str = 'extra_long',
    ) -> Optional[Dict[str, Any]]:
        """Create a customer appreciation post."""
        post_text = f"💙 To our amazing customers,\n\n"
        post_text += f"Thank you for making {restaurant_name} part of your day! "
        post_text += "Your support means everything to our team.\n\n"
        post_text += "We're grateful for each and every one of you. "
        post_text += "Here's to many more delicious moments together! 🍕✨"

        return {
            "type": "customer_appreciation",
            "title": "Thank You Customers",
            "post_text": post_text,
            "target_day": "Thursday",
            "featured_items": [],
            "recommended_time": "3:00 PM",
            "reason": "Build customer loyalty and community",
            "hashtags": ["#ThankYou", "#CustomerAppreciation", "#LocalLove"],
            "call_to_action": "We appreciate you!",
            "generated_by": "template",
        }

    async def _generate_post_with_ai(
        self,
        post_type: str,
        context: Dict[str, Any],
        text_length: str = 'extra_long',
        return_metadata: bool = False,
    ):
        """
        Generate post text using GPT-4 with rich context.

        Args:
            post_type: Type of post to generate
            context: Context dictionary with restaurant info
            text_length: Text length preset ('short', 'medium', 'long', 'extra_long')
            return_metadata: If True, return dict with full request/response data

        Returns:
            If return_metadata=False: Tuple of (post_text, generation_source)
            If return_metadata=True: Dict with post_text, request_data, response_data
        """
        try:
            # Get text length preset
            length_preset = self.TEXT_LENGTH_PRESETS.get(text_length, self.TEXT_LENGTH_PRESETS['extra_long'])

            # Build comprehensive context for better AI generation
            rich_context = self._build_rich_context(context)

            prompt = f"""You are a social media manager for a restaurant. Create an engaging {post_type} social media post.

RESTAURANT PROFILE:
Name: {rich_context['restaurant_name']}
Location: {rich_context.get('location', 'N/A')}
Cuisine: {rich_context.get('cuisine_type', 'N/A')}
Brand Voice: {rich_context['brand_voice']}

MENU HIGHLIGHTS:
{rich_context.get('menu_context', 'N/A')}

SALES INSIGHTS:
{rich_context.get('sales_context', 'N/A')}

POST CONTEXT:
{rich_context.get('post_context', 'N/A')}

TARGET AUDIENCE: {rich_context.get('target_audience', 'Local food lovers')}

Write a compelling social media post ({length_preset['sentences']} sentences, max {length_preset['max_chars']} characters).
- Be engaging and authentic
- Use the specified brand voice
- Include relevant emojis
- Reference specific menu items when appropriate
- Do NOT include hashtags in the post text
- Keep it concise and impactful
"""

            # Prepare request data
            system_message = "You are an expert social media manager specializing in restaurant marketing. You create engaging, authentic posts that drive customer engagement and sales."

            request_params = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "max_tokens": length_preset['max_tokens'],
            }

            # Call OpenAI API
            from datetime import datetime
            start_time = datetime.now()
            response = self.client.chat.completions.create(**request_params)
            end_time = datetime.now()

            post_text = response.choices[0].message.content.strip()

            # Always capture request/response data for logging
            request_data = {
                "model": request_params["model"],
                "temperature": request_params["temperature"],
                "max_tokens": request_params["max_tokens"],
                "system_message": system_message,
                "user_prompt": prompt,
                "post_type": post_type,
                "text_length": text_length,
            }

            response_data = {
                "post_text": post_text,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "response_time_ms": int((end_time - start_time).total_seconds() * 1000),
            }

            # Calculate cost (GPT-4 pricing)
            prompt_cost = response.usage.prompt_tokens * 0.00003  # $0.03 per 1K tokens
            completion_cost = response.usage.completion_tokens * 0.00006  # $0.06 per 1K tokens
            total_cost = prompt_cost + completion_cost
            response_data["estimated_cost_usd"] = round(total_cost, 6)

            # Store in instance variable for retrieval by calendar service
            self.openai_calls.append({
                "request": request_data,
                "response": response_data,
            })

            # If metadata is requested, return complete data
            if return_metadata:
                return {
                    "post_text": post_text,
                    "generation_source": "openai",
                    "request_data": request_data,
                    "response_data": response_data,
                }

            return post_text, "openai"

        except Exception as e:
            logger.error(f"Error generating post with AI: {e}")
            return self._template_generic_post(context.get('restaurant_name', 'Our Restaurant')), "template"

    def _build_rich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive context for AI generation."""
        rich = {
            'restaurant_name': context.get('restaurant_name', 'Our Restaurant'),
            'brand_voice': context.get('brand_voice', 'friendly and welcoming'),
            'location': context.get('location', ''),
            'cuisine_type': context.get('cuisine_type', ''),
            'target_audience': context.get('target_audience', 'Local food lovers'),
        }

        # Add menu context
        menu_items = context.get('menu_items', [])
        if menu_items:
            menu_text = []
            for item in menu_items[:5]:  # Top 5 items
                if hasattr(item, 'name'):
                    desc = f"  - {item.name}"
                    if hasattr(item, 'category') and item.category:
                        desc += f" ({item.category})"
                    if hasattr(item, 'description') and item.description:
                        desc += f": {item.description[:50]}"
                    if hasattr(item, 'price') and item.price:
                        desc += f" - ${item.price}"
                    menu_text.append(desc)
            rich['menu_context'] = "\n".join(menu_text) if menu_text else "Various delicious items"

        # Add sales context
        sales_context = []
        if context.get('slowest_days'):
            sales_context.append(f"Slowest days: {', '.join(context['slowest_days'])}")
        if context.get('busiest_days'):
            sales_context.append(f"Busiest days: {', '.join(context['busiest_days'])}")
        if context.get('top_sellers'):
            top = context['top_sellers'][:3]
            sales_context.append(f"Top sellers: {', '.join([s.get('name', '') for s in top if s.get('name')])}")
        rich['sales_context'] = "\n".join(sales_context) if sales_context else "N/A"

        # Add post-specific context
        post_context = []
        if context.get('featured_items'):
            post_context.append(f"Featured items: {', '.join(context['featured_items'])}")
        if context.get('target_day'):
            post_context.append(f"Target day: {context['target_day']}")
        if context.get('special_context'):
            post_context.append(context['special_context'])
        rich['post_context'] = "\n".join(post_context) if post_context else "General promotional post"

        return rich

    def _template_promotional_post(self, restaurant_name: str, day: str, discount: str) -> str:
        """Template for promotional post."""
        return f"🎉 {day} Special at {restaurant_name}!\n\n" \
               f"Beat the mid-week blues with {discount} on your order! " \
               f"Perfect time to try that dish you've been eyeing. 😋\n\n" \
               f"Valid all day {day}!"

    def _template_product_showcase_post(
        self, restaurant_name: str, item_name: str, is_bestseller: bool, rank: int
    ) -> str:
        """Template for product showcase post."""
        if is_bestseller:
            return f"⭐ Customer Favorite Alert!\n\n" \
                   f"Our #{rank} bestseller: {item_name}! " \
                   f"There's a reason everyone loves it. 😍\n\n" \
                   f"Have you tried it yet?"
        else:
            return f"✨ Spotlight on: {item_name}\n\n" \
                   f"One of our signature dishes that keeps customers coming back! " \
                   f"Fresh, delicious, and made with love. ❤️"

    def _template_weekend_driver_post(
        self, restaurant_name: str, day: str, items: List[str]
    ) -> str:
        """Template for weekend driver post."""
        items_text = ", ".join(items[:2])
        return f"🎊 Weekend Plans = {restaurant_name}!\n\n" \
               f"Join us this {day} for {items_text}, and more! " \
               f"Perfect way to kick off the weekend. 🍽️\n\n" \
               f"We'll save you a seat!"

    def _template_generic_post(self, restaurant_name: str) -> str:
        """Generic template post."""
        return f"Come visit us at {restaurant_name} today! Fresh food, great atmosphere, amazing taste. 😊"

    async def _get_post_image(
        self,
        db: Session,
        tenant_id: str,
        post_type: str,
        featured_items: List[str],
        post_text: str,
        profile: RestaurantProfile,
    ) -> Optional[tuple[Optional[uuid.UUID], Optional[str]]]:
        """
        Get image for post using hybrid approach: assets first, then AI generation.

        Returns:
            Tuple of (asset_id, image_url) or (None, None) if images disabled
        """
        try:
            # Check if images are enabled
            content_strategy = profile.content_strategy or {}
            if not content_strategy.get('include_images', False):
                return None, None

            image_strategy = content_strategy.get('image_strategy', 'assets_first')

            # Try to find existing asset
            if image_strategy in ['assets_first', 'assets_only']:
                asset_id, image_url = await self._select_existing_image(
                    db, tenant_id, post_type, featured_items
                )
                if asset_id or image_url:
                    logger.info(f"Using existing asset for post: {asset_id or image_url}")
                    return asset_id, image_url

            # Generate AI image if assets_only is not set
            if image_strategy != 'assets_only' and self.client:
                image_url = await self._generate_ai_image(
                    db, tenant_id, post_type, post_text, profile
                )
                if image_url:
                    logger.info(f"Generated AI image for post: {image_url}")
                    return None, image_url

            logger.info(f"No image found/generated for post type: {post_type}")
            return None, None

        except Exception as e:
            logger.error(f"Error getting post image: {e}")
            return None, None

    async def _select_existing_image(
        self,
        db: Session,
        tenant_id: str,
        post_type: str,
        featured_items: List[str],
    ) -> tuple[Optional[uuid.UUID], Optional[str]]:
        """
        Select an existing image from brand assets or menu items.

        Returns:
            Tuple of (asset_id, image_url)
        """
        try:
            # First, try to find menu item images for featured items
            if featured_items:
                for item_name in featured_items:
                    menu_item = db.query(MenuItem).filter(
                        MenuItem.tenant_id == uuid.UUID(tenant_id),
                        MenuItem.name == item_name,
                        MenuItem.image_url.isnot(None)
                    ).first()

                    if menu_item and menu_item.image_url:
                        logger.info(f"Found menu item image for {item_name}")
                        return menu_item.asset_id, menu_item.image_url

            # Try to find brand assets with relevant tags
            tag_queries = []
            if post_type:
                tag_queries.append(post_type)
            if featured_items:
                tag_queries.extend(featured_items)

            if tag_queries:
                # Search for assets with matching tags
                asset = db.query(BrandAsset).filter(
                    BrandAsset.tenant_id == uuid.UUID(tenant_id),
                    BrandAsset.tags.contains(tag_queries)
                ).order_by(
                    BrandAsset.last_used_at.nulls_last()
                ).first()

                if asset:
                    logger.info(f"Found brand asset with tags: {asset.id}")
                    return asset.id, asset.file_url

            # Fallback: get a random general brand asset
            general_asset = db.query(BrandAsset).filter(
                BrandAsset.tenant_id == uuid.UUID(tenant_id)
            ).order_by(
                BrandAsset.last_used_at.nulls_last()
            ).first()

            if general_asset:
                logger.info(f"Using general brand asset: {general_asset.id}")
                return general_asset.id, general_asset.file_url

            return None, None

        except Exception as e:
            logger.error(f"Error selecting existing image: {e}")
            return None, None

    async def _generate_ai_image(
        self,
        db: Session,
        tenant_id: str,
        post_type: str,
        post_text: str,
        profile: RestaurantProfile,
    ) -> Optional[str]:
        """
        Generate an AI image using DALL-E 3.

        Returns:
            Image URL or None
        """
        try:
            if not self.client:
                return None

            # Get AI image style from content strategy
            content_strategy = profile.content_strategy or {}
            ai_style = content_strategy.get('ai_image_style', 'food photography, professional, appetizing')

            # Build DALL-E prompt
            prompt = f"""Create a professional {post_type} image for a restaurant social media post.
Restaurant: {profile.name}
Cuisine: {profile.cuisine_type or 'casual dining'}
Post: {post_text[:200]}
Style: {ai_style}
Requirements: High quality, appetizing, Instagram-ready, {profile.cuisine_type or 'food'} focused"""

            logger.info(f"Generating DALL-E image with prompt: {prompt[:100]}...")

            # Generate image with DALL-E 3
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url

            # Download and save the image
            image_response = requests.get(image_url)
            if image_response.status_code == 200:
                # Save image using image service
                file_path, public_url = await self.image_service.save_image_bytes(
                    image_response.content,
                    f"ai_generated_{uuid.uuid4()}.png",
                    tenant_id
                )

                # Optionally save as brand asset for future use
                asset = BrandAsset(
                    id=uuid.uuid4(),
                    tenant_id=uuid.UUID(tenant_id),
                    filename=f"ai_generated_{uuid.uuid4()}.png",
                    file_path=file_path,
                    file_url=public_url,
                    file_size=len(image_response.content),
                    mime_type="image/png",
                    title=f"AI Generated - {post_type}",
                    description=post_text[:200],
                    tags=[post_type, "ai_generated"],
                    times_used=0,
                )
                db.add(asset)
                db.flush()

                logger.info(f"Successfully generated and saved AI image: {public_url}")
                return public_url

            return None

        except Exception as e:
            logger.error(f"Error generating AI image: {e}")
            return None
