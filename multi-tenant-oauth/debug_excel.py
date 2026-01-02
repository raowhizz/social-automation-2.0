"""Debug script to inspect Excel file structure."""

import pandas as pd

print("=" * 80)
print("MENU FILE STRUCTURE")
print("=" * 80)

# Read menu Excel file
menu_file = "krusti.pizza.pasta.dec28.xlsx"
excel_data = pd.read_excel(menu_file, sheet_name=None, engine='openpyxl')

for sheet_name, df in excel_data.items():
    print(f"\n### Sheet: {sheet_name}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst 3 rows:")
    print(df.head(3))
    print("\n" + "-" * 80)

print("\n" + "=" * 80)
print("SALES FILE STRUCTURE")
print("=" * 80)

# Read sales Excel file
sales_file = "Krusti-Pizza-Pasta-Order History Report 12-01-2025_12-28-2025.xlsx"

# Try different skiprows values
for skiprows in [0, 1, 2, 3, 4, 5]:
    print(f"\n### With skiprows={skiprows}")
    try:
        df = pd.read_excel(sales_file, skiprows=skiprows, engine='openpyxl')
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"\nFirst 2 rows:")
        print(df.head(2))
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 80)
