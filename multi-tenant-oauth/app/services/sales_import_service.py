"""Sales import service for Innowi POS order history Excel files."""

from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
import pandas as pd
import logging
import re

from app.models import SalesData, RestaurantProfile, MenuItem

logger = logging.getLogger(__name__)


class SalesImportService:
    """Service for importing sales/order history from Innowi POS Excel files."""

    def __init__(self):
        """Initialize sales import service."""
        pass

    async def import_sales_from_excel(
        self,
        db: Session,
        file_path: str,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Import sales data from Innowi POS order history Excel file.

        Args:
            db: Database session
            file_path: Path to uploaded Excel file
            tenant_id: Tenant UUID

        Returns:
            Dict with import statistics and results

        Excel file structure (Innowi POS Order History):
        - Columns: Order ID, Order Date, Items, Customer Name, Total Amount, Status
        - Header rows may contain report metadata (skip first 4 rows)
        """
        try:
            # Read Excel file, skipping header rows (Innowi has 5 header rows)
            df = pd.read_excel(file_path, skiprows=5, engine='openpyxl')

            # Clean column names (remove extra whitespace)
            df.columns = df.columns.str.strip()

            # Parse orders from DataFrame
            orders = self._parse_orders(df)

            # Clear existing sales data for this tenant
            db.query(SalesData).filter(SalesData.tenant_id == uuid.UUID(tenant_id)).delete()

            # Import orders into database
            imported_orders = []
            for order_data in orders:
                sales_record = self._create_sales_record(order_data, tenant_id)
                db.add(sales_record)
                imported_orders.append(sales_record)

            # Update menu items popularity based on sales data
            await self._update_menu_popularity(db, tenant_id, orders)

            # Update restaurant profile with import metadata
            profile = db.query(RestaurantProfile).filter(
                RestaurantProfile.tenant_id == uuid.UUID(tenant_id)
            ).first()

            if profile:
                profile.last_sales_import = datetime.utcnow()
                profile.sales_records_count = len(imported_orders)
            else:
                # Create new profile if doesn't exist
                profile = RestaurantProfile(
                    tenant_id=uuid.UUID(tenant_id),
                    last_sales_import=datetime.utcnow(),
                    sales_records_count=len(imported_orders),
                )
                db.add(profile)

            db.commit()

            # Calculate statistics
            stats = self._calculate_sales_stats(imported_orders)

            logger.info(f"Successfully imported {len(imported_orders)} orders for tenant {tenant_id}")

            return {
                "success": True,
                "orders_imported": len(imported_orders),
                "date_range": {
                    "start": min(order.order_date for order in imported_orders) if imported_orders else None,
                    "end": max(order.order_date for order in imported_orders) if imported_orders else None,
                },
                "statistics": stats,
            }

        except Exception as e:
            logger.error(f"Error importing sales from Excel: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "orders_imported": 0,
            }

    def _parse_orders(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Parse orders from DataFrame.

        Args:
            df: DataFrame from order history Excel

        Returns:
            List of order dictionaries
        """
        orders = []
        for _, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row.get('Order ID')):
                    continue

                # Parse order date (handle various formats)
                order_date = self._parse_date(row.get('Order Date'))
                if not order_date:
                    logger.warning(f"Skipping order with invalid date: {row.get('Order Date')}")
                    continue

                # Parse items ordered
                items_str = str(row.get('Items', ''))
                items_ordered = self._parse_items_ordered(items_str)

                # Parse total amount
                total_amount = self._parse_decimal(row.get('Total Amount'))
                if not total_amount:
                    logger.warning(f"Skipping order with invalid total: {row.get('Total Amount')}")
                    continue

                order = {
                    'order_id': str(row.get('Order ID', '')),
                    'order_date': order_date,
                    'items_ordered': items_ordered,
                    'subtotal': self._parse_decimal(row.get('Subtotal')) if 'Subtotal' in row else None,
                    'tax': self._parse_decimal(row.get('Tax')) if 'Tax' in row else None,
                    'tip': self._parse_decimal(row.get('Tip')) if 'Tip' in row else None,
                    'total_amount': total_amount,
                    'customer_name': str(row.get('Customer Name', '')) if pd.notna(row.get('Customer Name')) else None,
                    'customer_phone': str(row.get('Customer Phone', '')) if pd.notna(row.get('Customer Phone')) else None,
                    'order_source': str(row.get('Source', 'pos')) if 'Source' in row else 'pos',
                    'status': str(row.get('Status', 'completed')),
                }
                orders.append(order)

            except Exception as e:
                logger.warning(f"Error parsing order row: {e}")
                continue

        return orders

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """
        Parse date from various formats.

        Args:
            date_value: Date value from Excel

        Returns:
            datetime object or None
        """
        if pd.isna(date_value):
            return None

        try:
            # If already a datetime
            if isinstance(date_value, datetime):
                return date_value

            # Try parsing string formats
            if isinstance(date_value, str):
                # Remove timezone abbreviations (PST, EST, etc.) first
                date_str = re.sub(r'\s+[A-Z]{3,4}$', '', date_value)

                # Try common formats
                for fmt in [
                    '%m/%d/%Y %I:%M:%S %p',  # 12/28/2025 5:49:51 PM (after TZ removal)
                    '%m/%d/%Y %H:%M:%S',     # 12/28/2025 17:49:51
                    '%m/%d/%Y',              # 12/28/2025
                    '%Y-%m-%d %H:%M:%S',     # 2025-12-28 17:49:51
                    '%Y-%m-%d',              # 2025-12-28
                ]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue

            # Try pandas to_datetime as fallback
            return pd.to_datetime(date_value)

        except Exception as e:
            logger.warning(f"Could not parse date: {date_value} - {e}")
            return None

    def _parse_items_ordered(self, items_str: str) -> List[Dict[str, Any]]:
        """
        Parse items ordered from string format.

        Args:
            items_str: String like "Veggie Pasta(1), Ground Beef Pasta(1)"

        Returns:
            List of item dictionaries
        """
        if not items_str or pd.isna(items_str):
            return []

        items = []
        # Split by comma
        item_parts = items_str.split(',')

        for part in item_parts:
            part = part.strip()
            # Match pattern: "Item Name(quantity)"
            match = re.match(r'(.+)\((\d+)\)', part)
            if match:
                name = match.group(1).strip()
                quantity = int(match.group(2))
                items.append({
                    'name': name,
                    'quantity': quantity,
                })
            elif part:
                # No quantity found, assume 1
                items.append({
                    'name': part,
                    'quantity': 1,
                })

        return items

    def _create_sales_record(self, order_data: Dict[str, Any], tenant_id: str) -> SalesData:
        """
        Create a SalesData model instance from parsed data.

        Args:
            order_data: Parsed order dictionary
            tenant_id: Tenant UUID

        Returns:
            SalesData instance
        """
        return SalesData(
            tenant_id=uuid.UUID(tenant_id),
            order_id=order_data['order_id'],
            order_date=order_data['order_date'],
            items_ordered=order_data['items_ordered'],
            subtotal=order_data.get('subtotal'),
            tax=order_data.get('tax'),
            tip=order_data.get('tip'),
            total_amount=order_data['total_amount'],
            customer_name=order_data.get('customer_name'),
            customer_phone=order_data.get('customer_phone'),
            order_source=order_data.get('order_source'),
            status=order_data['status'],
        )

    async def _update_menu_popularity(
        self,
        db: Session,
        tenant_id: str,
        orders: List[Dict[str, Any]]
    ) -> None:
        """
        Update menu items popularity based on sales data.

        Args:
            db: Database session
            tenant_id: Tenant UUID
            orders: List of order dictionaries
        """
        # Count how many times each item was ordered
        item_counts = {}
        item_revenues = {}

        for order in orders:
            for item in order['items_ordered']:
                item_name = item['name']
                quantity = item.get('quantity', 1)

                if item_name not in item_counts:
                    item_counts[item_name] = 0
                    item_revenues[item_name] = Decimal('0')

                item_counts[item_name] += quantity

                # Estimate revenue (total / number of items in order)
                num_items_in_order = len(order['items_ordered'])
                estimated_item_revenue = order['total_amount'] / num_items_in_order
                item_revenues[item_name] += estimated_item_revenue

        # Update menu items
        menu_items = db.query(MenuItem).filter(
            MenuItem.tenant_id == uuid.UUID(tenant_id)
        ).all()

        for menu_item in menu_items:
            # Try to match by exact name first
            if menu_item.name in item_counts:
                menu_item.times_ordered = item_counts[menu_item.name]
                menu_item.total_revenue = item_revenues[menu_item.name]
            else:
                # Try fuzzy match (case-insensitive, partial match)
                for item_name, count in item_counts.items():
                    if menu_item.name.lower() in item_name.lower() or item_name.lower() in menu_item.name.lower():
                        menu_item.times_ordered = count
                        menu_item.total_revenue = item_revenues[item_name]
                        break

        # Calculate popularity ranking (1 = most popular)
        sorted_items = sorted(menu_items, key=lambda x: x.times_ordered, reverse=True)
        for rank, menu_item in enumerate(sorted_items, start=1):
            if menu_item.times_ordered > 0:
                menu_item.popularity_rank = rank

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

    def _calculate_sales_stats(self, orders: List[SalesData]) -> Dict[str, Any]:
        """
        Calculate statistics about imported sales.

        Args:
            orders: List of imported sales records

        Returns:
            Statistics dictionary
        """
        if not orders:
            return {}

        # Calculate totals
        total_revenue = sum(float(order.total_amount) for order in orders)
        total_orders = len(orders)

        # Calculate by day of week
        day_of_week_stats = {}
        for order in orders:
            day_name = order.order_date.strftime('%A')  # Monday, Tuesday, etc.
            if day_name not in day_of_week_stats:
                day_of_week_stats[day_name] = {'count': 0, 'revenue': 0}
            day_of_week_stats[day_name]['count'] += 1
            day_of_week_stats[day_name]['revenue'] += float(order.total_amount)

        # Find slowest day
        slowest_day = min(day_of_week_stats.items(), key=lambda x: x[1]['count'])[0] if day_of_week_stats else None

        # Calculate average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        return {
            'total_revenue': round(total_revenue, 2),
            'total_orders': total_orders,
            'average_order_value': round(avg_order_value, 2),
            'orders_by_day_of_week': day_of_week_stats,
            'slowest_day': slowest_day,
            'unique_customers': len(set(order.customer_name for order in orders if order.customer_name)),
        }
