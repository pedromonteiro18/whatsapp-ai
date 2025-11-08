"""Management command to download activity images from Pexels."""

import time
from typing import Any

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from backend.booking_system.models import Activity, ActivityImage


class Command(BaseCommand):
    """Download activity images from Pexels and link them to activities."""

    help = "Download activity images from Pexels"

    # Mapping of activity names to specific Pexels photo IDs (curated themed images)
    ACTIVITY_IMAGE_IDS = {
        "Tropical Snorkeling Adventure": "1007657",  # snorkeling underwater
        "Stand-Up Paddleboarding": "416676",  # paddleboard on water
        "Jet Ski Ocean Safari": "2049422",  # jet ski action
        "Scuba Diving Experience": "2231746",  # scuba diving
        "Rainforest Zip Line Tour": "2398220",  # zip line adventure
        "Rock Climbing & Rappelling": "2398375",  # rock climbing
        "ATV Coastal Adventure": "2397415",  # ATV riding
        "Jungle Trek & Waterfall Swim": "1660995",  # waterfall nature
        "Swedish Massage Therapy": "3757657",  # massage spa
        "Hot Stone Therapy": "3757657",  # hot stone massage
        "Couples Spa Package": "3757946",  # couples spa
        "Beachside BBQ Experience": "1580518",  # beach barbecue
        "Sunset Dinner Cruise": "1797161",  # sunset boat cruise
        "Chef's Table Experience": "2291599",  # chef cooking
        "Sunrise Beach Yoga": "317157",  # beach yoga
        "Guided Meditation & Breathwork": "3822668",  # meditation
        "Holistic Wellness Workshop": "3822622",  # wellness
    }

    def add_arguments(self, parser: Any) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing activity images before downloading",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command."""
        if options["clear"]:
            self.stdout.write("Clearing existing activity images...")
            ActivityImage.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Cleared existing images"))

        activities = Activity.objects.filter(is_active=True)
        total = activities.count()
        success_count = 0
        skip_count = 0

        self.stdout.write(f"Processing {total} activities...")

        for activity in activities:
            # Skip if activity already has images (unless --clear was used)
            if not options["clear"] and activity.images.exists():
                self.stdout.write(f"  Skipping {activity.name} (already has images)")
                skip_count += 1
                continue

            photo_id = self.ACTIVITY_IMAGE_IDS.get(activity.name)
            if not photo_id:
                self.stdout.write(
                    self.style.WARNING(f"  No image ID defined for: {activity.name}")
                )
                continue

            try:
                self.stdout.write(f"  Downloading image for: {activity.name}")
                image_data = self.download_pexels_image(photo_id)

                if image_data:
                    # Create filename from activity slug
                    filename = f"{activity.slug}.jpg"

                    # Create ActivityImage record
                    activity_image = ActivityImage(
                        activity=activity,
                        alt_text=f"{activity.name} activity image",
                        is_primary=True,
                        order=0,
                    )
                    activity_image.image.save(
                        filename, ContentFile(image_data), save=True
                    )

                    self.stdout.write(
                        self.style.SUCCESS(f"    ✓ Saved image: {filename}")
                    )
                    success_count += 1

                    # Rate limiting - be nice to Unsplash
                    time.sleep(1)
                else:
                    self.stdout.write(
                        self.style.ERROR("    ✗ Failed to download image")
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    ✗ Error: {str(e)}"))

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"Downloaded {success_count}/{total} images " f"(skipped {skip_count})"
            )
        )

    def download_pexels_image(self, photo_id: str, width: int = 800) -> bytes | None:
        """
        Download an image from Pexels by photo ID.

        Args:
            photo_id: Pexels photo ID
            width: Desired image width

        Returns:
            Image data as bytes or None if download failed
        """
        try:
            # Use Pexels image URL format (no API key needed for direct photo access)
            # Format: https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w={width}
            url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w={width}"

            response = requests.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()

            # Verify it's an image
            content_type = response.headers.get("content-type", "")
            if "image" not in content_type:
                self.stdout.write(
                    self.style.WARNING(f"    Invalid content type: {content_type}")
                )
                return None

            return response.content

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"    Request error: {e}"))
            return None
