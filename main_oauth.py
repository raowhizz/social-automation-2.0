#!/usr/bin/env python3
"""
Social Media Automation with OAuth Integration

Updated version of main.py that uses multi-tenant OAuth tokens instead of hardcoded credentials.

Usage:
    python main_oauth.py --tenant test_restaurant --campaign weekend_special --items 3
    python main_oauth.py --tenant krusty_pizza --campaign thanksgiving --post
"""
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "multi-tenant-oauth"))

# OAuth integration
from oauth_integration import MultiTenantPosterFactory, OAuthTokenManager

# Existing imports
from config import Config, RestaurantConfig, validate_api_keys
from content_generator import ContentGenerator
from campaign_manager import CampaignManager

# Tenant registry - maps restaurant slugs to tenant IDs
TENANT_REGISTRY = {
    "test_restaurant": "1485f8b4-04e9-47b7-ad8a-27adbe78d20a",  # Test Restaurant
    "krusty_pizza": "1485f8b4-04e9-47b7-ad8a-27adbe78d20a",     # Using same for demo
    # Add more restaurants here:
    # "pizza_place": "tenant-id-here",
    # "burger_joint": "tenant-id-here",
}


def check_oauth_health(tenant_slug: str) -> bool:
    """
    Check OAuth token health for a tenant.

    Args:
        tenant_slug: Restaurant slug (e.g., 'krusty_pizza')

    Returns:
        True if tokens are healthy, False otherwise
    """
    if tenant_slug not in TENANT_REGISTRY:
        print(f"\n❌ Tenant '{tenant_slug}' not found in registry!")
        print(f"   Available tenants: {', '.join(TENANT_REGISTRY.keys())}")
        return False

    tenant_id = TENANT_REGISTRY[tenant_slug]

    print(f"\n{'='*60}")
    print(f"CHECKING OAUTH STATUS FOR: {tenant_slug.upper()}")
    print('='*60)

    try:
        with OAuthTokenManager(tenant_id) as manager:
            # Get token health
            health = manager.get_token_health()

            print(f"\n📊 Token Health:")
            print(f"   Active tokens: {health['active_tokens']}")
            print(f"   Expiring soon: {health['expiring_soon']}")
            print(f"   Expired: {health['expired']}")
            print(f"   Total accounts: {health['total_accounts']}")

            if health['active_tokens'] == 0:
                print("\n❌ No active OAuth tokens found!")
                print("\n   To connect accounts, run:")
                print(f"   1. Start OAuth flow:")
                print(f"      curl -X POST http://localhost:8000/api/v1/oauth/facebook/authorize \\")
                print(f"        -H 'Content-Type: application/json' \\")
                print(f"        -d '{{\"tenant_id\": \"{tenant_id}\", \"return_url\": \"http://localhost:8000/\"}}'")
                print(f"\n   2. Open the authorization URL in your browser")
                print(f"   3. Grant permissions to connect your Facebook Page")
                return False

            # Get connected accounts
            accounts = manager.get_account_info()

            print(f"\n📱 Connected Accounts:")
            for account in accounts:
                print(f"   • {account['account_name']} ({account['platform']})")

            if health['expiring_soon'] > 0:
                print(f"\n⚠️  Warning: {health['expiring_soon']} tokens expiring soon")
                print("   Consider refreshing tokens or reconnecting accounts")

            print("\n✅ OAuth tokens are healthy!")
            return True

    except Exception as e:
        print(f"\n❌ Error checking OAuth status: {e}")
        return False


