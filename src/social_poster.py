"""
Social Media Poster Module
Handles posting content to Facebook, Instagram, and TikTok
"""
import json
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

import requests

from config import Config


class SocialMediaPoster:
    """Base class for social media posting"""

    def __init__(self):
        self.post_history = []

    def log_post(self, platform: str, post_id: str, content: Dict):
        """Log successful post"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "post_id": post_id,
            "content": content
        }
        self.post_history.append(log_entry)

    def save_post_history(self, output_path: Path):
        """Save post history to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.post_history, f, indent=2)


class FacebookPoster(SocialMediaPoster):
    """Handle Facebook posting via Graph API"""

    def __init__(self):
        super().__init__()
        self.access_token = Config.FACEBOOK_PAGE_ACCESS_TOKEN
        self.page_id = Config.FACEBOOK_PAGE_ID
        self.graph_api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"

    def post_photo(
        self,
        image_path: Path,
        caption: str,
        scheduled_time: Optional[int] = None
    ) -> Dict:
        """
        Post a photo to Facebook page

        Args:
            image_path: Path to image file
            caption: Post caption
            scheduled_time: Unix timestamp for scheduled post (optional)

        Returns:
            Dict with post_id and success status
        """
        if not self.access_token or not self.page_id:
            return {
                "success": False,
                "error": "Facebook credentials not configured"
            }

        url = f"{self.base_url}/{self.page_id}/photos"

        # Prepare the image
        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}

            params = {
                'access_token': self.access_token,
                'message': caption
            }

            if scheduled_time:
                params['published'] = 'false'
                params['scheduled_publish_time'] = scheduled_time

            try:
                response = requests.post(url, params=params, files=files)
                response.raise_for_status()

                result = response.json()

                if 'id' in result:
                    post_id = result['id']
                    self.log_post("facebook", post_id, {
                        "caption": caption,
                        "image": str(image_path),
                        "scheduled": scheduled_time is not None
                    })

                    return {
                        "success": True,
                        "post_id": post_id,
                        "platform": "facebook"
                    }
                else:
                    return {
                        "success": False,
                        "error": "No post ID returned",
                        "response": result
                    }

            except requests.exceptions.RequestException as e:
                return {
                    "success": False,
                    "error": str(e)
                }


class InstagramPoster(SocialMediaPoster):
    """Handle Instagram posting via Graph API"""

    def __init__(self):
        super().__init__()
        self.access_token = Config.FACEBOOK_PAGE_ACCESS_TOKEN
        self.instagram_account_id = Config.INSTAGRAM_BUSINESS_ACCOUNT_ID
        self.graph_api_version = "v18.0"
        self.base_url = f"https://graph.facebook.com/{self.graph_api_version}"

    def post_photo(
        self,
        image_url: str,
        caption: str
    ) -> Dict:
        """
        Post a photo to Instagram

        Note: Instagram requires images to be hosted at a publicly accessible URL
        For local files, you'll need to upload to a hosting service first

        Args:
            image_url: Public URL of the image
            caption: Post caption

        Returns:
            Dict with post_id and success status
        """
        if not self.access_token or not self.instagram_account_id:
            return {
                "success": False,
                "error": "Instagram credentials not configured"
            }

        # Step 1: Create container
        container_url = f"{self.base_url}/{self.instagram_account_id}/media"

        container_params = {
            'image_url': image_url,
            'caption': caption,
            'access_token': self.access_token
        }

        try:
            # Create container
            container_response = requests.post(container_url, params=container_params)
            container_response.raise_for_status()
            container_result = container_response.json()

            if 'id' not in container_result:
                return {
                    "success": False,
                    "error": "Failed to create media container",
                    "response": container_result
                }

            container_id = container_result['id']

            # Step 2: Publish container (wait a bit for processing)
            time.sleep(2)

            publish_url = f"{self.base_url}/{self.instagram_account_id}/media_publish"
            publish_params = {
                'creation_id': container_id,
                'access_token': self.access_token
            }

            publish_response = requests.post(publish_url, params=publish_params)
            publish_response.raise_for_status()
            publish_result = publish_response.json()

            if 'id' in publish_result:
                post_id = publish_result['id']
                self.log_post("instagram", post_id, {
                    "caption": caption,
                    "image_url": image_url
                })

                return {
                    "success": True,
                    "post_id": post_id,
                    "platform": "instagram"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to publish media",
                    "response": publish_result
                }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def post_local_photo(self, image_path: Path, caption: str) -> Dict:
        """
        Helper method for posting local files
        Note: This requires a separate image hosting solution

        For production use, you would:
        1. Upload image to S3/Cloudinary/etc.
        2. Get public URL
        3. Pass to post_photo()
        """
        return {
            "success": False,
            "error": "Instagram requires publicly accessible image URLs. "
                     "Please upload the image to a hosting service first.",
            "image_path": str(image_path)
        }


