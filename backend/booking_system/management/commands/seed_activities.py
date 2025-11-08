"""
Management command to seed the database with sample resort activities.

This command creates realistic resort activities across all categories with
descriptions, pricing, and time slots for testing and demonstration.
"""

import io
from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image

from backend.booking_system.models import Activity, ActivityImage, TimeSlot


class Command(BaseCommand):
    help = "Seed the database with sample resort activities and time slots"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing activities and time slots before seeding",
        )
        parser.add_argument(
            "--skip-timeslots",
            action="store_true",
            help="Only create activities without generating time slots",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to generate time slots for (default: 30)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Seeding Resort Activities"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        if options["clear"]:
            self._clear_existing_data()

        activities = self._create_activities()

        if not options["skip_timeslots"]:
            self._create_time_slots(activities, options["days"])

        self._print_summary(activities, options)

    def _clear_existing_data(self) -> None:
        """Delete all existing activities and related data."""
        self.stdout.write("Clearing existing data...")

        with transaction.atomic():
            # Delete in correct order due to foreign key constraints
            TimeSlot.objects.all().delete()
            ActivityImage.objects.all().delete()
            Activity.objects.all().delete()

        self.stdout.write(self.style.SUCCESS("  ✓ Existing data cleared"))
        self.stdout.write("")

    def _create_activities(self) -> list[Activity]:
        """Create sample activities across all categories."""
        self.stdout.write("Creating activities...")

        # Define sample activities with realistic data
        activities_data = [
            # Watersports
            {
                "name": "Tropical Snorkeling Adventure",
                "category": "watersports",
                "description": "Explore vibrant coral reefs and encounter colorful marine life in crystal-clear waters. Our experienced guides will take you to the best snorkeling spots where you can see tropical fish, sea turtles, and other fascinating sea creatures. All equipment provided including mask, snorkel, fins, and flotation devices.",
                "price": Decimal("75.00"),
                "duration_minutes": 120,
                "capacity_per_slot": 8,
                "location": "Paradise Beach, Coral Bay",
                "requirements": "Basic swimming ability required. Minimum age: 8 years. Life jackets provided for non-confident swimmers.",
                "color": (100, 180, 255),  # Blue
            },
            {
                "name": "Jet Ski Ocean Safari",
                "category": "watersports",
                "description": "Experience the thrill of jet skiing across pristine ocean waters. Ride your own jet ski or share with a partner as you explore hidden coves and secluded beaches. Our guided tour ensures safety while maximizing fun. Brief training session included for beginners.",
                "price": Decimal("150.00"),
                "duration_minutes": 60,
                "capacity_per_slot": 6,
                "location": "Marina Bay Water Sports Center",
                "requirements": "Valid driver's license required for solo riders. Minimum age: 16 years (solo), 8 years (passenger). No experience necessary.",
                "color": (50, 150, 255),  # Darker blue
            },
            {
                "name": "Stand-Up Paddleboarding",
                "category": "watersports",
                "description": "Glide across calm lagoon waters on a stand-up paddleboard. Perfect for beginners and experienced paddlers alike. Enjoy stunning views of the coastline while getting a full-body workout. Includes basic instruction and all equipment.",
                "price": Decimal("55.00"),
                "duration_minutes": 90,
                "capacity_per_slot": 10,
                "location": "Sunset Lagoon",
                "requirements": "Basic swimming ability recommended. Suitable for all fitness levels. Minimum age: 10 years.",
                "color": (130, 200, 255),  # Light blue
            },
            {
                "name": "Scuba Diving Experience",
                "category": "watersports",
                "description": "Discover the underwater world with our professional dive instructors. This beginner-friendly dive includes classroom instruction, pool practice, and a shallow reef dive. See vibrant coral formations, tropical fish, and maybe even a reef shark! PADI certified instructors ensure your safety.",
                "price": Decimal("200.00"),
                "duration_minutes": 180,
                "capacity_per_slot": 4,
                "location": "Blue Lagoon Dive Center",
                "requirements": "Medical clearance form required. Minimum age: 12 years. Must be comfortable in water. Certification not required.",
                "color": (30, 120, 200),  # Deep blue
            },
            # Spa
            {
                "name": "Swedish Massage Therapy",
                "category": "spa",
                "description": "Indulge in a luxurious 90-minute Swedish massage designed to relax muscles and ease tension. Our skilled therapists use flowing strokes and gentle pressure to promote circulation and deep relaxation. Choose from aromatherapy oils including lavender, eucalyptus, or tropical coconut.",
                "price": Decimal("120.00"),
                "duration_minutes": 90,
                "capacity_per_slot": 3,
                "location": "Serenity Spa, Main Building",
                "requirements": "Arrive 15 minutes early. Notify us of any medical conditions or allergies. Gratuity not included.",
                "color": (220, 180, 200),  # Light pink
            },
            {
                "name": "Hot Stone Therapy",
                "category": "spa",
                "description": "Experience ultimate relaxation with our signature hot stone massage. Smooth, heated volcanic stones are placed on key points of your body while our therapists use massage techniques to melt away stress and muscle tension. The warmth penetrates deep into muscles for lasting relief.",
                "price": Decimal("140.00"),
                "duration_minutes": 75,
                "capacity_per_slot": 2,
                "location": "Serenity Spa, Main Building",
                "requirements": "Not suitable for pregnant women or those with certain medical conditions. Please consult with spa staff.",
                "color": (180, 140, 160),  # Muted purple
            },
            {
                "name": "Couples Spa Package",
                "category": "spa",
                "description": "Share a romantic spa experience with your partner in our private couples suite. Includes side-by-side massages, access to private hot tub, champagne and chocolate-covered strawberries, and aromatic foot soaks. The perfect way to reconnect and relax together.",
                "price": Decimal("280.00"),
                "duration_minutes": 120,
                "capacity_per_slot": 1,  # One couple per slot
                "location": "Serenity Spa, Couples Suite",
                "requirements": "Advanced booking required. Must be 18+ years old. Please arrive 20 minutes early to enjoy amenities.",
                "color": (255, 200, 220),  # Soft pink
            },
            # Dining
            {
                "name": "Beachside BBQ Experience",
                "category": "dining",
                "description": "Enjoy a memorable evening with toes in the sand at our beachside barbecue. Feast on grilled seafood, prime meats, and fresh salads while watching the sunset. Live acoustic music sets the mood as you dine under the stars. Includes unlimited non-alcoholic beverages.",
                "price": Decimal("95.00"),
                "duration_minutes": 150,
                "capacity_per_slot": 30,
                "location": "Paradise Beach Restaurant",
                "requirements": "Vegetarian and vegan options available. Please inform us of dietary restrictions 24 hours in advance.",
                "color": (255, 180, 100),  # Orange
            },
            {
                "name": "Sunset Dinner Cruise",
                "category": "dining",
                "description": "Set sail on our luxury catamaran for an unforgettable dining experience at sea. Watch the sun dip below the horizon while enjoying a three-course gourmet meal prepared by our executive chef. Includes wine pairing and complimentary champagne toast at sunset.",
                "price": Decimal("165.00"),
                "duration_minutes": 180,
                "capacity_per_slot": 20,
                "location": "Marina Bay Dock 3",
                "requirements": "Smart casual attire required. Not recommended for those prone to seasickness. Minimum age: 12 years.",
                "color": (255, 150, 80),  # Sunset orange
            },
            {
                "name": "Chef's Table Experience",
                "category": "dining",
                "description": "An exclusive culinary journey with our award-winning chef. Watch your seven-course tasting menu being prepared in our showcase kitchen. Each course is paired with premium wines selected by our sommelier. Limited to just 8 guests for an intimate experience.",
                "price": Decimal("250.00"),
                "duration_minutes": 180,
                "capacity_per_slot": 8,
                "location": "Azure Restaurant, Private Dining Room",
                "requirements": "Advanced booking required (48 hours minimum). Formal attire. 21+ years only. Dietary restrictions accommodated with notice.",
                "color": (200, 120, 60),  # Rich brown
            },
            # Adventure
            {
                "name": "Rainforest Zip Line Tour",
                "category": "adventure",
                "description": "Soar through the jungle canopy on our thrilling zip line course featuring 8 lines ranging from 100 to 600 feet. Experience breathtaking views of the rainforest from above while trained guides ensure your safety. Includes transportation from resort, all equipment, and refreshments.",
                "price": Decimal("125.00"),
                "duration_minutes": 150,
                "capacity_per_slot": 10,
                "location": "Tropical Rainforest Adventure Park (20 min from resort)",
                "requirements": "Weight limits: 70-250 lbs. Closed-toe shoes required. Minimum age: 10 years. Signed waiver required.",
                "color": (100, 200, 100),  # Green
            },
            {
                "name": "Rock Climbing & Rappelling",
                "category": "adventure",
                "description": "Challenge yourself on our natural rock formations suitable for all skill levels. Expert instructors provide training and guidance whether you're a first-timer or experienced climber. Includes rock climbing session and an exhilarating rappel descent. All safety equipment provided.",
                "price": Decimal("110.00"),
                "duration_minutes": 180,
                "capacity_per_slot": 6,
                "location": "Volcanic Cliff Adventure Site",
                "requirements": "Good physical condition required. Weight limit: 250 lbs. Minimum age: 12 years. Athletic shoes required.",
                "color": (140, 180, 100),  # Olive green
            },
            {
                "name": "Jungle Trek & Waterfall Swim",
                "category": "adventure",
                "description": "Embark on a guided hike through lush tropical rainforest to discover a hidden waterfall. Learn about native plants and wildlife from our naturalist guide. Cool off with a refreshing swim in the crystal-clear waterfall pool. Includes lunch and transportation.",
                "price": Decimal("85.00"),
                "duration_minutes": 240,
                "capacity_per_slot": 12,
                "location": "Mountain Trails Park (30 min from resort)",
                "requirements": "Moderate fitness level required. Hiking shoes essential. Bring swimsuit and towel. Minimum age: 8 years.",
                "color": (80, 160, 80),  # Forest green
            },
            {
                "name": "ATV Coastal Adventure",
                "category": "adventure",
                "description": "Explore rugged coastal trails and hidden beaches on a powerful all-terrain vehicle. Follow your guide through diverse terrain including beach, jungle paths, and mountain trails. Stop for photos at scenic viewpoints and take a refreshing dip at a secluded beach.",
                "price": Decimal("135.00"),
                "duration_minutes": 150,
                "capacity_per_slot": 8,
                "location": "Coastal Trail Head, North Beach",
                "requirements": "Valid driver's license required. Minimum age: 18 years (driver), 8 years (passenger). Closed-toe shoes and long pants recommended.",
                "color": (160, 200, 120),  # Yellow-green
            },
            # Wellness
            {
                "name": "Sunrise Beach Yoga",
                "category": "wellness",
                "description": "Start your day with an invigorating yoga session on the beach as the sun rises. Suitable for all levels, our certified instructor guides you through poses designed to energize and center your mind. Includes yoga mat and fresh fruit smoothie after class.",
                "price": Decimal("45.00"),
                "duration_minutes": 60,
                "capacity_per_slot": 15,
                "location": "Paradise Beach Pavilion",
                "requirements": "All fitness levels welcome. Bring water and towel. Wear comfortable athletic clothing. Arrive 10 minutes early.",
                "color": (255, 220, 180),  # Warm beige
            },
            {
                "name": "Guided Meditation & Breathwork",
                "category": "wellness",
                "description": "Find inner peace with our guided meditation session combining ancient techniques with modern mindfulness practices. Learn breathing exercises to reduce stress and improve mental clarity. Perfect for beginners and experienced meditators. Takes place in our serene meditation garden.",
                "price": Decimal("40.00"),
                "duration_minutes": 75,
                "capacity_per_slot": 12,
                "location": "Zen Garden Meditation Pavilion",
                "requirements": "No experience necessary. Wear comfortable clothing. Cushions and props provided. Silence your phone.",
                "color": (200, 220, 240),  # Light blue-gray
            },
            {
                "name": "Holistic Wellness Workshop",
                "category": "wellness",
                "description": "Join our wellness expert for an interactive workshop covering nutrition, stress management, and healthy lifestyle practices. Learn practical techniques you can incorporate into daily life. Includes wellness consultation, healthy cooking demonstration, and take-home resource guide.",
                "price": Decimal("75.00"),
                "duration_minutes": 120,
                "capacity_per_slot": 10,
                "location": "Wellness Center, Conference Room",
                "requirements": "Suitable for all ages 16+. Light refreshments provided. Please advise of any food allergies when booking.",
                "color": (180, 220, 200),  # Mint green
            },
        ]

        created_activities = []

        with transaction.atomic():
            for data in activities_data:
                # Extract color and remove from data dict
                color = data.pop("color")

                # Create slug from name
                slug = slugify(data["name"])

                # Create activity
                activity = Activity.objects.create(
                    slug=slug,
                    currency="USD",
                    is_active=True,
                    **data,
                )

                # Create placeholder images (2-3 per activity)
                num_images = 2 if data["category"] in ["spa", "dining"] else 3
                for i in range(num_images):
                    self._create_placeholder_image(activity, i, color)

                created_activities.append(activity)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Created: {activity.name} ({activity.category})"
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(created_activities)} activities across {len(set(a.category for a in created_activities))} categories"
            )
        )
        self.stdout.write("")

        return created_activities

    def _create_placeholder_image(
        self, activity: Activity, index: int, color: tuple[int, int, int]
    ) -> None:
        """Create a placeholder image for an activity."""
        # Create a simple colored image using PIL
        img = Image.new("RGB", (800, 600), color=color)

        # Save to BytesIO
        img_io = io.BytesIO()
        img.save(img_io, format="JPEG", quality=85)
        img_io.seek(0)

        # Create Django file
        image_file = SimpleUploadedFile(
            name=f"{activity.slug}-{index + 1}.jpg",
            content=img_io.read(),
            content_type="image/jpeg",
        )

        # Create ActivityImage
        ActivityImage.objects.create(
            activity=activity,
            image=image_file,
            alt_text=f"{activity.name} - Image {index + 1}",
            is_primary=(index == 0),
            order=index,
        )

    def _create_time_slots(self, activities: list[Activity], days: int) -> None:
        """Create time slots for all activities."""
        self.stdout.write(f"Creating time slots for next {days} days...")

        today = timezone.now().date()
        time_slots_created = 0

        with transaction.atomic():
            for activity in activities:
                # Determine time slots based on category
                if activity.category == "watersports":
                    times = [
                        time(9, 0),
                        time(11, 0),
                        time(13, 0),
                        time(15, 0),
                    ]
                elif activity.category == "spa":
                    times = [
                        time(9, 0),
                        time(11, 0),
                        time(13, 0),
                        time(15, 0),
                        time(17, 0),
                    ]
                elif activity.category == "dining":
                    times = [
                        time(18, 0),
                        time(19, 30),
                    ]
                elif activity.category == "adventure":
                    times = [
                        time(8, 0),
                        time(10, 0),
                        time(13, 0),
                        time(15, 0),
                    ]
                elif activity.category == "wellness":
                    times = [
                        time(6, 30),
                        time(8, 30),
                        time(16, 0),
                        time(17, 30),
                    ]
                else:
                    times = [time(9, 0), time(14, 0)]

                # Create slots for each day and time
                for day_offset in range(days):
                    slot_date = today + timedelta(days=day_offset)

                    for slot_time in times:
                        start_datetime = timezone.make_aware(
                            datetime.combine(slot_date, slot_time)
                        )
                        end_datetime = start_datetime + timedelta(
                            minutes=activity.duration_minutes
                        )

                        # Skip if time slot already exists
                        if TimeSlot.objects.filter(
                            activity=activity, start_time=start_datetime
                        ).exists():
                            continue

                        TimeSlot.objects.create(
                            activity=activity,
                            start_time=start_datetime,
                            end_time=end_datetime,
                            capacity=activity.capacity_per_slot,
                            booked_count=0,
                            is_available=True,
                        )
                        time_slots_created += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Created {time_slots_created:,} time slots")
        )
        self.stdout.write("")

    def _print_summary(self, activities: list[Activity], options: dict) -> None:
        """Print summary of what was created."""
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Summary"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Count by category
        by_category = {}
        for activity in activities:
            by_category[activity.category] = by_category.get(activity.category, 0) + 1

        self.stdout.write("Activities by Category:")
        for category, count in sorted(by_category.items()):
            self.stdout.write(f"  {category.title()}: {count}")
        self.stdout.write("")

        # Time slots info
        if not options["skip_timeslots"]:
            total_slots = TimeSlot.objects.count()
            self.stdout.write(f"Total Time Slots: {total_slots:,}")
            self.stdout.write("")

        # Images info
        total_images = ActivityImage.objects.count()
        self.stdout.write(f"Total Images: {total_images}")
        self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("✓ Seeding completed successfully!"))
        self.stdout.write("")
        self.stdout.write("Next steps:")
        self.stdout.write("  1. Visit Django admin to view activities")
        self.stdout.write("  2. Access the web app to browse activities")
        self.stdout.write("  3. Test booking flow via WhatsApp or web interface")
        self.stdout.write("")
