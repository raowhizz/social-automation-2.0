# Social Media Automation for Restaurants

Automated social media content generation and posting system for restaurants using AI. Creates engaging posts with beautiful images and compelling captions for Facebook, Instagram, and TikTok.

## Features

- **AI-Powered Content Generation**: Uses GPT-4 Vision to analyze dish images and generate appetizing captions
- **Multi-Platform Support**: Facebook, Instagram, and TikTok
- **Campaign Management**: Pre-built templates for Thanksgiving, holidays, weekends, and daily specials
- **Smart Image Processing**: Automatic text overlays and platform-specific formatting
- **Restaurant-Specific Branding**: Customizable brand voice and messaging
- **Batch Processing**: Generate content for multiple menu items at once

## Project Structure

```
social-automation/
├── data/
│   └── restaurants/
│       └── hults_cafe/              # Example restaurant
│           ├── images/              # Dish photos
│           ├── popular_items.xlsx   # Menu items data
│           └── restaurant_brief.txt # Restaurant info & branding
├── output/
│   └── hults_cafe/
│       ├── generated_content/       # AI-generated images
│       └── posted/                  # Post history
├── src/
│   ├── config.py                    # Configuration management
│   ├── content_generator.py         # AI content generation
│   ├── social_poster.py             # Social media APIs
│   └── campaign_manager.py          # Campaign templates
├── templates/                       # Campaign templates
├── main.py                          # Main orchestration script
├── requirements.txt                 # Python dependencies
└── .env                             # API keys (create from .env.example)
```

## Installation

### 1. Prerequisites

- Python 3.8 or higher
- pip package manager

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required: OPENAI_API_KEY
# Optional: Facebook, Instagram, TikTok credentials
```

## Quick Start

### Step 1: Prepare Restaurant Data

For each restaurant, create a folder structure:

```
data/restaurants/your_restaurant_name/
├── images/                    # Put dish photos here
├── popular_items.xlsx         # Excel with menu items
└── restaurant_brief.txt       # Restaurant description
```

**Example Excel Format** (`popular_items.xlsx`):

| Item Name | Category | Description | Price | Popularity Rank | Image Filename | Dietary Info | Best For |
|-----------|----------|-------------|-------|-----------------|----------------|--------------|----------|
| Eggs Benedict | Breakfast | Poached eggs with hollandaise | 12.99 | 1 | eggs_benedict.jpg | Vegetarian | Brunch special |
| Blueberry Pancakes | Breakfast | Fluffy pancakes with blueberries | 9.99 | 2 | blueberry_pancakes.jpg | Vegetarian | Weekend breakfast |

**Example Restaurant Brief** (`restaurant_brief.txt`):

```
RESTAURANT BRIEF: YOUR RESTAURANT NAME

Restaurant Name: Your Restaurant
Cuisine Type: American Cafe
Brand Voice: Warm, friendly, community-focused

Specialty: Fresh, quality ingredients and homestyle cooking
Target Audience: Local families, working professionals

Social Media Goals:
- Showcase menu items with appetizing visuals
- Drive foot traffic and online orders
- Build community engagement
```

### Step 2: Validate Setup

```bash
python main.py --restaurant hults_cafe --validate
```

This checks:
- ✅ API keys are configured
- ✅ Restaurant data files exist
- ✅ Images directory is set up

### Step 3: Generate Content (Dry Run)

```bash
# Generate content for top 3 items with Thanksgiving theme
python main.py --restaurant hults_cafe --campaign "Thanksgiving 2024" --items 3
```

This will:
1. Analyze dish images with GPT-4 Vision
2. Generate platform-specific captions
3. Create images with text overlays
4. Save everything to `output/hults_cafe/generated_content/`

### Step 4: Review Generated Content

Check the output directory:
- Images with text overlays
- `content_summary_[timestamp].json` with all captions and metadata

### Step 5: Post to Social Media (Optional)

```bash
# Actually post to Facebook and Instagram
python main.py --restaurant hults_cafe --campaign "Thanksgiving 2024" --items 3 --post
```

⚠️ **Note**: Remove `--post` flag to run in dry-run mode (recommended for testing)

## Usage Examples

### Generate Thanksgiving Content

```bash
python main.py \
  --restaurant hults_cafe \
  --campaign "Thanksgiving 2024" \
  --items 5 \
  --platforms facebook instagram
```

### Generate Weekend Special

```bash
python main.py \
  --restaurant hults_cafe \
  --campaign "Weekend Special" \
  --items 3 \
  --platforms facebook instagram tiktok
```

### Post to Facebook Only

```bash
python main.py \
  --restaurant hults_cafe \
  --campaign "Daily Special" \
  --platforms facebook \
  --post
