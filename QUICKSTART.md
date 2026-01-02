# Quick Start Guide

Get your first social media post generated in 5 minutes!

## Step 1: Install (1 minute)

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment file
cp .env.example .env
```

## Step 2: Add Your OpenAI API Key (1 minute)

Edit `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
```

Get your API key from: https://platform.openai.com/api-keys

## Step 3: Prepare Your Restaurant Data (2 minutes)

### Option A: Use the Sample Data (Fastest)

Sample data for "hults_cafe" is already included!

Just add some images:
```bash
# Add your dish photos to:
data/restaurants/hults_cafe/images/

# Name them to match the Excel file:
# - eggs_benedict.jpg
# - blueberry_pancakes.jpg
# - avocado_toast.jpg
# etc.
```

### Option B: Create Your Own Restaurant

```bash
# 1. Create your restaurant folder
mkdir -p data/restaurants/my_restaurant/images

# 2. Copy the sample files
cp data/restaurants/hults_cafe/popular_items.xlsx data/restaurants/my_restaurant/
cp data/restaurants/hults_cafe/restaurant_brief.txt data/restaurants/my_restaurant/

# 3. Edit the files with your restaurant's info

# 4. Add your dish images
# Copy your photos to: data/restaurants/my_restaurant/images/
```

## Step 4: Validate Setup (30 seconds)

```bash
python main.py --restaurant hults_cafe --validate
```

You should see:
```
✅ OpenAI API key configured
✅ Images directory exists
✅ Popular items Excel file exists
✅ Restaurant brief exists
```

## Step 5: Generate Your First Post! (30 seconds)

```bash
python main.py \
  --restaurant hults_cafe \
  --campaign "Thanksgiving 2024" \
  --items 3
```

This will:
1. Analyze your top 3 dish images with AI
2. Generate compelling captions
3. Create beautiful images with text overlays
4. Save everything to `output/hults_cafe/generated_content/`

## What You Get

Check the `output/hults_cafe/generated_content/` folder:

- **Images**: Beautiful photos with text overlays and pricing
- **content_summary_[timestamp].json**: All captions and metadata

Example output:
```
output/hults_cafe/generated_content/
├── eggs_benedict_overlay_20241116_143022.jpg
├── eggs_benedict_instagram_20241116_143023.jpg
├── eggs_benedict_facebook_20241116_143024.jpg
├── blueberry_pancakes_overlay_20241116_143025.jpg
└── content_summary_20241116_143026.json
```

## Next Steps

### View the Generated Content

Open the images in the `output/` folder to see your AI-generated posts!

### Try Different Campaigns

```bash
# Weekend special
python main.py --restaurant hults_cafe --campaign "Weekend Special" --items 3

# Daily special
python main.py --restaurant hults_cafe --campaign "Daily Special" --items 2
```

### Post to Social Media (When Ready)

```bash
# First, add Facebook credentials to .env
# Then run with --post flag:
python main.py \
  --restaurant hults_cafe \
  --campaign "Thanksgiving 2024" \
  --items 3 \
  --platforms facebook \
  --post
```

## Common Issues

### "OpenAI API key not set"
→ Add your API key to the `.env` file

### "Images directory not found"
→ Create it: `mkdir -p data/restaurants/hults_cafe/images`

### "Image not found: eggs_benedict.jpg"
→ Add the image file to `data/restaurants/hults_cafe/images/`

### Need help?
→ Check the full README.md for detailed documentation

## Example: Complete Workflow for Thanksgiving

```bash
# 1. Validate
python main.py --restaurant hults_cafe --validate

# 2. Generate content (dry run)
python main.py --restaurant hults_cafe --campaign "Thanksgiving 2024" --items 5

# 3. Review the generated content in output/ folder

# 4. If happy, post to Facebook
python main.py --restaurant hults_cafe --campaign "Thanksgiving 2024" --items 5 --platforms facebook --post
```

---

That's it! You're ready to automate your restaurant's social media! 🎉

For more details, see the full [README.md](README.md)
