"""
Content Generator Module
Handles AI-powered content creation including:
- Image analysis using GPT-4 Vision
- Caption generation
- Text overlay on images
- Platform-specific image formatting
"""
import base64
import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import pandas as pd
from openai import OpenAI

from config import Config, RestaurantConfig, PlatformConfig


class ContentGenerator:
    """Generates social media content using AI"""

    def __init__(self, restaurant_config: RestaurantConfig):
        self.restaurant = restaurant_config
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def load_popular_items(self, top_n: Optional[int] = None) -> pd.DataFrame:
        """Load popular items from Excel file"""
        df = pd.read_excel(self.restaurant.popular_items_file)

        # Sort by popularity rank
        df = df.sort_values('Popularity Rank')

        if top_n:
            df = df.head(top_n)

        return df

    def encode_image_to_base64(self, image_path: Path) -> str:
        """Encode image to base64 for OpenAI API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_dish_image(self, image_path: Path, item_info: Dict) -> str:
        """Use GPT-4 Vision to analyze a dish image and generate insights"""
        base64_image = self.encode_image_to_base64(image_path)

        prompt = f"""
        Analyze this image of {item_info['Item Name']} from a restaurant.

        Dish Information:
        - Name: {item_info['Item Name']}
        - Category: {item_info['Category']}
        - Description: {item_info['Description']}
        - Price: ${item_info['Price']}
        - Dietary Info: {item_info.get('Dietary Info', 'N/A')}

        Please provide:
        1. Visual appeal description (colors, presentation, plating)
        2. Key ingredients visible in the image
        3. What makes this dish look appetizing
        4. Suggested emotional appeal (comfort, excitement, indulgence, health, etc.)
        5. Best angle/composition notes

        Keep it concise and focused on social media appeal.
        """

        response = self.client.chat.completions.create(
            model=Config.GPT_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )

        return response.choices[0].message.content

    def generate_caption(
        self,
        item_info: Dict,
        image_analysis: str,
        campaign_context: str,
        platform: str = "instagram"
    ) -> Dict[str, str]:
        """Generate social media caption using GPT-4"""
        platform_config = PlatformConfig.get_platform_config(platform)
        max_length = platform_config["max_caption_length"]

        prompt = f"""
        Create an engaging social media caption for {platform.capitalize()}.

        RESTAURANT CONTEXT:
        {self.restaurant.restaurant_brief}

        CAMPAIGN CONTEXT:
        {campaign_context}

        DISH DETAILS:
        - Name: {item_info['Item Name']}
        - Category: {item_info['Category']}
        - Description: {item_info['Description']}
        - Price: ${item_info['Price']}
        - Best For: {item_info.get('Best For', 'N/A')}

        IMAGE ANALYSIS:
        {image_analysis}

        REQUIREMENTS:
        1. Create a compelling, appetizing caption (max {max_length} characters)
        2. Match the restaurant's brand voice (warm, friendly, community-focused)
        3. Incorporate the campaign context naturally
        4. Include a clear call-to-action
        5. Suggest 5-8 relevant hashtags
        6. Keep it authentic and engaging

        FORMAT YOUR RESPONSE AS:
        CAPTION:
        [Your caption here]

        HASHTAGS:
        #hashtag1 #hashtag2 #hashtag3 ...

        SHORT_TEXT_OVERLAY:
        [2-4 word catchy phrase for image overlay]
        """

        response = self.client.chat.completions.create(
            model=Config.GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a creative social media content writer specializing in food and restaurant marketing."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=800,
            temperature=0.8
        )

        content = response.choices[0].message.content

        # Parse the response
        caption = ""
        hashtags = ""
        text_overlay = ""

        lines = content.split('\n')
        section = None

        for line in lines:
            line = line.strip()
            if line.startswith('CAPTION:'):
                section = 'caption'
                continue
            elif line.startswith('HASHTAGS:'):
                section = 'hashtags'
                hashtags = line.replace('HASHTAGS:', '').strip()
                continue
            elif line.startswith('SHORT_TEXT_OVERLAY:'):
                section = 'text_overlay'
                text_overlay = line.replace('SHORT_TEXT_OVERLAY:', '').strip()
                continue

            if section == 'caption' and line:
                caption += line + '\n'

        return {
            "caption": caption.strip(),
            "hashtags": hashtags,
            "text_overlay": text_overlay,
            "full_post": f"{caption.strip()}\n\n{hashtags}"
        }

    def add_text_overlay(
        self,
        image_path: Path,
        text: str,
        subtitle: Optional[str] = None,
        output_path: Optional[Path] = None,
        position: str = "bottom"
    ) -> Path:
        """Add text overlay to an image"""
        # Load image
        img = Image.open(image_path)
        img = img.convert('RGBA')

        # Create a semi-transparent overlay
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Calculate overlay dimensions
        img_width, img_height = img.size
        overlay_height = img_height // 3

        if position == "bottom":
            overlay_y = img_height - overlay_height
        elif position == "top":
            overlay_y = 0
        else:  # center
            overlay_y = (img_height - overlay_height) // 2

        # Draw semi-transparent rectangle
        overlay_alpha = int(255 * Config.OVERLAY_OPACITY)
        draw.rectangle(
            [(0, overlay_y), (img_width, overlay_y + overlay_height)],
            fill=(0, 0, 0, overlay_alpha)
        )

        # Composite overlay onto image
        img = Image.alpha_composite(img, overlay)

        # Add text
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fall back to default if not available
        try:
            title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", Config.FONT_SIZE_TITLE)
            subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", Config.FONT_SIZE_SUBTITLE)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()

        # Draw main text
        # Get text bounding box for centering
        bbox = draw.textbbox((0, 0), text, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = (img_width - text_width) // 2
        text_y = overlay_y + (overlay_height - text_height) // 2

        if subtitle:
            text_y -= 30  # Move title up a bit

        # Draw text with outline for better visibility
        outline_range = 3
        for adj_x in range(-outline_range, outline_range + 1):
            for adj_y in range(-outline_range, outline_range + 1):
                draw.text(
                    (text_x + adj_x, text_y + adj_y),
                    text,
                    font=title_font,
                    fill=Config.FONT_OUTLINE_COLOR
                )

        # Draw main text
        draw.text((text_x, text_y), text, font=title_font, fill=Config.FONT_COLOR)

        # Draw subtitle if provided
        if subtitle:
            bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            sub_width = bbox[2] - bbox[0]
            sub_x = (img_width - sub_width) // 2
            sub_y = text_y + text_height + 10

            # Outline
            for adj_x in range(-2, 3):
                for adj_y in range(-2, 3):
                    draw.text(
                        (sub_x + adj_x, sub_y + adj_y),
                        subtitle,
                        font=subtitle_font,
                        fill=Config.FONT_OUTLINE_COLOR
                    )

            draw.text((sub_x, sub_y), subtitle, font=subtitle_font, fill=Config.FONT_COLOR)

        # Convert back to RGB
        img = img.convert('RGB')

        # Save
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{image_path.stem}_overlay_{timestamp}.jpg"
            output_path = self.restaurant.get_output_path(filename)

        img.save(output_path, quality=95)
        return output_path

    def resize_for_platform(
        self,
        image_path: Path,
        platform: str,
        output_path: Optional[Path] = None
    ) -> Path:
        """Resize image for specific social media platform"""
        platform_config = PlatformConfig.get_platform_config(platform)
        target_size = platform_config["image_size"]

        img = Image.open(image_path)

        # Calculate scaling to maintain aspect ratio
        img_ratio = img.width / img.height
        target_ratio = target_size[0] / target_size[1]

        if img_ratio > target_ratio:
            # Image is wider, scale by height
            new_height = target_size[1]
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller, scale by width
            new_width = target_size[0]
            new_height = int(new_width / img_ratio)

        # Resize
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Crop to target size (center crop)
        left = (new_width - target_size[0]) // 2
        top = (new_height - target_size[1]) // 2
        right = left + target_size[0]
        bottom = top + target_size[1]

        img = img.crop((left, top, right, bottom))

        # Save
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{image_path.stem}_{platform}_{timestamp}.jpg"
            output_path = self.restaurant.get_output_path(filename)

        img.save(output_path, quality=95)
        return output_path

    def generate_content_for_item(
        self,
        item_info: Dict,
        campaign_context: str,
        platforms: List[str] = ["instagram", "facebook", "tiktok"]
    ) -> Dict:
        """Generate complete content package for a menu item"""
        print(f"\nGenerating content for: {item_info['Item Name']}")

        # Get image path
        image_filename = item_info['Image Filename']
        image_path = self.restaurant.get_image_path(image_filename)

        if not image_path.exists():
            print(f"  ⚠️  Warning: Image not found: {image_path}")
            return None

        # Step 1: Analyze image
        print("  📸 Analyzing image with GPT-4 Vision...")
        image_analysis = self.analyze_dish_image(image_path, item_info)

        # Step 2: Generate captions for each platform
        content_package = {
            "item_name": item_info['Item Name'],
            "original_image": str(image_path),
            "image_analysis": image_analysis,
            "platforms": {}
        }

        for platform in platforms:
            print(f"  ✍️  Generating {platform} content...")

            caption_data = self.generate_caption(
                item_info,
                image_analysis,
                campaign_context,
                platform
            )

            # Create image with overlay
            text_overlay = caption_data['text_overlay']
            subtitle = f"${item_info['Price']}"

            overlay_image = self.add_text_overlay(
                image_path,
                text_overlay,
                subtitle,
                position="bottom"
            )

            # Resize for platform
            platform_image = self.resize_for_platform(
                overlay_image,
                platform
            )

            content_package["platforms"][platform] = {
                "caption": caption_data['caption'],
                "hashtags": caption_data['hashtags'],
                "full_post": caption_data['full_post'],
                "image_path": str(platform_image)
            }

            print(f"  ✅ {platform.capitalize()} content ready: {platform_image.name}")

        return content_package


if __name__ == "__main__":
    # Test content generator
    print("=" * 60)
    print("CONTENT GENERATOR TEST")
    print("=" * 60)

    # Initialize
    restaurant = RestaurantConfig("hults_cafe")
    generator = ContentGenerator(restaurant)

    # Test loading popular items
    print("\nLoading popular items...")
    items = generator.load_popular_items(top_n=1)
    print(f"Loaded {len(items)} items")

    if len(items) > 0:
        print("\nFirst item:")
        print(items.iloc[0].to_dict())

    print("\n" + "=" * 60)
    print("Note: To test full content generation, ensure:")
    print("1. OPENAI_API_KEY is set in .env")
    print("2. Images exist in data/restaurants/hults_cafe/images/")
    print("=" * 60)
