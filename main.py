#!/usr/bin/env python3
"""
Social Media Automation - Main Orchestration Script

This script orchestrates the entire social media content generation and posting workflow:
1. Loads restaurant data and campaign information
2. Generates AI-powered content for menu items
3. Creates platform-specific images with text overlays
4. Posts to Facebook, Instagram, and TikTok

Usage:
    python main.py --restaurant hults_cafe --campaign thanksgiving --items 3 --dry-run
    python main.py --restaurant hults_cafe --campaign "Weekend Special" --post
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import Config, RestaurantConfig, validate_api_keys
from content_generator import ContentGenerator
from social_poster import SocialMediaManager
from campaign_manager import (
    CampaignManager,
    create_thanksgiving_campaign,
    create_weekend_special_campaign,
    create_daily_special_campaign
)


def setup_campaign_templates():
    """Initialize campaign templates if they don't exist"""
    manager = CampaignManager(Config.TEMPLATES_DIR)

    # Create default campaigns if templates directory is empty
    if not manager.list_campaigns():
        print("Creating default campaign templates...")
        manager.create_campaign_template(create_thanksgiving_campaign())
        manager.create_campaign_template(create_weekend_special_campaign())
        manager.create_campaign_template(create_daily_special_campaign())
        manager.load_templates()

    return manager


def validate_setup(restaurant_slug: str) -> bool:
    """Validate that everything is set up correctly"""
    print("\n" + "=" * 60)
    print("VALIDATING SETUP")
    print("=" * 60)

    all_valid = True

    # Check API keys
    print("\n1. Checking API credentials...")
    api_validation = validate_api_keys()

    if api_validation["openai"]:
        print("   ✅ OpenAI API key configured")
    else:
        print("   ❌ OpenAI API key missing")
        all_valid = False

    if api_validation["facebook"]:
        print("   ✅ Facebook API credentials configured")
    else:
        print("   ⚠️  Facebook API credentials missing (required for posting)")

    if api_validation["instagram"]:
        print("   ✅ Instagram API credentials configured")
    else:
        print("   ⚠️  Instagram API credentials missing (required for posting)")

    # Check restaurant data
    print("\n2. Checking restaurant data...")
    restaurant = RestaurantConfig(restaurant_slug)
    data_validation = restaurant.validate_data()

    if data_validation["images_dir_exists"]:
        print("   ✅ Images directory exists")
    else:
        print("   ❌ Images directory not found")
        all_valid = False

    if data_validation["popular_items_exists"]:
        print("   ✅ Popular items Excel file exists")
    else:
        print("   ❌ Popular items Excel file not found")
        all_valid = False

    if data_validation["restaurant_brief_exists"]:
        print("   ✅ Restaurant brief exists")
    else:
        print("   ❌ Restaurant brief not found")
        all_valid = False

    if data_validation["errors"]:
        print("\n   Errors:")
        for error in data_validation["errors"]:
            print(f"     - {error}")

    return all_valid


def generate_content(
    restaurant_slug: str,
    campaign_name: str,
    num_items: int = 3,
    platforms: list = None
) -> dict:
    """
    Generate social media content for restaurant

    Args:
        restaurant_slug: Restaurant identifier
        campaign_name: Campaign name to use
        num_items: Number of items to create content for
        platforms: List of platforms (default: facebook, instagram)

    Returns:
        Dict with generated content packages
    """
    if platforms is None:
        platforms = ["facebook", "instagram"]

    print("\n" + "=" * 60)
    print("GENERATING CONTENT")
    print("=" * 60)

    # Initialize
    restaurant = RestaurantConfig(restaurant_slug)
    generator = ContentGenerator(restaurant)
    campaign_manager = setup_campaign_templates()

    # Get campaign
    campaign = campaign_manager.get_campaign(campaign_name)
    if not campaign:
        print(f"\n❌ Campaign '{campaign_name}' not found")
        print(f"Available campaigns: {', '.join(campaign_manager.list_campaigns())}")
        return None

    print(f"\n📋 Campaign: {campaign.name}")
    print(f"   Theme: {campaign.theme}")
    print(f"   Dates: {campaign.start_date.strftime('%b %d')} - {campaign.end_date.strftime('%b %d, %Y')}")
    print(f"   Active: {'Yes' if campaign.is_active() else 'No'}")

    # Load items
    print(f"\n📊 Loading popular items (top {num_items})...")
    items_df = generator.load_popular_items(top_n=num_items)

    if len(items_df) == 0:
        print("❌ No items found in Excel file")
        return None

    print(f"   Found {len(items_df)} items")

    # Generate content for each item
    campaign_context = campaign.get_context_prompt()
    all_content = []

    for idx, row in items_df.iterrows():
        item_info = row.to_dict()

        content_package = generator.generate_content_for_item(
            item_info,
            campaign_context,
            platforms=platforms
        )

        if content_package:
            all_content.append(content_package)

    print(f"\n✅ Generated content for {len(all_content)} items")

    # Save summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = restaurant.get_output_path(
        f"content_summary_{timestamp}.json"
    )

    with open(summary_file, 'w') as f:
        json.dump({
            "restaurant": restaurant_slug,
            "campaign": campaign.to_dict(),
            "generated_at": timestamp,
            "items": all_content
        }, f, indent=2)

    print(f"\n💾 Summary saved: {summary_file}")

    return {
        "restaurant": restaurant_slug,
        "campaign": campaign_name,
        "content": all_content,
        "summary_file": str(summary_file)
    }


