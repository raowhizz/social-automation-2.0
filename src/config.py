"""
Configuration module for social media automation
Handles restaurant-specific settings and API credentials
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration"""

    # Project paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data" / "restaurants"
    OUTPUT_DIR = BASE_DIR / "output"
    TEMPLATES_DIR = BASE_DIR / "templates"

    # API Keys (loaded from .env)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Facebook/Instagram (Meta) API
    FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

    # TikTok API
    TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN")
    TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
    TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")

    # Image generation settings
    DEFAULT_IMAGE_SIZE = (1080, 1080)  # Square for Instagram
    INSTAGRAM_PORTRAIT_SIZE = (1080, 1350)
    FACEBOOK_LANDSCAPE_SIZE = (1200, 630)
    TIKTOK_VERTICAL_SIZE = (1080, 1920)

    # AI Model settings
    GPT_MODEL = "gpt-4-turbo-preview"
    GPT_VISION_MODEL = "gpt-4o"  # Updated: gpt-4-vision-preview deprecated
    DALLE_MODEL = "dall-e-3"

    # Content generation settings
    MAX_CAPTION_LENGTH = 2200  # Instagram limit
    MAX_HASHTAGS = 30  # Instagram limit

    # Text overlay settings
    FONT_SIZE_TITLE = 72
    FONT_SIZE_SUBTITLE = 48
    FONT_COLOR = (255, 255, 255)  # White
    FONT_OUTLINE_COLOR = (0, 0, 0)  # Black outline
    OVERLAY_OPACITY = 0.3  # For background overlay


class RestaurantConfig:
    """Restaurant-specific configuration"""

    def __init__(self, restaurant_slug: str):
        self.slug = restaurant_slug
        self.data_dir = Config.DATA_DIR / restaurant_slug
        self.output_dir = Config.OUTPUT_DIR / restaurant_slug

        # Ensure output directories exist
        (self.output_dir / "generated_content").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "posted").mkdir(parents=True, exist_ok=True)

        # Data file paths
        self.images_dir = self.data_dir / "images"
        self.popular_items_file = self.data_dir / "popular_items.xlsx"
        self.restaurant_brief_file = self.data_dir / "restaurant_brief.txt"

        # Load restaurant brief
        self.restaurant_brief = self._load_restaurant_brief()

    def _load_restaurant_brief(self) -> str:
        """Load restaurant brief from text file"""
        if self.restaurant_brief_file.exists():
            with open(self.restaurant_brief_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def get_image_path(self, filename: str) -> Path:
        """Get full path to an image file"""
        return self.images_dir / filename

    def get_output_path(self, filename: str, subfolder: str = "generated_content") -> Path:
        """Get full path for output file"""
        return self.output_dir / subfolder / filename

    def validate_data(self) -> dict:
        """Validate that all required data files exist"""
        validation = {
            "images_dir_exists": self.images_dir.exists(),
            "popular_items_exists": self.popular_items_file.exists(),
            "restaurant_brief_exists": self.restaurant_brief_file.exists(),
            "errors": []
        }

        if not validation["images_dir_exists"]:
            validation["errors"].append(f"Images directory not found: {self.images_dir}")

        if not validation["popular_items_exists"]:
            validation["errors"].append(f"Popular items Excel not found: {self.popular_items_file}")

        if not validation["restaurant_brief_exists"]:
            validation["errors"].append(f"Restaurant brief not found: {self.restaurant_brief_file}")

        validation["is_valid"] = len(validation["errors"]) == 0
        return validation


class PlatformConfig:
    """Platform-specific configuration for social media posts"""

    FACEBOOK = {
        "name": "Facebook",
        "image_size": Config.FACEBOOK_LANDSCAPE_SIZE,
        "max_caption_length": 63206,  # Very high limit
        "supports_carousel": True,
        "supports_video": True,
        "aspect_ratios": ["16:9", "1:1", "4:5"]
    }

    INSTAGRAM = {
        "name": "Instagram",
        "image_size": Config.INSTAGRAM_PORTRAIT_SIZE,
        "max_caption_length": 2200,
        "supports_carousel": True,
        "supports_video": True,
        "aspect_ratios": ["1:1", "4:5", "9:16"]
    }

    TIKTOK = {
        "name": "TikTok",
        "image_size": Config.TIKTOK_VERTICAL_SIZE,
        "max_caption_length": 2200,
        "supports_carousel": False,
        "supports_video": True,
        "aspect_ratios": ["9:16"],
        "preferred_format": "video"
    }

    @classmethod
    def get_platform_config(cls, platform: str) -> dict:
        """Get configuration for a specific platform"""
        platform_map = {
            "facebook": cls.FACEBOOK,
            "instagram": cls.INSTAGRAM,
            "tiktok": cls.TIKTOK
        }
        return platform_map.get(platform.lower(), cls.INSTAGRAM)


def validate_api_keys() -> dict:
    """Validate that required API keys are set"""
    validation = {
        "openai": bool(Config.OPENAI_API_KEY),
        "facebook": bool(Config.FACEBOOK_PAGE_ACCESS_TOKEN),
        "instagram": bool(Config.INSTAGRAM_BUSINESS_ACCOUNT_ID),
        "tiktok": bool(Config.TIKTOK_ACCESS_TOKEN),
        "errors": []
    }

    if not validation["openai"]:
        validation["errors"].append("OPENAI_API_KEY not set in .env file")

    if not validation["facebook"]:
        validation["errors"].append("FACEBOOK_PAGE_ACCESS_TOKEN not set in .env file")

    validation["is_valid"] = len(validation["errors"]) == 0
    return validation


if __name__ == "__main__":
    # Test configuration
    print("=" * 60)
    print("CONFIGURATION TEST")
    print("=" * 60)

    # Test API keys
    print("\nAPI Keys Validation:")
    api_validation = validate_api_keys()
    for key, status in api_validation.items():
        if key != "errors" and key != "is_valid":
            print(f"  {key}: {'✓' if status else '✗'}")

    if api_validation["errors"]:
        print("\nErrors:")
        for error in api_validation["errors"]:
            print(f"  - {error}")

    # Test restaurant config
    print("\nRestaurant Configuration (hults_cafe):")
    restaurant = RestaurantConfig("hults_cafe")
    print(f"  Data directory: {restaurant.data_dir}")
    print(f"  Output directory: {restaurant.output_dir}")

    validation = restaurant.validate_data()
    print(f"\n  Images directory: {'✓' if validation['images_dir_exists'] else '✗'}")
    print(f"  Popular items Excel: {'✓' if validation['popular_items_exists'] else '✗'}")
    print(f"  Restaurant brief: {'✓' if validation['restaurant_brief_exists'] else '✗'}")

    if validation["errors"]:
        print("\n  Errors:")
        for error in validation["errors"]:
            print(f"    - {error}")

    print("\n" + "=" * 60)
