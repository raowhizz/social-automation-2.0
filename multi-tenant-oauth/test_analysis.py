"""Test script for restaurant AI analysis."""

import requests
import json

# Configuration
API_URL = "http://localhost:8000"
TENANT_ID = "1485f8b4-04e9-47b7-ad8a-27adbe78d20a"  # Krusty Pizza tenant


def trigger_analysis():
    """Trigger AI analysis for the restaurant."""
    print("=" * 80)
    print("TRIGGERING AI ANALYSIS")
    print("=" * 80)

    url = f"{API_URL}/api/v1/restaurant/{TENANT_ID}/analyze"
    response = requests.post(url)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("\n✅ Analysis completed successfully!\n")

        # Print brand analysis
        if result.get('brand_analysis'):
            print("🎨 BRAND PERSONALITY:")
            print("-" * 80)
            brand = result['brand_analysis']

            if 'brand_personality' in brand:
                print(f"\nVoice Tone: {brand['brand_personality'].get('voice_tone')}")
                print(f"Target Audience: {brand['brand_personality'].get('target_audience')}")
                print(f"Key Attributes: {', '.join(brand['brand_personality'].get('key_attributes', []))}")
                print(f"USPs: {', '.join(brand['brand_personality'].get('unique_selling_points', []))}")

            if 'cuisine_analysis' in brand:
                print(f"\nPrimary Cuisine: {brand['cuisine_analysis'].get('primary_cuisine')}")
                print(f"Cuisine Style: {brand['cuisine_analysis'].get('cuisine_style')}")
                print(f"Price Positioning: {brand['cuisine_analysis'].get('price_positioning')}")
                print(f"Signature Items: {', '.join(brand['cuisine_analysis'].get('signature_items', []))}")

            if 'content_themes' in brand:
                print(f"\nContent Pillars: {', '.join(brand['content_themes'].get('content_pillars', []))}")
                print(f"Hashtags: {' '.join(brand['content_themes'].get('hashtag_suggestions', []))}")

        # Print sales insights
        if result.get('sales_insights'):
            print("\n\n📊 SALES INSIGHTS:")
            print("-" * 80)
            sales = result['sales_insights']

            if 'sales_patterns' in sales:
                patterns = sales['sales_patterns']
                print(f"\nBusiest Days: {', '.join(patterns.get('busiest_days', []))}")
                print(f"Slowest Days: {', '.join(patterns.get('slowest_days', []))}")

            if 'item_performance' in sales:
                perf = sales['item_performance']

                if perf.get('top_sellers'):
                    print("\nTop Sellers:")
                    for i, item in enumerate(perf['top_sellers'][:5], 1):
                        print(f"  {i}. {item.get('name')} - {item.get('times_ordered')} orders")
                        print(f"     💡 {item.get('insight')}")

            if 'promotional_recommendations' in sales:
                print("\n💰 Promotional Recommendations:")
                for i, promo in enumerate(sales['promotional_recommendations'][:3], 1):
                    print(f"\n  {i}. {promo.get('strategy')}")
                    print(f"     Target: {promo.get('target_day')}")
                    print(f"     Reason: {promo.get('reason')}")
                    print(f"     Suggested Discount: {promo.get('suggested_discount')}")

        # Print content strategy
        if result.get('content_strategy'):
            print("\n\n📱 CONTENT STRATEGY:")
            print("-" * 80)
            strategy = result['content_strategy']

            if 'posting_schedule' in strategy:
                schedule = strategy['posting_schedule']
                print(f"\nPosting Frequency: {schedule.get('frequency')}")
                print(f"Best Days: {', '.join(schedule.get('best_days_to_post', []))}")
                print(f"Best Times: {', '.join(schedule.get('best_times', []))}")
                print(f"Rationale: {schedule.get('rationale')}")

            if 'content_mix' in strategy:
                print("\nContent Mix:")
                for content_type in strategy['content_mix']:
                    print(f"  • {content_type.get('content_type')}: {content_type.get('percentage')}%")
                    print(f"    {content_type.get('description')}")

            if 'featured_items_rotation' in strategy:
                rotation = strategy['featured_items_rotation']
                print(f"\nFeatured Items Rotation:")
                print(f"  Weekly Rotation: {', '.join(rotation.get('weekly_rotation', []))}")

        # Print full JSON for reference
        print("\n\n" + "=" * 80)
        print("FULL JSON RESPONSE:")
        print("=" * 80)
        print(json.dumps(result, indent=2))

    else:
        print(f"❌ Error: {response.text}")


def get_profile():
    """Get restaurant profile after analysis."""
    print("\n\n" + "=" * 80)
    print("GETTING RESTAURANT PROFILE")
    print("=" * 80)

    url = f"{API_URL}/api/v1/restaurant/{TENANT_ID}/profile"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        profile = response.json()
        print("\n✅ Profile retrieved successfully!\n")
        print(f"Restaurant ID: {profile.get('id')}")
        print(f"Menu Items Count: {profile.get('menu_items_count')}")
        print(f"Sales Records Count: {profile.get('sales_records_count')}")
        print(f"Last Menu Import: {profile.get('last_menu_import')}")
        print(f"Last Sales Import: {profile.get('last_sales_import')}")

        print("\n📊 Analysis Status:")
        print(f"Brand Analysis: {'✅ Available' if profile.get('brand_analysis') else '❌ Not available'}")
        print(f"Sales Insights: {'✅ Available' if profile.get('sales_insights') else '❌ Not available'}")
        print(f"Content Strategy: {'✅ Available' if profile.get('content_strategy') else '❌ Not available'}")

    else:
        print(f"❌ Error: {response.text}")


if __name__ == "__main__":
    trigger_analysis()
    get_profile()
