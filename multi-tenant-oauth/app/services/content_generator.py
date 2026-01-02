"""AI-powered content generation service for social media posts."""

import os
from typing import List, Dict, Optional
from datetime import datetime
import openai
from openai import OpenAI


class ContentGenerator:
    """Generate engaging social media content using AI."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize content generator.

        Args:
            api_key: OpenAI API key (or uses OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.text_model = os.getenv("GPT_TEXT_MODEL", "gpt-4")  # Read from env, default to gpt-4

        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None


    # Text length presets (same as PostSuggestionService)
    TEXT_LENGTH_PRESETS = {
        'short': {'description': '1-2 sentences', 'max_chars': 150, 'max_tokens': 80, 'sentences': '1-2'},
        'medium': {'description': '2-3 sentences', 'max_chars': 280, 'max_tokens': 150, 'sentences': '2-3'},
        'long': {'description': '3-5 sentences', 'max_chars': 500, 'max_tokens': 250, 'sentences': '3-5'},
        'extra_long': {'description': '5-8 sentences', 'max_chars': 800, 'max_tokens': 400, 'sentences': '5-8'}
    }

    def generate_post_caption(
        self,
        restaurant_name: str,
        restaurant_description: str,
        post_type: str = "daily_special",
        item_name: Optional[str] = None,
        item_description: Optional[str] = None,
        tone: str = "friendly",
        platform: str = "facebook",
        recent_captions: Optional[List[str]] = None,
        max_length: int = 2200,
        text_length: str = "extra_long",
        return_metadata: bool = False,
    ):
        """
        Generate a social media post caption using AI.

        Args:
            restaurant_name: Name of the restaurant
            restaurant_description: Brief description of the restaurant
            post_type: Type of post (daily_special, promotion, event, announcement, holiday)
            item_name: Optional item name (e.g., "Margherita Pizza")
            item_description: Optional item description
            tone: Tone of the post (friendly, professional, casual, exciting)
            platform: Platform (facebook/instagram)
            recent_captions: Recent post captions to avoid similarity
            max_length: Maximum caption length

        Returns:
            Generated caption string
        """
        if not self.client:
            # Fallback to template-based generation if no API key
            return self._generate_template_caption(
                restaurant_name=restaurant_name,
                post_type=post_type,
                item_name=item_name,
                item_description=item_description,
            )

        # Build prompt
        prompt = self._build_generation_prompt(
            restaurant_name=restaurant_name,
            restaurant_description=restaurant_description,
            post_type=post_type,
            item_name=item_name,
            item_description=item_description,
            tone=tone,
            text_length=text_length,
            platform=platform,
            recent_captions=recent_captions,
            max_length=max_length,
        )

        # Prepare request data
        system_message = "You are a creative social media manager specialized in restaurant marketing. You create engaging, authentic posts that drive customer engagement and sales."

        request_params = {
            "model": self.text_model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 500,
        }

        try:
            # Call OpenAI API
            start_time = datetime.now()
            response = self.client.chat.completions.create(**request_params)
            end_time = datetime.now()

            caption = response.choices[0].message.content.strip()

            # If metadata is requested, return complete data
            if return_metadata:
                request_data = {
                    "model": request_params["model"],
                    "temperature": request_params["temperature"],
                    "max_tokens": request_params["max_tokens"],
                    "system_message": system_message,
                    "user_prompt": prompt,
                }

                response_data = {
                    "caption": caption,
                    "model": response.model,
                    "finish_reason": response.choices[0].finish_reason,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                    "response_time_ms": int((end_time - start_time).total_seconds() * 1000),
                }

                # Calculate cost (GPT-4 pricing as of 2024)
                prompt_cost = response.usage.prompt_tokens * 0.00003  # $0.03 per 1K tokens
                completion_cost = response.usage.completion_tokens * 0.00006  # $0.06 per 1K tokens
                total_cost = prompt_cost + completion_cost
                response_data["estimated_cost_usd"] = round(total_cost, 6)

                return {
                    "caption": caption,
                    "request_data": request_data,
                    "response_data": response_data,
                }

            return caption

        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"❌ OpenAI API Error: {type(e).__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            print(f"❌ OpenAI API Error: {type(e).__name__}: {e}")
            # Fallback to template
            logger.info("⚠️  Falling back to template-based caption generation")
            return self._generate_template_caption(
                restaurant_name=restaurant_name,
                post_type=post_type,
                item_name=item_name,
                item_description=item_description,
            )

    def _build_generation_prompt(
        self,
        restaurant_name: str,
        restaurant_description: str,
        post_type: str,
        item_name: Optional[str],
        item_description: Optional[str],
        tone: str,
        platform: str,
        recent_captions: Optional[List[str]],
        max_length: int,
        text_length: str = "extra_long",
    ) -> str:
        length_preset = self.TEXT_LENGTH_PRESETS.get(text_length, self.TEXT_LENGTH_PRESETS["extra_long"])
        """Build the AI prompt for caption generation."""

        prompt = f"""Create an engaging {platform} post for {restaurant_name}.

