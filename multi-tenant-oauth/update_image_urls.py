#!/usr/bin/env python3
"""Update image URLs from localhost to ngrok URL."""

import os
from sqlalchemy import create_engine, text

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/social_automation_multi_tenant")
engine = create_engine(DATABASE_URL)

# Old and new URLs
OLD_URL = "http://localhost:8000"
NEW_URL = "https://kristian-unrenewable-mercedez.ngrok-free.dev"

print(f"Updating image URLs...")
print(f"  From: {OLD_URL}")
print(f"  To:   {NEW_URL}")
print()

with engine.connect() as conn:
    # Update brand_assets table
    result = conn.execute(
        text("""
            UPDATE brand_assets
            SET file_url = REPLACE(file_url, :old_url, :new_url)
            WHERE file_url LIKE :pattern
        """),
        {"old_url": OLD_URL, "new_url": NEW_URL, "pattern": f"{OLD_URL}%"}
    )
    conn.commit()

    print(f"✅ Updated {result.rowcount} image URLs in brand_assets table")

    # Update post_history table
    result = conn.execute(
        text("""
            UPDATE post_history
            SET image_url = REPLACE(image_url, :old_url, :new_url)
            WHERE image_url LIKE :pattern
        """),
        {"old_url": OLD_URL, "new_url": NEW_URL, "pattern": f"{OLD_URL}%"}
    )
    conn.commit()

    print(f"✅ Updated {result.rowcount} image URLs in post_history table")

print()
print("Done! All image URLs have been updated to use the ngrok URL.")
