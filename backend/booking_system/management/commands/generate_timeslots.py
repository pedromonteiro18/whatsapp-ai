"""
Management command to generate time slots for activities.

This command provides flexible time slot generation with support for
date ranges, specific times, and recurrence patterns.
"""

from datetime import datetime, time, timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from backend.booking_system.models import Activity, TimeSlot


class Command(BaseCommand):
    help = "Generate time slots for activities with flexible scheduling options"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--activity",
            type=str,
            required=True,
            help="Activity slug or ID to generate time slots for",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            required=True,
            help="Start date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            required=True,
            help="End date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "--time",
            action="append",
            dest="times",
            required=True,
            help="Time(s) to create slots in HH:MM format (can be repeated)",
        )
        parser.add_argument(
            "--days",
            type=str,
            help='Days of week (e.g., "mon,wed,fri" or "weekdays" or "weekends" or "all")',
        )
        parser.add_argument(
            "--capacity",
            type=int,
            help="Override activity capacity for these slots",
        )
        parser.add_argument(
            "--skip-validation",
            action="store_true",
            help="Skip overlap validation (use with caution)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without saving to database",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Generate Time Slots"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Validate and parse inputs
        activity = self._get_activity(options["activity"])
        start_date = self._parse_date(options["start_date"])
        end_date = self._parse_date(options["end_date"])
        times = self._parse_times(options["times"])
        days_filter = self._parse_days(options.get("days"))
        capacity = options.get("capacity") or activity.capacity_per_slot

        # Validate date range
        if end_date < start_date:
            raise CommandError("End date must be after start date")

        # Show configuration
        self._print_configuration(
            activity, start_date, end_date, times, days_filter, capacity, options
        )

        # Generate time slots
        slots_to_create = self._generate_slots(
            activity,
            start_date,
            end_date,
            times,
            days_filter,
            capacity,
            options["skip_validation"],
        )

        if not slots_to_create:
            self.stdout.write(self.style.WARNING("No time slots to create"))
            return

        # Show what will be created
        self._preview_slots(slots_to_create)

        if options["dry_run"]:
            self.stdout.write("")
            self.stdout.write(
                self.style.WARNING("DRY RUN: No changes made to database")
            )
            return

        # Create slots
        self._create_slots(slots_to_create)

    def _get_activity(self, identifier: str) -> Activity:
        """Get activity by slug or ID."""
        self.stdout.write(f"Looking up activity: {identifier}")

        try:
            # Try as slug first
            activity = Activity.objects.get(slug=identifier)
        except Activity.DoesNotExist:
            # Try as ID
            try:
                activity = Activity.objects.get(id=identifier)
            except Activity.DoesNotExist:
                raise CommandError(f"Activity not found: {identifier}")

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Found: {activity.name} ({activity.category}, {activity.duration_minutes} min)"
            )
        )
        self.stdout.write("")
        return activity

    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse date string in YYYY-MM-DD format."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise CommandError(
                f"Invalid date format: {date_str}. Use YYYY-MM-DD format."
            )

    def _parse_times(self, time_strings: list[str]) -> list[time]:
        """Parse time strings in HH:MM format."""
        parsed_times = []
        for time_str in time_strings:
            try:
                hour, minute = map(int, time_str.split(":"))
                parsed_times.append(time(hour, minute))
            except (ValueError, AttributeError):
                raise CommandError(
                    f"Invalid time format: {time_str}. Use HH:MM format (e.g., 09:00, 14:30)"
                )
        return sorted(parsed_times)

    def _parse_days(self, days_str: str | None) -> set[int] | None:
        """
        Parse days filter string.

        Returns set of weekday numbers (0=Monday, 6=Sunday) or None for all days.
        """
        if not days_str:
            return None

        days_str = days_str.lower()

        # Handle special keywords
        if days_str == "all":
            return None
        elif days_str == "weekdays":
            return {0, 1, 2, 3, 4}  # Mon-Fri
        elif days_str == "weekends":
            return {5, 6}  # Sat-Sun

        # Parse individual days
        day_mapping = {
            "mon": 0,
            "monday": 0,
            "tue": 1,
            "tuesday": 1,
            "wed": 2,
            "wednesday": 2,
            "thu": 3,
            "thursday": 3,
            "fri": 4,
            "friday": 4,
            "sat": 5,
            "saturday": 5,
            "sun": 6,
            "sunday": 6,
        }

        days = set()
        for day in days_str.split(","):
            day = day.strip()
            if day not in day_mapping:
                raise CommandError(
                    f"Invalid day: {day}. Use day names (e.g., mon,tue,wed) or 'weekdays'/'weekends'/'all'"
                )
            days.add(day_mapping[day])

        return days

    def _print_configuration(
        self,
        activity: Activity,
        start_date: datetime.date,
        end_date: datetime.date,
        times: list[time],
        days_filter: set[int] | None,
        capacity: int,
        options: dict,
    ) -> None:
        """Print configuration summary."""
        self.stdout.write("Configuration:")
        self.stdout.write(f"  Activity: {activity.name}")
        self.stdout.write(f"  Date Range: {start_date} to {end_date}")
        self.stdout.write(
            f"  Times: {', '.join(t.strftime('%H:%M') for t in times)}"
        )

        if days_filter:
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            days_str = ", ".join(day_names[d] for d in sorted(days_filter))
            self.stdout.write(f"  Days: {days_str}")
        else:
            self.stdout.write("  Days: All days")

        self.stdout.write(f"  Capacity per slot: {capacity}")

        if options["skip_validation"]:
            self.stdout.write(
                self.style.WARNING("  Overlap validation: DISABLED")
            )

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("  Mode: DRY RUN"))

        self.stdout.write("")

    def _generate_slots(
        self,
        activity: Activity,
        start_date: datetime.date,
        end_date: datetime.date,
        times: list[time],
        days_filter: set[int] | None,
        capacity: int,
        skip_validation: bool,
    ) -> list[dict]:
        """Generate list of time slots to create."""
        self.stdout.write("Generating time slots...")

        slots_to_create = []
        skipped_existing = 0
        skipped_overlap = 0

        current_date = start_date
        while current_date <= end_date:
            # Check day filter
            if days_filter and current_date.weekday() not in days_filter:
                current_date += timedelta(days=1)
                continue

            for slot_time in times:
                start_datetime = timezone.make_aware(
                    datetime.combine(current_date, slot_time)
                )
                end_datetime = start_datetime + timedelta(
                    minutes=activity.duration_minutes
                )

                # Check if slot already exists
                if TimeSlot.objects.filter(
                    activity=activity, start_time=start_datetime
                ).exists():
                    skipped_existing += 1
                    continue

                # Check for overlaps if validation enabled
                if not skip_validation:
                    overlapping = TimeSlot.objects.filter(
                        activity=activity,
                        start_time__lt=end_datetime,
                        end_time__gt=start_datetime,
                    ).exists()

                    if overlapping:
                        skipped_overlap += 1
                        continue

                slots_to_create.append(
                    {
                        "activity": activity,
                        "start_time": start_datetime,
                        "end_time": end_datetime,
                        "capacity": capacity,
                    }
                )

            current_date += timedelta(days=1)

        # Show statistics
        self.stdout.write(
            self.style.SUCCESS(f"  ✓ {len(slots_to_create)} slots to create")
        )
        if skipped_existing > 0:
            self.stdout.write(f"  • {skipped_existing} slots already exist (skipped)")
        if skipped_overlap > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"  • {skipped_overlap} slots would overlap (skipped)"
                )
            )
        self.stdout.write("")

        return slots_to_create

    def _preview_slots(self, slots: list[dict]) -> None:
        """Show preview of slots to be created."""
        if not slots:
            return

        self.stdout.write("Preview (showing first 10):")

        for i, slot in enumerate(slots[:10]):
            start = slot["start_time"]
            end = slot["end_time"]
            self.stdout.write(
                f"  {start.strftime('%Y-%m-%d %H:%M')} - {end.strftime('%H:%M')} "
                f"(capacity: {slot['capacity']})"
            )

        if len(slots) > 10:
            self.stdout.write(f"  ... and {len(slots) - 10} more")

        self.stdout.write("")

    def _create_slots(self, slots: list[dict]) -> None:
        """Create time slots in database."""
        self.stdout.write("Creating time slots...")

        with transaction.atomic():
            time_slot_objects = [
                TimeSlot(
                    activity=slot["activity"],
                    start_time=slot["start_time"],
                    end_time=slot["end_time"],
                    capacity=slot["capacity"],
                    booked_count=0,
                    is_available=True,
                )
                for slot in slots
            ]

            TimeSlot.objects.bulk_create(time_slot_objects)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS(f"✓ Successfully created {len(slots):,} time slots!")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
