#!/usr/bin/env python3
"""
Data Conversion Script for Krusty Pizza & Pasta
Converts menu.xlsx format to popular_items.xlsx format expected by the system
Downloads images from S3 URLs and saves them locally
"""
import os
import re
import requests
from pathlib import Path
from typing import Dict, List
import pandas as pd
from urllib.parse import urlparse


# Configuration
RESTAURANT_SLUG = "krusti_pizza_and_pasta"
BASE_DIR = Path(__file__).parent
RESTAURANT_DIR = BASE_DIR / "data" / "restaurants" / RESTAURANT_SLUG
MENU_FILE = RESTAURANT_DIR / "menu.xlsx"
IMAGES_DIR = RESTAURANT_DIR / "images"
OUTPUT_FILE = RESTAURANT_DIR / "popular_items.xlsx"


def clean_filename(name: str) -> str:
    """Convert item name to clean filename"""
    # Remove special characters, convert to lowercase
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return f"{name}.jpg"


def download_image(url: str, save_path: Path) -> bool:
    """Download image from S3 URL"""
    try:
        print(f"  Downloading: {save_path.name}...", end=" ")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            f.write(response.content)

        print("✅")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def infer_category_from_name(item_name: str, categories_df: pd.DataFrame) -> str:
    """Infer category from item name by checking Categories tab"""
    # Look through each category column to find this item
    for col in categories_df.columns:
        if col in ['Unnamed: 0', 'A', 'B']:  # Skip metadata columns
            continue

        # Check if item name appears in this category column
        category_items = categories_df[col].dropna().astype(str)
        if item_name in category_items.values:
            return col

    # Fallback: infer from keywords
    name_lower = item_name.lower()
    if 'pizza' in name_lower:
        return 'Specialty Pizza' if any(word in name_lower for word in ['supreme', 'deluxe', 'special']) else 'Pizza'
    elif 'pasta' in name_lower:
        return 'Pasta'
    elif 'burger' in name_lower:
        return 'Burgers'
    elif 'wing' in name_lower or 'chop' in name_lower:
        return 'Wings & Chops'
    elif 'bread' in name_lower or 'fries' in name_lower or 'salad' in name_lower:
        return 'Appetizers'
    elif 'drink' in name_lower or 'soda' in name_lower or 'beverage' in name_lower:
        return 'Beverages'
    else:
        return 'Specialty Items'


def infer_dietary_info(item_name: str, description: str) -> str:
    """Infer dietary information from item name and description"""
    text = f"{item_name} {description}".lower()

    dietary_tags = []

    if 'vegetarian' in text or 'veggie' in text:
        dietary_tags.append('Vegetarian option available')

    if 'chicken' in text or 'beef' in text or 'meat' in text:
        dietary_tags.append('Contains meat')

    if 'cheese' in text:
        dietary_tags.append('Contains dairy')

    if 'spicy' in text or 'hot' in text:
        dietary_tags.append('Spicy')

    return ', '.join(dietary_tags) if dietary_tags else 'N/A'


def infer_best_for(category: str, item_name: str) -> str:
    """Infer best use case for the item"""
    category_map = {
        'Combo Deal': 'Family meals, Value seekers',
        'Appetizers': 'Starters, Sharing',
        'Pizza': 'Lunch, Dinner, Parties',
        'Specialty Pizza': 'Special occasions, Pizza lovers',
        'Pasta': 'Dinner, Italian cuisine lovers',
        'Burgers': 'Lunch, Quick meals',
        'Wings & Chops': 'Game day, Parties',
        'Pizza By Slices': 'Quick lunch, Individual portions',
        'Beverages': 'Refreshment, Meals',
        'Meal Deals': 'Family dinners, Value meals'
    }

    return category_map.get(category, 'All occasions')