def run_campaign_with_oauth(
    tenant_slug: str,
    campaign_name: str,
    num_items: int = 3,
    dry_run: bool = True,
    platforms: list = None
):
    """
    Run a campaign using OAuth tokens for a specific tenant.

    Args:
        tenant_slug: Restaurant slug (e.g., 'krusty_pizza')
        campaign_name: Campaign name (e.g., 'thanksgiving')
        num_items: Number of items to post
        dry_run: If True, don't actually post
        platforms: List of platforms to post to (['facebook', 'instagram'])
    """
    if platforms is None:
        platforms = ['facebook']

    # Get tenant ID
    tenant_id = TENANT_REGISTRY.get(tenant_slug)
    if not tenant_id:
        print(f"Error: Tenant '{tenant_slug}' not found in registry")
        return

    print(f"\n{'='*60}")
    print(f"RUNNING CAMPAIGN: {campaign_name.upper()}")
    print(f"Tenant: {tenant_slug}")
    print(f"Items: {num_items}")
    print(f"Platforms: {', '.join(platforms)}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE POSTING'}")
    print('='*60)

    # Load restaurant config
    restaurant = RestaurantConfig(tenant_slug)

    # Load campaign
    campaign_manager = CampaignManager(Config.TEMPLATES_DIR)
    campaign = campaign_manager.get_campaign(campaign_name)

    if not campaign:
        print(f"\nError: Campaign '{campaign_name}' not found")
        print(f"Available campaigns: {campaign_manager.list_campaigns()}")
        return

    # Generate content
    print("\n📝 Generating content...")
    generator = ContentGenerator()

    # For demo, we'll use a simple test post
    posts = []
    for i in range(num_items):
        post = {
            'caption': f"""🧪 Test Post #{i+1} - {campaign_name.title()} Campaign

Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This post demonstrates the multi-tenant OAuth integration!

✅ OAuth2 authentication
✅ Encrypted token storage
✅ Multi-tenant support

#{campaign_name.replace('_', '')} #TestPost #OAuth""",
            'image_path': None  # We'll post text-only for demo
        }
        posts.append(post)

    print(f"   Generated {len(posts)} posts")

    # Post to platforms
    for platform in platforms:
        print(f"\n📤 Posting to {platform.upper()}...")

        if dry_run:
            print("   [DRY RUN] Skipping actual posting")
            for i, post in enumerate(posts, 1):
                print(f"\n   Post {i}/{len(posts)}:")
                print(f"   Caption: {post['caption'][:100]}...")
            continue

        # Create OAuth-powered poster
        try:
            if platform == 'facebook':
                poster = MultiTenantPosterFactory.create_facebook_poster(tenant_id)
            elif platform == 'instagram':
                poster = MultiTenantPosterFactory.create_instagram_poster(tenant_id)
            else:
                print(f"   ❌ Unsupported platform: {platform}")
                continue

            print(f"   ✅ OAuth poster created successfully")

        except ValueError as e:
            print(f"   ❌ Error: {e}")
            continue

        # Post each item
        for i, post in enumerate(posts, 1):
            print(f"\n   Post {i}/{len(posts)}...")

            try:
                # Use Facebook's text post endpoint (no image)
                import requests
                url = f"https://graph.facebook.com/v18.0/{poster.page_id}/feed"

                data = {
                    "message": post['caption'],
                    "access_token": poster.access_token
                }

                response = requests.post(url, data=data)
                result = response.json()

                if 'id' in result:
                    post_id = result['id']
                    print(f"      ✅ Posted successfully!")
                    print(f"      Post ID: {post_id}")
                    print(f"      URL: https://www.facebook.com/{post_id.replace('_', '/posts/')}")
                else:
                    print(f"      ❌ Failed: {result.get('error', {}).get('message', 'Unknown error')}")

            except Exception as e:
                print(f"      ❌ Error posting: {e}")

    print(f"\n{'='*60}")
    print("✅ Campaign completed!")
    print('='*60)


def main():
    parser = argparse.ArgumentParser(
        description="Social Media Automation with OAuth Integration"
    )

    parser.add_argument(
        '--tenant',
        required=True,
        help='Tenant slug (e.g., krusty_pizza, test_restaurant)'
    )

    parser.add_argument(
        '--campaign',
        default='daily_special',
        help='Campaign name (e.g., thanksgiving, weekend_special)'
    )

    parser.add_argument(
        '--items',
        type=int,
        default=3,
        help='Number of items to post'
    )

    parser.add_argument(
        '--post',
        action='store_true',
        help='Actually post (default is dry-run)'
    )

    parser.add_argument(
        '--platforms',
        nargs='+',
        default=['facebook'],
        help='Platforms to post to (facebook, instagram)'
    )

    parser.add_argument(
        '--check-oauth',
        action='store_true',
        help='Only check OAuth status, don\'t run campaign'
    )

    args = parser.parse_args()

    # Check OAuth health
    if not check_oauth_health(args.tenant):
        print("\n⚠️  Fix OAuth issues before continuing!")
        sys.exit(1)

    if args.check_oauth:
        # Only checking OAuth, exit
        sys.exit(0)

    # Run campaign
    run_campaign_with_oauth(
        tenant_slug=args.tenant,
        campaign_name=args.campaign,
        num_items=args.items,
        dry_run=not args.post,
        platforms=args.platforms
    )


if __name__ == "__main__":
    main()
