"""Test script to import Krusty Pizza sample data."""

import requests
import os
from pathlib import Path

# API base URL
API_URL = "http://localhost:8000"

# Tenant ID (Krusty Pizza - from previous sessions)
TENANT_ID = "1485f8b4-04e9-47b7-ad8a-27adbe78d20a"

# File paths
MENU_FILE = "krusti.pizza.pasta.dec28.xlsx"
SALES_FILE = "Krusti-Pizza-Pasta-Order History Report 12-01-2025_12-28-2025.xlsx"

def import_menu():
    """Import menu data."""
    print("=" * 80)
    print("IMPORTING MENU DATA")
    print("=" * 80)

    if not os.path.exists(MENU_FILE):
        print(f"ERROR: Menu file not found: {MENU_FILE}")
        return

    url = f"{API_URL}/api/v1/restaurant/{TENANT_ID}/import/menu"

    with open(MENU_FILE, 'rb') as f:
        files = {'file': (MENU_FILE, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(url, files=files)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def import_sales():
    """Import sales data."""
    print("=" * 80)
    print("IMPORTING SALES DATA")
    print("=" * 80)

    if not os.path.exists(SALES_FILE):
        print(f"ERROR: Sales file not found: {SALES_FILE}")
        return

    url = f"{API_URL}/api/v1/restaurant/{TENANT_ID}/import/sales"

    with open(SALES_FILE, 'rb') as f:
        files = {'file': (SALES_FILE, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(url, files=files)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def get_restaurant_profile():
    """Get restaurant profile."""
    print("=" * 80)
    print("RESTAURANT PROFILE")
    print("=" * 80)

    url = f"{API_URL}/api/v1/restaurant/{TENANT_ID}/profile"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print(f"Name: {profile.get('name', 'Not set')}")
        print(f"Cuisine Type: {profile.get('cuisine_type', 'Not set')}")
        print(f"Menu Items Count: {profile.get('menu_items_count', 0)}")
        print(f"Sales Records Count: {profile.get('sales_records_count', 0)}")
        print(f"Last Menu Import: {profile.get('last_menu_import', 'Never')}")
        print(f"Last Sales Import: {profile.get('last_sales_import', 'Never')}")
    else:
        print(f"Error: {response.text}")
    print()

def get_menu_items():
    """Get menu items."""
    print("=" * 80)
    print("MENU ITEMS (Top 10)")
    print("=" * 80)

    url = f"{API_URL}/api/v1/restaurant/{TENANT_ID}/menu?limit=10&sort_by=name"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        items = response.json()
        print(f"Total items returned: {len(items)}")
        for item in items[:10]:
            print(f"- {item['name']} ({item['category']}) - ${item.get('price', 'N/A')}")
            if item.get('popularity_rank'):
                print(f"  Popularity Rank: #{item['popularity_rank']} | Times Ordered: {item['times_ordered']}")
    else:
        print(f"Error: {response.text}")
    print()

def get_categories():
    """Get menu categories."""
    print("=" * 80)
    print("MENU CATEGORIES")
    print("=" * 80)

    url = f"{API_URL}/api/v1/restaurant/{TENANT_ID}/menu/categories"
    response = requests.get(url)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        categories = response.json()
        print(f"Total categories: {len(categories)}")
        for cat in categories:
            print(f"- {cat['category']}: {cat['item_count']} items")
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("KRUSTY PIZZA DATA IMPORT TEST")
    print("=" * 80 + "\n")

    # Import menu data
    import_menu()

    # Import sales data
    import_sales()

    # Get profile
    get_restaurant_profile()

    # Get menu items
    get_menu_items()

    # Get categories
    get_categories()

    print("=" * 80)
    print("IMPORT TEST COMPLETED")
    print("=" * 80)
