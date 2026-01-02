"""
Campaign Manager Module
Handles campaign templates and scheduling for different occasions
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class Campaign:
    """Represents a marketing campaign"""

    def __init__(
        self,
        name: str,
        description: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        theme: str = "",
        keywords: List[str] = None,
        target_items: List[str] = None
    ):
        self.name = name
        self.description = description
        self.start_date = start_date or datetime.now()
        self.end_date = end_date or (datetime.now() + timedelta(days=7))
        self.theme = theme
        self.keywords = keywords or []
        self.target_items = target_items or []

    def get_context_prompt(self) -> str:
        """Generate campaign context for AI content generation"""
        context = f"""
        CAMPAIGN: {self.name}

        {self.description}

        THEME: {self.theme}

        KEY MESSAGING:
        {chr(10).join('- ' + kw for kw in self.keywords)}

        CAMPAIGN DATES: {self.start_date.strftime('%B %d, %Y')} - {self.end_date.strftime('%B %d, %Y')}
        """

        if self.target_items:
            context += f"\n\nFEATURED ITEMS: {', '.join(self.target_items)}"

        return context.strip()

    def is_active(self) -> bool:
        """Check if campaign is currently active"""
        now = datetime.now()
        return self.start_date <= now <= self.end_date

    def to_dict(self) -> Dict:
        """Convert campaign to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "theme": self.theme,
            "keywords": self.keywords,
            "target_items": self.target_items
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Campaign':
        """Create campaign from dictionary"""
        start_date = datetime.fromisoformat(data['start_date']) if data.get('start_date') else None
        end_date = datetime.fromisoformat(data['end_date']) if data.get('end_date') else None

        return cls(
            name=data['name'],
            description=data['description'],
            start_date=start_date,
            end_date=end_date,
            theme=data.get('theme', ''),
            keywords=data.get('keywords', []),
            target_items=data.get('target_items', [])
        )


class CampaignManager:
    """Manages campaign templates and scheduling"""

    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        self.campaigns = {}
        self.load_templates()

    def load_templates(self):
        """Load all campaign templates from templates directory"""
        if not self.templates_dir.exists():
            return

        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template_data = json.load(f)

                campaign = Campaign.from_dict(template_data)
                self.campaigns[campaign.name] = campaign
                print(f"Loaded campaign: {campaign.name}")

            except Exception as e:
                print(f"Error loading template {template_file}: {e}")

    def get_campaign(self, name: str) -> Optional[Campaign]:
        """Get campaign by name"""
        return self.campaigns.get(name)

    def get_active_campaigns(self) -> List[Campaign]:
        """Get all currently active campaigns"""
        return [c for c in self.campaigns.values() if c.is_active()]

    def create_campaign_template(
        self,
        campaign: Campaign,
        output_path: Optional[Path] = None
    ):
        """Save campaign as a template"""
        if not output_path:
            filename = f"{campaign.name.lower().replace(' ', '_')}.json"
            output_path = self.templates_dir / filename

        self.templates_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(campaign.to_dict(), f, indent=2)

        print(f"Campaign template saved: {output_path}")

    def list_campaigns(self) -> List[str]:
        """List all available campaigns"""
        return list(self.campaigns.keys())


# Predefined campaign templates
def create_thanksgiving_campaign() -> Campaign:
    """Create Thanksgiving campaign template"""
    # Calculate Thanksgiving date (4th Thursday of November)
    now = datetime.now()
    year = now.year if now.month <= 11 else now.year + 1

    # Find 4th Thursday of November
    nov_1 = datetime(year, 11, 1)
    days_until_thursday = (3 - nov_1.weekday()) % 7
    first_thursday = nov_1 + timedelta(days=days_until_thursday)
    thanksgiving = first_thursday + timedelta(weeks=3)

    # Campaign runs 2 weeks before through the day of Thanksgiving
    start_date = thanksgiving - timedelta(days=14)
    end_date = thanksgiving

    return Campaign(
        name="Thanksgiving 2024",
        description="Celebrate Thanksgiving with our special dishes perfect for the holiday season. "
                    "Warm, comforting meals that bring families together.",
        start_date=start_date,
        end_date=end_date,
        theme="Gratitude, Family, Comfort Food, Tradition, Warmth",
        keywords=[
            "Perfect for your Thanksgiving celebration",
            "Bring the family together with comfort food",
            "Grateful for our community",
            "Traditional flavors, made with love",
            "Your Thanksgiving feast starts here",
            "Warm, hearty, and delicious",
            "Pre-order for Thanksgiving",
            "Thanksgiving specials available now"
        ],
        target_items=[
            "Turkey dishes",
            "Stuffing",
            "Mashed potatoes",
            "Pumpkin pie",
            "Cranberry items",
            "Comfort food classics"
        ]
    )