class TikTokPoster(SocialMediaPoster):
    """Handle TikTok posting via TikTok for Business API"""

    def __init__(self):
        super().__init__()
        self.access_token = Config.TIKTOK_ACCESS_TOKEN
        self.client_key = Config.TIKTOK_CLIENT_KEY
        self.base_url = "https://open-api.tiktok.com"

    def post_video(
        self,
        video_path: Path,
        caption: str,
        privacy_level: str = "PUBLIC_TO_EVERYONE"
    ) -> Dict:
        """
        Post a video to TikTok

        Args:
            video_path: Path to video file
            caption: Post caption
            privacy_level: Privacy setting (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY)

        Returns:
            Dict with post_id and success status
        """
        if not self.access_token:
            return {
                "success": False,
                "error": "TikTok credentials not configured"
            }

        # Note: TikTok API implementation varies by access level
        # This is a basic structure - actual implementation depends on API access tier

        return {
            "success": False,
            "error": "TikTok video posting requires additional API access and verification. "
                     "Please refer to TikTok for Developers documentation.",
            "note": "TikTok primarily supports video content. For images, consider creating "
                    "a short video slideshow using the image."
        }


class SocialMediaManager:
    """Unified manager for all social media platforms"""

    def __init__(self):
        self.facebook = FacebookPoster()
        self.instagram = InstagramPoster()
        self.tiktok = TikTokPoster()

    def post_to_platform(
        self,
        platform: str,
        content_package: Dict,
        dry_run: bool = False
    ) -> Dict:
        """
        Post content to specified platform

        Args:
            platform: 'facebook', 'instagram', or 'tiktok'
            content_package: Content data including image path and caption
            dry_run: If True, don't actually post (for testing)

        Returns:
            Dict with posting results
        """
        if dry_run:
            print(f"[DRY RUN] Would post to {platform}")
            print(f"Caption: {content_package['caption'][:100]}...")
            print(f"Image: {content_package['image_path']}")
            return {
                "success": True,
                "dry_run": True,
                "platform": platform
            }

        platform = platform.lower()

        if platform == "facebook":
            return self.facebook.post_photo(
                Path(content_package['image_path']),
                content_package['full_post']
            )

        elif platform == "instagram":
            # Instagram requires public URL
            # For now, return instruction
            return {
                "success": False,
                "error": "Instagram posting requires image to be uploaded to public URL first",
                "instruction": "Upload image to S3/Cloudinary and use the URL",
                "local_path": content_package['image_path']
            }

        elif platform == "tiktok":
            return self.tiktok.post_video(
                Path(content_package['image_path']),
                content_package['full_post']
            )

        else:
            return {
                "success": False,
                "error": f"Unknown platform: {platform}"
            }

    def post_to_all_platforms(
        self,
        content_packages: Dict,
        platforms: list = ["facebook", "instagram", "tiktok"],
        dry_run: bool = True
    ) -> Dict:
        """
        Post to multiple platforms

        Args:
            content_packages: Dict with platform-specific content
            platforms: List of platforms to post to
            dry_run: If True, simulate posting without actually posting

        Returns:
            Dict with results for each platform
        """
        results = {}

        for platform in platforms:
            if platform in content_packages:
                print(f"\nPosting to {platform}...")
                result = self.post_to_platform(
                    platform,
                    content_packages[platform],
                    dry_run=dry_run
                )
                results[platform] = result

                if result.get("success"):
                    print(f"  ✅ Successfully posted to {platform}")
                else:
                    print(f"  ❌ Failed to post to {platform}: {result.get('error')}")
            else:
                results[platform] = {
                    "success": False,
                    "error": f"No content package for {platform}"
                }

        return results


if __name__ == "__main__":
    # Test social media manager
    print("=" * 60)
    print("SOCIAL MEDIA POSTER TEST")
    print("=" * 60)

    manager = SocialMediaManager()

    # Test dry run
    test_content = {
        "facebook": {
            "caption": "Delicious test post!",
            "full_post": "Delicious test post! #food #restaurant",
            "image_path": "/path/to/test/image.jpg"
        }
    }

    print("\nTesting dry run...")
    results = manager.post_to_all_platforms(
        test_content,
        platforms=["facebook"],
        dry_run=True
    )

    print("\nResults:")
    print(json.dumps(results, indent=2))

    print("\n" + "=" * 60)
    print("Note: To post for real, ensure:")
    print("1. API credentials are set in .env")
    print("2. Set dry_run=False")
    print("3. For Instagram: Upload images to public URL first")
    print("=" * 60)
