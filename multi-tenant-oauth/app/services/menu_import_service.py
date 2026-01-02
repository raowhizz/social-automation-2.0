"""Menu import service for Innowi POS Excel files."""

from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
import pandas as pd
import logging

from app.models import MenuItem, RestaurantProfile, Tenant

logger = logging.getLogger(__name__)


class MenuImportService:
    """Service for importing menu data from Innowi POS Excel files."""

    def __init__(self):
        """Initialize menu import service."""
        pass

    async def import_menu_from_excel(
        self,
        db: Session,
        file_path: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Import menu data from Innowi POS Excel file.

        Args:
            db: Database session
            file_path: Path to uploaded Excel file
            tenant_id: Tenant UUID

        Returns:
            Dict with import statistics and results

        Excel file structure (Innowi POS format):
        - Taxes sheet: Tax rates
        - Discounts sheet: Discount rules
        - Categories sheet: Menu categories
        - Items sheet: Menu items with details
        - Modifier_Group sheet: Modifier options
        """
        try:
            # Read all sheets from Excel file
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')

            # Parse data from each sheet
            categories = self._parse_categories(excel_data.get('Categories'))
            items = self._parse_items(excel_data.get('Items'))
            modifiers = self._parse_modifiers(excel_data.get('Modifier_Group'))

            # Link modifiers to items
            items_with_modifiers = self._link_modifiers_to_items(items, modifiers)

            # Clear existing menu items for this tenant
            db.query(MenuItem).filter(MenuItem.tenant_id == uuid.UUID(tenant_id)).delete()

            # Import items into database
            imported_items = []
            for item_data in items_with_modifiers:
                menu_item = self._create_menu_item(item_data, tenant_id)
                db.add(menu_item)
                imported_items.append(menu_item)

            # Update restaurant profile with import metadata
            profile = db.query(RestaurantProfile).filter(
                RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
            ).first()

            if profile:
                profile.last_menu_import = datetime.utcnow()
                profile.menu_items_count = len(imported_items)
            else:
                # Create new profile if doesn't exist
                profile = RestaurantProfile(
                    tenant_id=uuid.UUID(tenant_id),
                    last_menu_import=datetime.utcnow(),
                    menu_items_count=len(imported_items),
                )
                db.add(profile)

            db.commit()

            # Calculate statistics
            stats = self._calculate_import_stats(imported_items, categories)

            logger.info(f"Successfully imported {len(imported_items)} menu items for tenant {tenant_id}")

            return {
                "success": True,
                "items_imported": len(imported_items),
                "categories_found": len(categories),
                "items_with_modifiers": sum(1 for item in imported_items if item.has_modifiers),
                "deals_found": sum(1 for item in imported_items if item.is_deal),
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"Error importing menu from Excel: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "items_imported": 0,
            }

    def _parse_categories(self, df: Optional[pd.DataFrame]) -> Dict[str, str]:
        """
        Parse categories sheet from Excel.

        Args:
            df: DataFrame from Categories sheet

        Returns:
            Dict mapping category ID to category name
        """
        if df is None or df.empty:
            return {}

        categories = {}
        for _, row in df.iterrows():
            try:
                cat_id = str(row.get('ID', ''))
                cat_name = str(row.get('Name', ''))
                if cat_id and cat_name:
                    categories[cat_id] = cat_name
            except Exception as e:
                logger.warning(f"Error parsing category row: {e}")
                continue

        return categories

    def _parse_items(self, df: Optional[pd.DataFrame]) -> List[Dict[str, Any]]:
        """
        Parse items sheet from Excel.

        Args:
            df: DataFrame from Items sheet

        Returns:
            List of item dictionaries
        """
        if df is None or df.empty:
            return []

        items = []
        for _, row in df.iterrows():
            try:
                # Skip rows with NaN ID (header rows or empty rows)
                if pd.isna(row.get('ID')):
                    continue

                # Extract item data (use actual column names from Innowi export)
                name = str(row.get('Name', ''))
                if not name or name == 'nan':
                    continue

                item = {
                    'external_id': str(int(row.get('ID', 0))) if pd.notna(row.get('ID')) else None,
                    'name': name,
                    'description': str(row.get('Description', '')) if pd.notna(row.get('Description')) else None,
                    'image_url': str(row.get('Image Name', '')) if pd.notna(row.get('Image Name')) else None,
                    'price': self._parse_decimal(row.get('Item Price')),
                    'cost': self._parse_decimal(row.get('Item Cost')) if 'Item Cost' in row else None,
                    'category_id': None,  # Will be matched from Categories sheet later
                    'category_name': self._find_item_category(row),  # Find which category this item belongs to
                    'is_deal': 'Deal' in name or 'Combo' in name or 'combo' in name.lower(),
                    'modifier_groups': str(row.get('Modifier Groups', '')) if pd.notna(row.get('Modifier Groups')) else '',
                }
                items.append(item)
            except Exception as e:
                logger.warning(f"Error parsing item row: {e}")
                continue

        return items

    def _find_item_category(self, row: pd.Series) -> Optional[str]:
        """
        Infer category from item name using keyword matching.

        Args:
            row: DataFrame row

        Returns:
            Category name or None
        """
        name = str(row.get('Name', '')).lower()

        # Category keywords mapping
        category_keywords = {
            'Pizza': ['pizza'],
            'Pasta': ['pasta', 'spaghetti', 'fettuccine', 'penne'],
            'Burgers': ['burger'],
            'Wings': ['wing', 'wings', 'chops', 'tender', 'tenders'],
            'Appetizers': ['falafel', 'garlic bread', 'breadsticks', 'fries', 'salad'],
            'Beverages': ['soda', 'drink', 'water', 'juice', 'tea', 'coffee'],
            'Deals': ['deal', 'combo'],
            'Desserts': ['dessert', 'cake', 'ice cream'],
        }

        # Check each category
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in name:
                    return category

        return None

    def _parse_modifiers(self, df: Optional[pd.DataFrame]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse modifier groups sheet from Excel.

        Args:
            df: DataFrame from Modifier_Group sheet

        Returns:
            Dict mapping modifier group name to list of modifiers
        """
        if df is None or df.empty:
            return {}

        modifier_groups = {}
        for _, row in df.iterrows():
            try:
                group_name = str(row.get('Group Name', ''))
                modifier_name = str(row.get('Name', ''))
                modifier_price = self._parse_decimal(row.get('Price', 0))

                if group_name:
                    if group_name not in modifier_groups:
                        modifier_groups[group_name] = []

                    modifier_groups[group_name].append({
                        'name': modifier_name,
                        'price': float(modifier_price) if modifier_price else 0,
                    })
            except Exception as e:
                logger.warning(f"Error parsing modifier row: {e}")
                continue

        return modifier_groups

    def _link_modifiers_to_items(
        self,
        items: List[Dict[str, Any]],
        modifiers: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Link modifier groups to menu items.

        Args:
            items: List of item dictionaries
            modifiers: Dict of modifier groups

        Returns:
            Items with linked modifiers
        """
        for item in items:
            modifier_group_names = item.get('modifier_groups', '').split(',')
            modifier_group_names = [name.strip() for name in modifier_group_names if name.strip()]

            if modifier_group_names:
                item['modifiers'] = []
                for group_name in modifier_group_names:
                    if group_name in modifiers:
                        item['modifiers'].append({
                            'group_name': group_name,
                            'options': modifiers[group_name],
                        })
                item['has_modifiers'] = True
            else:
                item['modifiers'] = None
                item['has_modifiers'] = False

        return items

    def _create_menu_item(self, item_data: Dict[str, Any], tenant_id: str) -> MenuItem:
        """
        Create a MenuItem model instance from parsed data.

        Args:
            item_data: Parsed item dictionary
            tenant_id: Tenant UUID

        Returns:
            MenuItem instance
        """
        return MenuItem(
            tenant_id=uuid.UUID(tenant_id),
            external_id=item_data.get('external_id'),
            category=item_data.get('category_name'),
            name=item_data['name'],
            description=item_data.get('description'),
            image_url=item_data.get('image_url'),
            price=item_data.get('price'),
            cost=item_data.get('cost'),
            has_modifiers=item_data.get('has_modifiers', False),
            modifiers=item_data.get('modifiers'),
            is_deal=item_data.get('is_deal', False),
            out_of_stock=False,
            times_ordered=0,
            total_revenue=Decimal('0'),
            popularity_rank=None,
            times_posted_about=0,
            last_featured_date=None,
        )

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """
        Parse a value to Decimal, handling various formats.

        Args:
            value: Value to parse

        Returns:
            Decimal value or None
        """
        if pd.isna(value):
            return None

        try:
            # Remove currency symbols and commas
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').strip()
            return Decimal(str(value))
        except Exception:
            return None

    def _calculate_import_stats(
        self,
        items: List[MenuItem],
        categories: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Calculate statistics about imported menu.

        Args:
            items: List of imported menu items
            categories: Dict of categories

        Returns:
            Statistics dictionary
        """
        # Calculate category distribution
        category_counts = {}
        for item in items:
            cat = item.category or 'Uncategorized'
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Calculate price statistics
        prices = [float(item.price) for item in items if item.price]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        return {
            'total_categories': len(set(item.category for item in items if item.category)),
            'category_distribution': category_counts,
            'average_price': round(avg_price, 2),
            'min_price': round(min_price, 2),
            'max_price': round(max_price, 2),
            'items_with_images': sum(1 for item in items if item.image_url),
            'items_with_descriptions': sum(1 for item in items if item.description),
        }