def create_holiday_season_campaign() -> Campaign:
    """Create general holiday season campaign"""
    now = datetime.now()
    year = now.year if now.month <= 12 else now.year + 1

    start_date = datetime(year, 12, 1)
    end_date = datetime(year, 12, 31)

    return Campaign(
        name="Holiday Season 2024",
        description="Celebrate the holiday season with special treats and festive favorites.",
        start_date=start_date,
        end_date=end_date,
        theme="Joy, Celebration, Festivity, Togetherness",
        keywords=[
            "Holiday specials",
            "Festive flavors",
            "Perfect for holiday gatherings",
            "Season's greetings from our kitchen",
            "Make your holidays delicious",
            "Holiday catering available"
        ]
    )


def create_weekend_special_campaign() -> Campaign:
    """Create recurring weekend special campaign"""
    # This weekend
    now = datetime.now()
    days_until_friday = (4 - now.weekday()) % 7
    if days_until_friday == 0 and now.hour >= 17:
        days_until_friday = 7

    friday = now + timedelta(days=days_until_friday)
    sunday = friday + timedelta(days=2)

    return Campaign(
        name="Weekend Special",
        description="Weekend vibes call for delicious food! Check out our weekend favorites.",
        start_date=friday.replace(hour=17, minute=0, second=0),
        end_date=sunday.replace(hour=23, minute=59, second=59),
        theme="Relaxation, Indulgence, Weekend Vibes",
        keywords=[
            "Weekend plans? We've got you covered",
            "Perfect for a relaxing weekend",
            "Treat yourself this weekend",
            "Weekend favorites",
            "Make it a delicious weekend"
        ]
    )


def create_daily_special_campaign() -> Campaign:
    """Create daily special campaign"""
    now = datetime.now()
    start_date = now.replace(hour=0, minute=0, second=0)
    end_date = now.replace(hour=23, minute=59, second=59)

    day_name = now.strftime("%A")

    return Campaign(
        name=f"{day_name} Special",
        description=f"Fresh {day_name} specials to brighten your day!",
        start_date=start_date,
        end_date=end_date,
        theme="Fresh, Daily, Seasonal",
        keywords=[
            f"Happy {day_name}!",
            "Fresh daily specials",
            "Made fresh today",
            f"Start your {day_name} right",
            "Daily favorites"
        ]
    )


if __name__ == "__main__":
    # Test campaign manager
    print("=" * 60)
    print("CAMPAIGN MANAGER TEST")
    print("=" * 60)

    # Create templates directory
    from config import Config
    templates_dir = Config.TEMPLATES_DIR

    # Create sample campaigns
    thanksgiving = create_thanksgiving_campaign()
    weekend = create_weekend_special_campaign()

    # Initialize manager
    manager = CampaignManager(templates_dir)

    # Save templates
    print("\nCreating campaign templates...")
    manager.create_campaign_template(thanksgiving)
    manager.create_campaign_template(weekend)

    # Reload
    manager.load_templates()

    print("\nAvailable campaigns:")
    for name in manager.list_campaigns():
        campaign = manager.get_campaign(name)
        print(f"\n  {name}")
        print(f"    Active: {campaign.is_active()}")
        print(f"    Dates: {campaign.start_date.strftime('%b %d')} - {campaign.end_date.strftime('%b %d, %Y')}")

    # Show Thanksgiving context
    print("\n" + "=" * 60)
    print("THANKSGIVING CAMPAIGN CONTEXT")
    print("=" * 60)
    thanksgiving = manager.get_campaign("Thanksgiving 2024")
    if thanksgiving:
        print(thanksgiving.get_context_prompt())

    print("\n" + "=" * 60)
