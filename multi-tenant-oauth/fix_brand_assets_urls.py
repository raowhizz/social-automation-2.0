#!/usr/bin/env python3
"""Fix brand_assets URLs - copy S3 URLs from menu_items."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/social_automation_multi_tenant")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def fix_brand_assets_urls():
    """Update brand_assets.file_url with S3 URLs from menu_items.image_url."""
    session = Session()

    try:
        # Find all menu items with S3 URLs that have linked assets
        query = text("""
            SELECT
                mi.id as menu_id,
                mi.name as menu_name,
                mi.image_url as s3_url,
                mi.asset_id,
                ba.file_url as current_asset_url
            FROM menu_items mi
            INNER JOIN brand_assets ba ON mi.asset_id = ba.id
            WHERE mi.image_url IS NOT NULL
            AND mi.image_url LIKE '%s3%'
            AND ba.file_url NOT LIKE '%s3%'
        """)

        results = session.execute(query).fetchall()

        print(f"Found {len(results)} brand assets to update\n")

        if len(results) == 0:
            print("No assets need updating!")
            return

        # Show what will be updated
        for row in results[:5]:  # Show first 5
            print(f"Menu: {row.menu_name}")
            print(f"  Current (ngrok): {row.current_asset_url}")
            print(f"  Will update to (S3): {row.s3_url}")
            print()

        if len(results) > 5:
            print(f"... and {len(results) - 5} more\n")

        # Ask for confirmation
        confirm = input(f"Update {len(results)} assets? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return

        # Update all brand_assets
        update_query = text("""
            UPDATE brand_assets ba
            SET file_url = mi.image_url
            FROM menu_items mi
            WHERE ba.id = mi.asset_id
            AND mi.image_url IS NOT NULL
            AND mi.image_url LIKE '%s3%'
            AND ba.file_url NOT LIKE '%s3%'
        """)

        result = session.execute(update_query)
        session.commit()

        print(f"\n✅ Updated {result.rowcount} brand assets with S3 URLs!")
        print("\nVerifying updates...")

        # Verify
        verify_query = text("""
            SELECT COUNT(*)
            FROM brand_assets ba
            INNER JOIN menu_items mi ON ba.id = mi.asset_id
            WHERE mi.image_url LIKE '%s3%'
            AND ba.file_url LIKE '%s3%'
        """)

        count = session.execute(verify_query).scalar()
        print(f"✅ {count} menu items now have matching S3 URLs in brand_assets")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("🔧 Brand Assets URL Fixer")
    print("=" * 50)
    print("This will update brand_assets.file_url to use S3 URLs from menu_items.image_url\n")

    fix_brand_assets_urls()