Restaurant: {restaurant_name}
Description: {restaurant_description}
Post Type: {post_type}
Tone: {tone}
"""

        if item_name:
            prompt += f"\nFeatured Item: {item_name}"
        if item_description:
            prompt += f"\nItem Description: {item_description}"

        prompt += f"""

Requirements:
- Maximum {max_length} characters
- Include relevant emojis (but don't overdo it)
- Include 3-5 relevant hashtags at the end
- Make it engaging and authentic
- Include a call-to-action (order now, visit us, etc.)
- Highlight what makes this restaurant/item special
"""

        if recent_captions:
            prompt += f"\n- Make it DIFFERENT from these recent posts (don't repeat themes or phrases):\n"
            for i, caption in enumerate(recent_captions[:5], 1):
                prompt += f"  {i}. {caption[:100]}...\n"

        platform_specific = {
            "facebook": "- Optimize for Facebook (can be longer, conversational)",
            "instagram": "- Optimize for Instagram (visual, concise, hashtag-friendly)",
        }
        prompt += f"\n{platform_specific.get(platform, '')}"

        prompt += "\n\nGenerate only the caption text, no explanations or meta-commentary."

        return prompt

    def _generate_template_caption(
        self,
        restaurant_name: str,
        post_type: str,
        item_name: Optional[str],
        item_description: Optional[str],
    ) -> str:
        """Fallback template-based caption generation."""

        # Default values for templates
        default_item = "Our chef's creation"
        default_special = "Today's special"

        # Hashtag for restaurant
        hashtag = restaurant_name.replace(' ', '')

        templates = {
            "daily_special": [
                f"🍽️ Today's Special at {restaurant_name}!\n\n{item_name or default_item} - {item_description or 'Freshly prepared with love!'}\n\nOrder now for pickup or delivery!\n\n#DailySpecial #{hashtag} #FoodLovers",
                f"✨ Don't miss out! {item_name or default_special} is ready at {restaurant_name}!\n\n{item_description or 'Made with the finest ingredients.'}\n\nVisit us today!\n\n#FoodOfTheDay #{hashtag} #Delicious",
            ],
            "promotion": [
                f"🎉 Special Offer at {restaurant_name}!\n\n{item_description or 'Limited time only!'}\n\nOrder now and enjoy!\n\n#SpecialOffer #{hashtag} #FoodDeals",
            ],
            "event": [
                f"📅 Join us at {restaurant_name}!\n\n{item_description or 'Special event coming up!'}\n\nDon't miss out!\n\n#Event #{hashtag} #Community",
            ],
            "announcement": [
                f"📢 News from {restaurant_name}!\n\n{item_description or 'Exciting updates!'}\n\nStay tuned!\n\n#Announcement #{hashtag}",
            ],
            "holiday": [
                f"🎊 Happy Holidays from {restaurant_name}!\n\n{item_description or 'Celebrate with us!'}\n\n#Holidays #{hashtag} #Celebration",
            ],
        }

        template_list = templates.get(post_type, templates["daily_special"])
        import random
        return random.choice(template_list)

    def check_similarity(self, new_caption: str, recent_captions: List[str]) -> float:
        """
        Check similarity between new caption and recent posts.

        Args:
            new_caption: New caption to check
            recent_captions: List of recent captions

        Returns:
            Similarity score (0-1, higher means more similar)
        """
        if not recent_captions:
            return 0.0

        # Simple word-based similarity check
        new_words = set(new_caption.lower().split())

        max_similarity = 0.0
        for recent in recent_captions:
            recent_words = set(recent.lower().split())

            if not recent_words:
                continue

            # Jaccard similarity
            intersection = new_words.intersection(recent_words)
            union = new_words.union(recent_words)

            if union:
                similarity = len(intersection) / len(union)
                max_similarity = max(max_similarity, similarity)

        return max_similarity

    def generate_post_variations(
        self,
        restaurant_name: str,
        restaurant_description: str,
        post_type: str,
        item_name: Optional[str] = None,
        item_description: Optional[str] = None,
        platform: str = "facebook",
        num_variations: int = 3,
        text_length: str = "extra_long",
    ) -> List[str]:
        """
        Generate multiple variations of a post.

        Args:
            restaurant_name: Name of the restaurant
            restaurant_description: Restaurant description
            post_type: Type of post
            item_name: Optional item name
            item_description: Optional item description
            platform: Platform name
            num_variations: Number of variations to generate

        Returns:
            List of caption variations
        """
        variations = []

        for i in range(num_variations):
            # Vary the tone for each variation
            tones = ["friendly", "professional", "casual", "exciting"]
            tone = tones[i % len(tones)]

            caption = self.generate_post_caption(
                restaurant_name=restaurant_name,
                restaurant_description=restaurant_description,
                post_type=post_type,
                item_name=item_name,
                item_description=item_description,
                tone=tone,
                platform=platform,
            )

            variations.append(caption)

        return variations

    def suggest_images_for_post(
        self,
        db,
        tenant_id: str,
        post_type: str,
        item_name: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict]:
        """
        Suggest relevant images from the asset library based on post type.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            post_type: Type of post (daily_special, promotion, event, etc.)
            item_name: Optional item name for searching
            limit: Maximum number of suggestions

        Returns:
            List of suggested assets with metadata
        """
        from app.services import AssetService

        asset_service = AssetService()

        # Map post types to folder names
        post_type_folder_map = {
            "daily_special": "Dishes",
            "promotion": "Dishes",
            "event": "Events",
            "announcement": "Brand Assets",
            "holiday": "Events",
        }

        # Get folder name for this post type
        folder_name = post_type_folder_map.get(post_type, "Dishes")

        # Get assets from the appropriate folder
        folder_assets = asset_service.get_assets_by_folder(
            db=db, tenant_id=tenant_id, folder_name=folder_name
        )

        # If we have an item name, also search by that
        if item_name and len(folder_assets) < limit:
            search_assets = asset_service.search_assets(
                db=db, tenant_id=tenant_id, query=item_name, limit=limit
            )
            # Merge, avoiding duplicates
            asset_ids = {str(a.id) for a in folder_assets}
            for asset in search_assets:
                if str(asset.id) not in asset_ids and len(folder_assets) < limit:
                    folder_assets.append(asset)
                    asset_ids.add(str(asset.id))

        # If still not enough, get recently used assets
        if len(folder_assets) < limit:
            recent_assets = asset_service.get_recently_used(
                db=db, tenant_id=tenant_id, limit=limit
            )
            asset_ids = {str(a.id) for a in folder_assets}
            for asset in recent_assets:
                if str(asset.id) not in asset_ids and len(folder_assets) < limit:
                    folder_assets.append(asset)
                    asset_ids.add(str(asset.id))

        # Format response
        suggestions = []
        for asset in folder_assets[:limit]:
            suggestions.append(
                {
                    "id": str(asset.id),
                    "title": asset.title or asset.filename,
                    "file_url": asset.file_url,
                    "thumbnail_url": asset.file_url,
                    "width": asset.width,
                    "height": asset.height,
                    "times_used": asset.times_used,
                    "tags": asset.tags or [],
                    "reason": f"From {folder_name} folder" if asset in folder_assets[:len(folder_assets)] else "Recently used",
                }
            )

        return suggestions
