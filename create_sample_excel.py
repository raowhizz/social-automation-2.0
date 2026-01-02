"""
Helper script to create a sample popular_items.xlsx template
Run this once to see the expected Excel format
"""
import pandas as pd

# Sample data showing the expected format
sample_data = {
    'Item Name': [
        'Classic Eggs Benedict',
        'Blueberry Pancakes',
        'Avocado Toast Special',
        'Grilled Chicken Sandwich',
        'Homemade Apple Pie',
        'Signature Coffee Blend'
    ],
    'Category': [
        'Breakfast',
        'Breakfast',
        'Breakfast',
        'Lunch',
        'Dessert',
        'Beverages'
    ],
    'Description': [
        'Poached eggs with hollandaise sauce on an English muffin',
        'Fluffy pancakes loaded with fresh blueberries',
        'Smashed avocado on artisan bread with cherry tomatoes',
        'Grilled chicken breast with lettuce, tomato, and special sauce',
        'Traditional apple pie with a flaky, buttery crust',
        'Our house-roasted coffee blend with notes of chocolate and caramel'
    ],
    'Price': [12.99, 9.99, 11.99, 13.99, 6.99, 3.99],
    'Popularity Rank': [1, 2, 3, 4, 5, 6],
    'Image Filename': [
        'eggs_benedict.jpg',
        'blueberry_pancakes.jpg',
        'avocado_toast.jpg',
        'grilled_chicken_sandwich.jpg',
        'apple_pie.jpg',
        'signature_coffee.jpg'
    ],
    'Dietary Info': [
        'Vegetarian',
        'Vegetarian',
        'Vegan option available',
        'Gluten-free option available',
        'Contains nuts',
        'Vegan, Gluten-free'
    ],
    'Best For': [
        'Brunch special',
        'Weekend breakfast',
        'Health-conscious',
        'Lunch crowd',
        'Dessert lovers',
        'Daily essential'
    ]
}

# Create DataFrame
df = pd.DataFrame(sample_data)

# Save to Excel
output_path = 'data/restaurants/hults_cafe/popular_items.xlsx'
df.to_excel(output_path, index=False, sheet_name='Popular Items')

print(f"Sample Excel file created at: {output_path}")
print("\nExpected columns:")
print("- Item Name: Name of the dish")
print("- Category: Breakfast/Lunch/Dinner/Dessert/Beverages")
print("- Description: Brief description of the item")
print("- Price: Item price")
print("- Popularity Rank: Ranking (1 = most popular)")
print("- Image Filename: Name of the image file in the images folder")
print("- Dietary Info: Special dietary information")
print("- Best For: Target audience or occasion")