def post_content(
    content_data: dict,
    platforms: list = None,
    dry_run: bool = True
) -> dict:
    """
    Post generated content to social media platforms

    Args:
        content_data: Generated content from generate_content()
        platforms: List of platforms to post to
        dry_run: If True, simulate posting without actually posting

    Returns:
        Dict with posting results
    """
    if platforms is None:
        platforms = ["facebook", "instagram"]

    print("\n" + "=" * 60)
    if dry_run:
        print("SIMULATING POSTS (DRY RUN)")
    else:
        print("POSTING TO SOCIAL MEDIA")
    print("=" * 60)

    manager = SocialMediaManager()
    all_results = []

    for item_content in content_data["content"]:
        print(f"\n📱 {item_content['item_name']}")

        results = manager.post_to_all_platforms(
            item_content["platforms"],
            platforms=platforms,
            dry_run=dry_run
        )

        all_results.append({
            "item": item_content['item_name'],
            "results": results
        })

    # Save results
    if not dry_run:
        restaurant = RestaurantConfig(content_data["restaurant"])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = restaurant.get_output_path(
            f"post_results_{timestamp}.json",
            subfolder="posted"
        )

        with open(results_file, 'w') as f:
            json.dump({
                "posted_at": timestamp,
                "campaign": content_data["campaign"],
                "results": all_results
            }, f, indent=2)

        print(f"\n💾 Results saved: {results_file}")

    return all_results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Social Media Automation for Restaurants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate content (dry run)
  python main.py --restaurant hults_cafe --campaign "Thanksgiving 2024" --items 3

  # Generate and post to Facebook only
  python main.py --restaurant hults_cafe --campaign "Weekend Special" --platforms facebook --post

  # Generate for all platforms with 5 items
  python main.py --restaurant hults_cafe --campaign "Daily Special" --items 5 --platforms facebook instagram tiktok

  # Validate setup only
  python main.py --restaurant hults_cafe --validate
        """
    )

    parser.add_argument(
        "--restaurant",
        required=True,
        help="Restaurant slug (e.g., hults_cafe)"
    )

    parser.add_argument(
        "--campaign",
        help="Campaign name (e.g., 'Thanksgiving 2024')"
    )

    parser.add_argument(
        "--items",
        type=int,
        default=3,
        help="Number of popular items to feature (default: 3)"
    )

    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["facebook", "instagram", "tiktok"],
        default=["facebook", "instagram"],
        help="Social media platforms to target (default: facebook instagram)"
    )

    parser.add_argument(
        "--post",
        action="store_true",
        help="Actually post to social media (default: dry run only)"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Only validate setup, don't generate content"
    )

    args = parser.parse_args()

    # Header
    print("\n" + "=" * 60)
    print("SOCIAL MEDIA AUTOMATION")
    print("=" * 60)
    print(f"Restaurant: {args.restaurant}")
    if args.campaign:
        print(f"Campaign: {args.campaign}")
    print(f"Platforms: {', '.join(args.platforms)}")
    print(f"Mode: {'LIVE POSTING' if args.post else 'DRY RUN'}")

    # Validate setup
    if not validate_setup(args.restaurant):
        print("\n❌ Setup validation failed. Please fix the errors above.")
        return 1

    if args.validate:
        print("\n✅ Validation complete!")
        return 0

    if not args.campaign:
        print("\n❌ --campaign is required for content generation")
        print("\nRun with --validate to check setup only")
        return 1

    # Generate content
    content_data = generate_content(
        args.restaurant,
        args.campaign,
        args.items,
        args.platforms
    )

    if not content_data:
        print("\n❌ Content generation failed")
        return 1

    # Post content
    dry_run = not args.post
    results = post_content(content_data, args.platforms, dry_run=dry_run)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Generated content for {len(content_data['content'])} items")

    if dry_run:
        print("\n💡 This was a DRY RUN. No actual posts were made.")
        print("   To post for real, add the --post flag")
    else:
        successful = sum(1 for r in results if any(
            p.get("success") for p in r["results"].values()
        ))
        print(f"✅ Successfully posted {successful} items")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
