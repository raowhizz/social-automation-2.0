"""Restaurant Intelligence Service - AI-powered restaurant context analysis."""

from typing import Dict, Any, List, Optional
import uuid
import json
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
import logging
from openai import OpenAI
import os

from app.models import RestaurantProfile, MenuItem, SalesData, Tenant

logger = logging.getLogger(__name__)


class RestaurantIntelligenceService:
    """AI-powered service for analyzing restaurant data and generating insights."""

    def __init__(self):
        """Initialize restaurant intelligence service."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            self.client = None

    async def analyze_restaurant(
        self,
        db: Session,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Perform complete AI analysis of restaurant.

        Args:
            db: Database session
            tenant_id: Tenant UUID

        Returns:
            Dict with analysis results
        """
        try:
            # Get tenant info
            tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
            if not tenant:
                return {"success": False, "error": "Tenant not found"}

            # Get menu items
            menu_items = db.query(MenuItem).filter(
                MenuItem.tenant_id == uuid.UUID(tenant_id)
            ).all()

            if not menu_items:
                return {"success": False, "error": "No menu data found. Please import menu first."}

            # Get sales data
            sales_data = db.query(SalesData).filter(
                SalesData.tenant_id == uuid.UUID(tenant_id)
            ).all()

            # Get or create restaurant profile
            profile = db.query(RestaurantProfile).filter(
                RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
            ).first()

            if not profile:
                profile = RestaurantProfile(
                    tenant_id=uuid.UUID(tenant_id),
                )
                db.add(profile)

            # Run AI analysis
            logger.info(f"Starting AI analysis for tenant {tenant_id}")

            # 1. Analyze menu for brand personality
            brand_analysis = await self._analyze_brand_personality(
                tenant, menu_items
            )
            profile.brand_analysis = brand_analysis

            # 2. Analyze sales data for trends and insights
            if sales_data:
                sales_insights = await self._analyze_sales_trends(
                    menu_items, sales_data
                )
                profile.sales_insights = sales_insights
            else:
                profile.sales_insights = {
                    "message": "No sales data available yet. Upload sales data to get insights."
                }

            # 3. Generate content strategy
            content_strategy = await self._generate_content_strategy(
                brand_analysis,
                profile.sales_insights if sales_data else None,
                menu_items
            )
            profile.content_strategy = content_strategy

            profile.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Successfully completed AI analysis for tenant {tenant_id}")

            return {
                "success": True,
                "brand_analysis": brand_analysis,
                "sales_insights": profile.sales_insights,
                "content_strategy": content_strategy,
            }

        except Exception as e:
            logger.error(f"Error analyzing restaurant: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
            }

    async def _analyze_brand_personality(
        self,
        tenant: Tenant,
        menu_items: List[MenuItem],
    ) -> Dict[str, Any]:
        """
        Use GPT-4 to analyze menu and generate brand personality.

        Args:
            tenant: Tenant model
            menu_items: List of menu items

        Returns:
            Brand analysis dictionary
        """
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured, using template response")
            return self._template_brand_analysis(tenant, menu_items)

        try:
            # Prepare menu data for analysis
            menu_summary = self._prepare_menu_summary(menu_items)

            # Create GPT-4 prompt
            prompt = f"""You are a restaurant branding expert. Analyze the following restaurant menu and generate a comprehensive brand personality profile.

Restaurant Name: {tenant.name or 'Unknown'}

Menu Categories and Items:
{menu_summary}

Based on this menu, provide a detailed analysis in JSON format with the following structure:
{{
    "brand_personality": {{
        "voice_tone": "string describing the brand voice (e.g., 'casual and friendly', 'upscale and sophisticated')",
        "key_attributes": ["attribute1", "attribute2", "attribute3"],
        "target_audience": "description of ideal customer",
        "unique_selling_points": ["usp1", "usp2", "usp3"]
    }},
    "cuisine_analysis": {{
        "primary_cuisine": "main cuisine type",
        "cuisine_style": "description of style (e.g., 'traditional Italian', 'modern fusion')",
        "signature_items": ["item1", "item2", "item3"],
        "price_positioning": "budget/mid-range/premium"
    }},
    "content_themes": {{
        "recommended_themes": ["theme1", "theme2", "theme3"],
        "hashtag_suggestions": ["#tag1", "#tag2", "#tag3"],
        "content_pillars": ["pillar1", "pillar2", "pillar3"]
    }}
}}

Provide ONLY the JSON response, no additional text."""

            # Call GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a restaurant branding expert that provides analysis in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500,
            )

            # Parse response
            analysis_text = response.choices[0].message.content.strip()

            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

            brand_analysis = json.loads(analysis_text)

            # Add metadata
            brand_analysis["analyzed_at"] = datetime.utcnow().isoformat()
            brand_analysis["total_menu_items"] = len(menu_items)

            return brand_analysis

        except Exception as e:
            logger.error(f"Error in GPT-4 brand analysis: {e}")
            return self._template_brand_analysis(tenant, menu_items)

    async def _analyze_sales_trends(
        self,
        menu_items: List[MenuItem],
        sales_data: List[SalesData],
    ) -> Dict[str, Any]:
        """
        Use GPT-4 to analyze sales data and generate insights.

        Args:
            menu_items: List of menu items
            sales_data: List of sales records

        Returns:
            Sales insights dictionary
        """
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured, using template response")
            return self._template_sales_insights(menu_items, sales_data)

        try:
            # Prepare sales summary
            sales_summary = self._prepare_sales_summary(menu_items, sales_data)

            # Create GPT-4 prompt
            prompt = f"""You are a restaurant sales analyst. Analyze the following sales data and provide actionable insights for social media marketing.

Sales Summary:
{sales_summary}

Based on this data, provide insights in JSON format with the following structure:
{{
    "sales_patterns": {{
        "busiest_days": ["day1", "day2"],
        "slowest_days": ["day1", "day2"],
        "peak_hours": "description if available",
        "seasonal_trends": "description of any trends"
    }},
    "item_performance": {{
        "top_sellers": [
            {{"name": "item name", "times_ordered": number, "insight": "why it's popular"}},
            ...
        ],
        "underperforming_items": [
            {{"name": "item name", "times_ordered": number, "suggestion": "how to promote"}},
            ...
        ]
    }},
    "promotional_recommendations": [
        {{
            "strategy": "promotion type (e.g., 'Happy Hour', 'Monday Madness')",
            "target_day": "day of week",
            "reason": "why this would work",
            "suggested_discount": "percentage or offer"
        }},
        ...
    ],
    "content_opportunities": [
        {{
            "opportunity": "description",
            "best_items_to_feature": ["item1", "item2"],
            "timing": "when to post"
        }},
        ...
    ]
}}

Provide ONLY the JSON response, no additional text."""

            # Call GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a restaurant sales analyst that provides insights in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
            )

            # Parse response
            analysis_text = response.choices[0].message.content.strip()

            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

            sales_insights = json.loads(analysis_text)

            # Add metadata
            sales_insights["analyzed_at"] = datetime.utcnow().isoformat()
            sales_insights["total_orders_analyzed"] = len(sales_data)

            return sales_insights

        except Exception as e:
            logger.error(f"Error in GPT-4 sales analysis: {e}")
            return self._template_sales_insights(menu_items, sales_data)

    async def _generate_content_strategy(
        self,
        brand_analysis: Dict[str, Any],
        sales_insights: Optional[Dict[str, Any]],
        menu_items: List[MenuItem],
    ) -> Dict[str, Any]:
        """
        Generate content strategy based on brand and sales analysis.

        Args:
            brand_analysis: Brand personality analysis
            sales_insights: Sales trends analysis
            menu_items: List of menu items

        Returns:
            Content strategy dictionary
        """
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured, using template response")
            return self._template_content_strategy(brand_analysis, sales_insights, menu_items)

        try:
            # Create GPT-4 prompt
            brand_summary = json.dumps(brand_analysis, indent=2)
            sales_summary = json.dumps(sales_insights, indent=2) if sales_insights else "No sales data available"

            prompt = f"""You are a social media content strategist for restaurants. Based on the brand analysis and sales insights below, create a comprehensive content strategy.

Brand Analysis:
{brand_summary}

Sales Insights:
{sales_summary}

Create a content strategy in JSON format with the following structure:
{{
    "posting_schedule": {{
        "frequency": "posts per week",
        "best_days_to_post": ["day1", "day2"],
        "best_times": ["time1", "time2"],
        "rationale": "why this schedule works"
    }},
    "content_mix": [
        {{
            "content_type": "type (e.g., 'Product Showcase', 'Behind the Scenes', 'Customer Stories')",
            "percentage": 30,
            "description": "what to post",
            "example_topics": ["topic1", "topic2"]
        }},
        ...
    ],
    "featured_items_rotation": {{
        "weekly_rotation": ["item1", "item2", "item3", "item4"],
        "strategy": "how to rotate items for maximum engagement"
    }},
    "promotional_calendar": [
        {{
            "week": 1,
            "focus": "what to promote",
            "items": ["item1", "item2"],
            "offer_suggestion": "promotion idea"
        }},
        ...
    ],
    "engagement_tactics": [
        {{
            "tactic": "engagement method",
            "implementation": "how to do it",
            "expected_outcome": "what to expect"
        }},
        ...
    ]
}}

Provide ONLY the JSON response, no additional text."""

            # Call GPT-4
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a social media strategist that provides content strategies in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2500,
            )

            # Parse response
            analysis_text = response.choices[0].message.content.strip()

            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

            content_strategy = json.loads(analysis_text)

            # Add metadata
            content_strategy["generated_at"] = datetime.utcnow().isoformat()

            return content_strategy

        except Exception as e:
            logger.error(f"Error in GPT-4 content strategy generation: {e}")
            return self._template_content_strategy(brand_analysis, sales_insights, menu_items)

    def _prepare_menu_summary(self, menu_items: List[MenuItem]) -> str:
        """Prepare menu summary for GPT-4 analysis."""
        # Group by category
        categories = {}
        for item in menu_items:
            cat = item.category or 'Other'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                'name': item.name,
                'price': float(item.price) if item.price else 0,
                'description': item.description[:100] if item.description else '',
            })

        # Format summary
        summary_lines = []
        for category, items in sorted(categories.items()):
            summary_lines.append(f"\n{category} ({len(items)} items):")
            for item in items[:5]:  # Show max 5 items per category
                summary_lines.append(f"  - {item['name']} (${item['price']:.2f})")
                if item['description']:
                    summary_lines.append(f"    {item['description']}")
            if len(items) > 5:
                summary_lines.append(f"  ... and {len(items) - 5} more items")

        return "\n".join(summary_lines)

    def _prepare_sales_summary(
        self,
        menu_items: List[MenuItem],
        sales_data: List[SalesData]
    ) -> str:
        """Prepare sales summary for GPT-4 analysis."""
        # Calculate day of week stats
        day_stats = {}
        for sale in sales_data:
            day = sale.order_date.strftime('%A')
            if day not in day_stats:
                day_stats[day] = {'count': 0, 'revenue': 0}
            day_stats[day]['count'] += 1
            day_stats[day]['revenue'] += float(sale.total_amount)

        # Get top items
        top_items = sorted(
            [item for item in menu_items if item.times_ordered > 0],
            key=lambda x: x.times_ordered,
            reverse=True
        )[:10]

        # Format summary
        summary_lines = [
            f"Total Orders: {len(sales_data)}",
            f"Date Range: {min(s.order_date for s in sales_data).strftime('%Y-%m-%d')} to {max(s.order_date for s in sales_data).strftime('%Y-%m-%d')}",
            f"Total Revenue: ${sum(float(s.total_amount) for s in sales_data):.2f}",
            f"Average Order Value: ${sum(float(s.total_amount) for s in sales_data) / len(sales_data):.2f}",
            "\nOrders by Day of Week:",
        ]

        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day in day_stats:
                stats = day_stats[day]
                summary_lines.append(
                    f"  {day}: {stats['count']} orders, ${stats['revenue']:.2f} revenue"
                )

        summary_lines.append("\nTop 10 Most Ordered Items:")
        for i, item in enumerate(top_items, 1):
            summary_lines.append(
                f"  {i}. {item.name} - Ordered {item.times_ordered} times, ${float(item.total_revenue):.2f} revenue"
            )

        return "\n".join(summary_lines)

    def _template_brand_analysis(self, tenant: Tenant, menu_items: List[MenuItem]) -> Dict[str, Any]:
        """Template response when OpenAI API is not available."""
        categories = set(item.category for item in menu_items if item.category)
        avg_price = sum(float(item.price) for item in menu_items if item.price) / len(menu_items) if menu_items else 0

        return {
            "brand_personality": {
                "voice_tone": "friendly and approachable",
                "key_attributes": ["family-friendly", "quality-focused", "community-oriented"],
                "target_audience": "Families and local food enthusiasts",
                "unique_selling_points": ["Fresh ingredients", "Diverse menu", "Great value"]
            },
            "cuisine_analysis": {
                "primary_cuisine": list(categories)[0] if categories else "Multi-cuisine",
                "cuisine_style": "Traditional comfort food",
                "signature_items": [item.name for item in menu_items[:3]],
                "price_positioning": "mid-range" if avg_price > 15 else "budget-friendly"
            },
            "content_themes": {
                "recommended_themes": ["Food Quality", "Customer Experience", "Daily Specials"],
                "hashtag_suggestions": ["#FreshFood", "#LocalEats", "#FoodLovers"],
                "content_pillars": ["Product Showcase", "Behind the Scenes", "Customer Stories"]
            },
            "note": "Using template analysis. Configure OPENAI_API_KEY for AI-powered insights.",
            "analyzed_at": datetime.utcnow().isoformat(),
            "total_menu_items": len(menu_items)
        }

    def _template_sales_insights(
        self,
        menu_items: List[MenuItem],
        sales_data: List[SalesData]
    ) -> Dict[str, Any]:
        """Template response when OpenAI API is not available."""
        # Calculate basic stats
        day_stats = {}
        for sale in sales_data:
            day = sale.order_date.strftime('%A')
            if day not in day_stats:
                day_stats[day] = {'count': 0, 'revenue': 0}
            day_stats[day]['count'] += 1
            day_stats[day]['revenue'] += float(sale.total_amount)

        busiest_day = max(day_stats.items(), key=lambda x: x[1]['count'])[0] if day_stats else None
        slowest_day = min(day_stats.items(), key=lambda x: x[1]['count'])[0] if day_stats else None

        top_items = sorted(
            [item for item in menu_items if item.times_ordered > 0],
            key=lambda x: x.times_ordered,
            reverse=True
        )[:3]

        return {
            "sales_patterns": {
                "busiest_days": [busiest_day] if busiest_day else [],
                "slowest_days": [slowest_day] if slowest_day else [],
                "peak_hours": "Data not available",
                "seasonal_trends": "Analyze over longer period for trends"
            },
            "statistics": {
                "orders_by_day_of_week": day_stats
            },
            "item_performance": {
                "top_sellers": [
                    {
                        "name": item.name,
                        "times_ordered": item.times_ordered,
                        "insight": f"Popular {item.category or 'item'} - great for promotion"
                    }
                    for item in top_items
                ],
                "underperforming_items": []
            },
            "promotional_recommendations": [
                {
                    "strategy": f"{slowest_day} Special" if slowest_day else "Weekly Special",
                    "target_day": slowest_day or "Monday",
                    "reason": f"Boost sales on slower {slowest_day}" if slowest_day else "Drive weekday traffic",
                    "suggested_discount": "15-20% off"
                }
            ],
            "content_opportunities": [
                {
                    "opportunity": "Feature bestsellers on social media",
                    "best_items_to_feature": [item.name for item in top_items],
                    "timing": f"Post on {busiest_day} to maximize engagement" if busiest_day else "Peak hours"
                }
            ],
            "note": "Using template analysis. Configure OPENAI_API_KEY for AI-powered insights.",
            "analyzed_at": datetime.utcnow().isoformat(),
            "total_orders_analyzed": len(sales_data)
        }

    def _template_content_strategy(
        self,
        brand_analysis: Dict[str, Any],
        sales_insights: Optional[Dict[str, Any]],
        menu_items: List[MenuItem]
    ) -> Dict[str, Any]:
        """Template response when OpenAI API is not available."""
        top_items = sorted(
            [item for item in menu_items if item.times_ordered > 0],
            key=lambda x: x.times_ordered,
            reverse=True
        )[:4] if menu_items else []

        return {
            "posting_schedule": {
                "frequency": "3-5 posts per week",
                "best_days_to_post": ["Tuesday", "Thursday", "Saturday"],
                "best_times": ["12:00 PM", "6:00 PM"],
                "rationale": "Post during meal planning times for maximum engagement"
            },
            "content_mix": [
                {
                    "content_type": "Product Showcase",
                    "percentage": 40,
                    "description": "Feature menu items with appealing photos",
                    "example_topics": ["Daily specials", "Signature dishes", "New items"]
                },
                {
                    "content_type": "Promotions & Deals",
                    "percentage": 30,
                    "description": "Announce special offers and discounts",
                    "example_topics": ["Weekend specials", "Happy hour", "Combo deals"]
                },
                {
                    "content_type": "Behind the Scenes",
                    "percentage": 20,
                    "description": "Show kitchen, staff, and preparation process",
                    "example_topics": ["Chef preparing dishes", "Fresh ingredients", "Team introductions"]
                },
                {
                    "content_type": "Customer Engagement",
                    "percentage": 10,
                    "description": "User-generated content and customer stories",
                    "example_topics": ["Customer reviews", "Photo contests", "Polls and questions"]
                }
            ],
            "featured_items_rotation": {
                "weekly_rotation": [item.name for item in top_items] if top_items else ["Feature your bestsellers"],
                "strategy": "Rotate popular items weekly to maintain variety while showcasing proven favorites"
            },
            "promotional_calendar": [
                {
                    "week": 1,
                    "focus": "Bestsellers showcase",
                    "items": [top_items[0].name] if top_items else ["Top item"],
                    "offer_suggestion": "Feature at regular price with story"
                },
                {
                    "week": 2,
                    "focus": "Slow day promotion",
                    "items": [top_items[1].name] if len(top_items) > 1 else ["Popular item"],
                    "offer_suggestion": "15% off on slowest day"
                },
                {
                    "week": 3,
                    "focus": "Combo deal",
                    "items": [item.name for item in top_items[:2]] if len(top_items) >= 2 else ["Items"],
                    "offer_suggestion": "Bundle discount"
                },
                {
                    "week": 4,
                    "focus": "Customer appreciation",
                    "items": [top_items[2].name] if len(top_items) > 2 else ["Special item"],
                    "offer_suggestion": "Loyalty reward or free upgrade"
                }
            ],
            "engagement_tactics": [
                {
                    "tactic": "Food Photography",
                    "implementation": "Post high-quality photos of dishes during golden hour",
                    "expected_outcome": "Higher engagement and shares"
                },
                {
                    "tactic": "Interactive Polls",
                    "implementation": "Ask followers to vote on next week's special",
                    "expected_outcome": "Increased comments and customer involvement"
                },
                {
                    "tactic": "User-Generated Content",
                    "implementation": "Encourage customers to tag restaurant in their posts",
                    "expected_outcome": "Authentic social proof and extended reach"
                }
            ],
            "note": "Using template strategy. Configure OPENAI_API_KEY for AI-powered recommendations.",
            "generated_at": datetime.utcnow().isoformat()
        }