```

## Available Campaigns

The system includes pre-built campaign templates:

- **Thanksgiving 2024**: Holiday-themed content (Nov 14-28)
- **Weekend Special**: Weekend promotions (Fri-Sun)
- **Daily Special**: Fresh daily content

### Creating Custom Campaigns

Edit campaign templates in `templates/` directory:

```json
{
  "name": "Summer Special 2024",
  "description": "Fresh summer flavors!",
  "start_date": "2024-06-01T00:00:00",
  "end_date": "2024-08-31T23:59:59",
  "theme": "Fresh, Light, Seasonal",
  "keywords": [
    "Summer freshness",
    "Light and delicious",
    "Perfect for summer"
  ],
  "target_items": [
    "Salads",
    "Smoothies",
    "Cold beverages"
  ]
}
```

## API Setup Guides

### OpenAI API (Required)

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

**Cost Estimate**: ~$0.05-0.10 per image analysis + caption generation

### Facebook & Instagram (Meta Graph API)

1. Create Facebook Developer account: https://developers.facebook.com/
2. Create a new app
3. Add "Instagram" product
4. Generate Page Access Token
5. Get Page ID from Facebook page settings
6. Get Instagram Business Account ID from Graph API Explorer

Add to `.env`:
```
FACEBOOK_PAGE_ACCESS_TOKEN=...
FACEBOOK_PAGE_ID=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
```

**Note**: Instagram requires images to be hosted at a public URL (e.g., S3, Cloudinary)

### TikTok API (Optional)

TikTok API requires business verification. See: https://developers.tiktok.com/

## Command Line Options

```
python main.py [OPTIONS]

Required:
  --restaurant SLUG        Restaurant identifier (e.g., hults_cafe)

Optional:
  --campaign NAME          Campaign name (e.g., "Thanksgiving 2024")
  --items N                Number of items to feature (default: 3)
  --platforms [LIST]       Platforms: facebook instagram tiktok (default: facebook instagram)
  --post                   Actually post (default: dry run)
  --validate               Validate setup only
```

## Development & Testing

### Test Individual Modules

```bash
# Test configuration
python src/config.py

# Test content generator
python src/content_generator.py

# Test social poster
python src/social_poster.py

# Test campaign manager
python src/campaign_manager.py
```

### Create Sample Data

```bash
# Generate sample Excel template
python create_sample_excel.py
```

## Scaling to Multiple Restaurants

### Option 1: Sequential Processing

```bash
for restaurant in hults_cafe another_cafe third_restaurant; do
  python main.py --restaurant $restaurant --campaign "Thanksgiving 2024" --items 3 --post
done
```

### Option 2: Batch Script

Create `batch_process.py`:

```python
restaurants = ["hults_cafe", "another_cafe", "third_restaurant"]
campaign = "Thanksgiving 2024"

for restaurant_slug in restaurants:
    content = generate_content(restaurant_slug, campaign, num_items=3)
    post_content(content, dry_run=False)
```

## Best Practices

### Image Guidelines

- **Resolution**: Minimum 1080x1080px (Instagram), 1200x630px (Facebook)
- **Quality**: High-quality photos with good lighting
- **Composition**: Food should be the main focus
- **File Format**: JPEG or PNG
- **File Naming**: `dish_name.jpg` (lowercase, underscores)

### Content Strategy

1. **Frequency**: 3-5 posts per week
2. **Timing**:
   - Breakfast posts: 7-9 AM
   - Lunch posts: 11 AM-1 PM
   - Dinner posts: 5-7 PM
3. **Variety**: Mix of menu items, specials, and seasonal content
4. **Engagement**: Monitor comments and respond promptly

### Cost Optimization

- **Batch Processing**: Generate multiple items at once to save API calls
- **Reuse Analysis**: Cache GPT-4 Vision results for similar images
- **Template Refinement**: Improve prompts to reduce regeneration needs

## Troubleshooting

### "Images directory not found"

Create the images folder:
```bash
mkdir -p data/restaurants/your_restaurant/images
```

### "OpenAI API key not set"

Add your API key to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### "Failed to post to Instagram"

Instagram requires publicly accessible image URLs. Upload images to:
- AWS S3
- Cloudinary
- Google Cloud Storage
- Any CDN

Then modify `social_poster.py` to use the public URL.

### Font not found errors

The system tries to use system fonts. If unavailable, it falls back to default fonts.
To use custom fonts, update `src/config.py`:

```python
FONT_PATH = "/path/to/your/font.ttf"
```

## Roadmap

- [ ] Video generation for TikTok
- [ ] Automated scheduling with cron jobs
- [ ] Analytics dashboard
- [ ] A/B testing for captions
- [ ] Multi-language support
- [ ] Hashtag optimization
- [ ] Engagement tracking

## Security Notes

- **Never commit `.env` file** - Contains sensitive API keys
- **Rotate API keys regularly** - Especially for production use
- **Use environment-specific keys** - Separate keys for dev/staging/production
- **Monitor API usage** - Set up billing alerts in OpenAI dashboard

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API documentation (OpenAI, Meta, TikTok)
3. Check `output/` directory for error logs

## License

This project is for Innowi internal use.

---

**Built for Innowi** - Automating restaurant social media, one post at a time 🍽️