def convert_menu_to_popular_items():
    """Main conversion function"""
    print("=" * 60)
    print("KRUSTY PIZZA & PASTA - DATA CONVERSION")
    print("=" * 60)

    # Create images directory
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # Read Excel file
    print(f"\n1. Reading menu.xlsx...")
    items_df = pd.read_excel(MENU_FILE, sheet_name='Items')
    categories_df = pd.read_excel(MENU_FILE, sheet_name='Categories')

    print(f"   Found {len(items_df)} rows in Items tab")

    # Filter out rows without valid IDs or names
    items_df = items_df.dropna(subset=['ID', 'Name'])
    items_df = items_df[items_df['Name'].str.strip() != '']

    print(f"   Valid items: {len(items_df)}")

    # Download images and prepare data
    print(f"\n2. Downloading images from S3...")

    converted_items = []
    downloaded_count = 0

    for idx, row in items_df.iterrows():
        item_name = row['Name']
        description = row.get('Description', '')
        price = row.get('Item Price', 0.0)
        image_url = row.get('Image Name', '')

        # Skip if no image URL
        if pd.isna(image_url) or not str(image_url).startswith('http'):
            print(f"  ⚠️  Skipping {item_name}: No image URL")
            continue

        # Generate clean filename
        image_filename = clean_filename(item_name)
        image_path = IMAGES_DIR / image_filename

        # Download image
        if download_image(image_url, image_path):
            downloaded_count += 1

        # Infer category
        category = infer_category_from_name(item_name, categories_df)

        # Create converted item
        converted_item = {
            'Item Name': item_name,
            'Category': category,
            'Description': description if pd.notna(description) else f"Delicious {item_name}",
            'Price': float(price) if pd.notna(price) else 0.0,
            'Popularity Rank': idx + 1,  # Use order from Excel as initial ranking
            'Image Filename': image_filename,
            'Dietary Info': infer_dietary_info(item_name, str(description)),
            'Best For': infer_best_for(category, item_name)
        }

        converted_items.append(converted_item)

    print(f"\n   Downloaded: {downloaded_count} images")

    # Create DataFrame
    print(f"\n3. Creating popular_items.xlsx...")
    popular_df = pd.DataFrame(converted_items)

    # Sort by category and price (premium items first)
    category_order = ['Specialty Pizza', 'Pizza', 'Combo Deal', 'Meal Deals',
                     'Pasta', 'Burgers', 'Wings & Chops', 'Appetizers',
                     'Pizza By Slices', 'Beverages']

    popular_df['Category_Order'] = popular_df['Category'].apply(
        lambda x: category_order.index(x) if x in category_order else 99
    )
    popular_df = popular_df.sort_values(['Category_Order', 'Price'],
                                       ascending=[True, False])
    popular_df = popular_df.drop('Category_Order', axis=1)

    # Reassign popularity ranks
    popular_df['Popularity Rank'] = range(1, len(popular_df) + 1)

    # Save to Excel
    popular_df.to_excel(OUTPUT_FILE, index=False, sheet_name='Popular Items')

    print(f"   ✅ Created: {OUTPUT_FILE}")
    print(f"   Items: {len(popular_df)}")

    # Show summary by category
    print(f"\n4. Summary by Category:")
    category_counts = popular_df['Category'].value_counts()
    for category, count in category_counts.items():
        print(f"   {category}: {count} items")

    # Show top 10 items
    print(f"\n5. Top 10 Items for Social Media:")
    top_10 = popular_df.head(10)
    for idx, row in top_10.iterrows():
        print(f"   {row['Popularity Rank']}. {row['Item Name']} ({row['Category']}) - ${row['Price']}")

    print("\n" + "=" * 60)
    print("✅ CONVERSION COMPLETE!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Review: {OUTPUT_FILE}")
    print(f"2. Check images in: {IMAGES_DIR}/")
    print(f"3. Create restaurant_brief.txt")
    print(f"4. Run: python main.py --restaurant {RESTAURANT_SLUG} --validate")
    print("=" * 60)

    return popular_df


if __name__ == "__main__":
    convert_menu_to_popular_items()
