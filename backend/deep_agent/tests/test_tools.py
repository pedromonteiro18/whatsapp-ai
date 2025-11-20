"""
Unit tests for deep-agent LangChain tools.

Tests tool functionality with Django models and services.
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.test import TestCase
from django.utils import timezone

from backend.booking_system.models import Activity, Booking, TimeSlot

from ..tools import (
    cancel_booking,
    check_time_slots,
    create_pending_booking,
    get_activity_details,
    get_user_bookings,
    search_activities,
    search_resort_knowledge,
)


class SearchActivitiesToolTest(TestCase):
    """Tests for search_activities tool."""

    def setUp(self):
        """Create test activities."""
        self.watersports_activity = Activity.objects.create(
            name="Kayaking Adventure",
            slug="kayaking-adventure",
            description="Explore the coastline by kayak",
            category="watersports",
            price=Decimal("75.00"),
            currency="USD",
            duration_minutes=120,
            capacity_per_slot=10,
            location="Beach",
            is_active=True,
        )

        self.spa_activity = Activity.objects.create(
            name="Relaxing Massage",
            slug="relaxing-massage",
            description="60-minute full body massage",
            category="spa",
            price=Decimal("120.00"),
            currency="USD",
            duration_minutes=60,
            capacity_per_slot=1,
            location="Spa Center",
            is_active=True,
        )

    def test_search_all_activities(self):
        """Test searching all active activities."""
        result = search_activities.invoke({})

        self.assertIn("Kayaking Adventure", result)
        self.assertIn("Relaxing Massage", result)
        self.assertIn("$75.00", result)
        self.assertIn("$120.00", result)

    def test_search_by_category(self):
        """Test filtering by category."""
        result = search_activities.invoke({"category": "watersports"})

        self.assertIn("Kayaking Adventure", result)
        self.assertNotIn("Relaxing Massage", result)

    def test_search_by_max_price(self):
        """Test filtering by maximum price."""
        result = search_activities.invoke({"max_price": 100.0})

        self.assertIn("Kayaking Adventure", result)
        self.assertNotIn("Relaxing Massage", result)

    def test_search_by_duration(self):
        """Test filtering by duration."""
        result = search_activities.invoke({"max_duration": 90})

        self.assertNotIn("Kayaking Adventure", result)
        self.assertIn("Relaxing Massage", result)

    def test_search_no_results(self):
        """Test search with no matching activities."""
        result = search_activities.invoke({"max_price": 10.0})

        self.assertIn("No activities found", result)


class GetActivityDetailsToolTest(TestCase):
    """Tests for get_activity_details tool."""

    def setUp(self):
        """Create test activity."""
        self.activity = Activity.objects.create(
            name="Scuba Diving",
            slug="scuba-diving",
            description="Beginner-friendly scuba diving experience",
            category="watersports",
            price=Decimal("150.00"),
            currency="USD",
            duration_minutes=180,
            capacity_per_slot=6,
            location="Marina Dock",
            requirements="Must be able to swim",
            is_active=True,
        )

    def test_get_existing_activity(self):
        """Test getting details of existing activity."""
        result = get_activity_details.invoke({"activity_id": str(self.activity.id)})

        self.assertIn("Scuba Diving", result)
        self.assertIn("$150.00", result)
        self.assertIn("3 hours", result)  # 180 minutes
        self.assertIn("Marina Dock", result)
        self.assertIn("Must be able to swim", result)

    def test_get_nonexistent_activity(self):
        """Test getting details of nonexistent activity."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        result = get_activity_details.invoke({"activity_id": fake_id})

        self.assertIn("not found", result)


class CheckTimeSlotsToolTest(TestCase):
    """Tests for check_time_slots tool."""

    def setUp(self):
        """Create test activity and time slots."""
        self.activity = Activity.objects.create(
            name="Sunset Cruise",
            slug="sunset-cruise",
            description="Beautiful sunset boat cruise",
            category="watersports",
            price=Decimal("90.00"),
            currency="USD",
            duration_minutes=120,
            capacity_per_slot=20,
            location="Harbor",
            is_active=True,
        )

        # Create time slots for the next 3 days
        now = timezone.now()
        for i in range(3):
            start_time = now + timedelta(days=i, hours=17)  # 5 PM each day
            TimeSlot.objects.create(
                activity=self.activity,
                start_time=start_time,
                end_time=start_time + timedelta(hours=2),
                capacity=20,
                booked_count=5,  # 15 available
                is_available=True,
            )

    def test_check_available_slots(self):
        """Test checking available time slots."""
        result = check_time_slots.invoke({"activity_id": str(self.activity.id)})

        self.assertIn("Sunset Cruise", result)
        self.assertIn("Available spots: 15/20", result)

    def test_check_slots_with_date_filter(self):
        """Test checking time slots for specific date."""
        tomorrow = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = check_time_slots.invoke({
            "activity_id": str(self.activity.id),
            "date": tomorrow,
        })

        # Should only show one slot for that specific date
        self.assertIn("Sunset Cruise", result)

    def test_check_slots_no_availability(self):
        """Test checking when no slots available."""
        # Make all slots fully booked
        TimeSlot.objects.filter(activity=self.activity).update(booked_count=20)

        result = check_time_slots.invoke({"activity_id": str(self.activity.id)})

        self.assertIn("No available time slots", result)


class CreatePendingBookingToolTest(TestCase):
    """Tests for create_pending_booking tool."""

    def setUp(self):
        """Create test activity and time slot."""
        self.activity = Activity.objects.create(
            name="Snorkeling Tour",
            slug="snorkeling-tour",
            description="Guided snorkeling adventure",
            category="watersports",
            price=Decimal("65.00"),
            currency="USD",
            duration_minutes=90,
            capacity_per_slot=12,
            location="Coral Bay",
            is_active=True,
        )

        start_time = timezone.now() + timedelta(days=1, hours=10)
        self.time_slot = TimeSlot.objects.create(
            activity=self.activity,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=90),
            capacity=12,
            booked_count=0,
            is_available=True,
        )

    @patch("backend.booking_system.services.NotificationService.send_booking_created")
    def test_create_valid_booking(self, mock_notification):
        """Test creating a valid pending booking."""
        result = create_pending_booking.invoke({
            "user_phone": "+1234567890",
            "activity_id": str(self.activity.id),
            "time_slot_id": str(self.time_slot.id),
            "participants": 2,
        })

        self.assertIn("Booking created successfully", result)
        self.assertIn("Snorkeling Tour", result)
        self.assertIn("$130.00", result)  # 2 participants * $65
        self.assertIn("Pending Confirmation", result)

        # Verify booking was created
        booking = Booking.objects.get(user_phone="+1234567890")
        self.assertEqual(booking.participants, 2)
        self.assertEqual(booking.status, "pending")

        # Verify time slot booked_count was incremented
        self.time_slot.refresh_from_db()
        self.assertEqual(self.time_slot.booked_count, 2)

    @patch("backend.booking_system.services.NotificationService.send_booking_created")
    def test_create_booking_no_availability(self, mock_notification):
        """Test creating booking when no availability."""
        # Fill up the time slot
        self.time_slot.booked_count = 12
        self.time_slot.save()

        result = create_pending_booking.invoke({
            "user_phone": "+1234567890",
            "activity_id": str(self.activity.id),
            "time_slot_id": str(self.time_slot.id),
            "participants": 1,
        })

        self.assertIn("Cannot create booking", result)
        self.assertIn("not available", result.lower())


class GetUserBookingsToolTest(TestCase):
    """Tests for get_user_bookings tool."""

    def setUp(self):
        """Create test bookings."""
        self.user_phone = "+1234567890"

        self.activity = Activity.objects.create(
            name="Yoga Class",
            slug="yoga-class",
            description="Morning yoga session",
            category="wellness",
            price=Decimal("30.00"),
            currency="USD",
            duration_minutes=60,
            capacity_per_slot=15,
            location="Wellness Center",
            is_active=True,
        )

        start_time = timezone.now() + timedelta(days=2)
        time_slot = TimeSlot.objects.create(
            activity=self.activity,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            capacity=15,
            booked_count=1,
            is_available=True,
        )

        # Create pending booking
        self.pending_booking = Booking.objects.create(
            user_phone=self.user_phone,
            activity=self.activity,
            time_slot=time_slot,
            status="pending",
            participants=1,
            total_price=Decimal("30.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        # Create confirmed booking
        self.confirmed_booking = Booking.objects.create(
            user_phone=self.user_phone,
            activity=self.activity,
            time_slot=time_slot,
            status="confirmed",
            participants=1,
            total_price=Decimal("30.00"),
            expires_at=timezone.now() + timedelta(days=2),
            confirmed_at=timezone.now(),
        )

    def test_get_all_bookings(self):
        """Test getting all user bookings."""
        result = get_user_bookings.invoke({"user_phone": self.user_phone})

        self.assertIn("Your Bookings", result)
        self.assertIn("Pending", result)
        self.assertIn("Confirmed", result)
        self.assertIn("Yoga Class", result)

    def test_get_bookings_by_status(self):
        """Test filtering bookings by status."""
        result = get_user_bookings.invoke({
            "user_phone": self.user_phone,
            "status": "pending",
        })

        self.assertIn("Pending", result)
        self.assertNotIn("Confirmed", result)

    def test_get_bookings_no_results(self):
        """Test getting bookings for user with none."""
        result = get_user_bookings.invoke({"user_phone": "+9999999999"})

        self.assertIn("No bookings found", result)


class SearchResortKnowledgeToolTest(TestCase):
    """Tests for search_resort_knowledge tool."""

    def test_search_checkin_info(self):
        """Test searching for check-in information."""
        result = search_resort_knowledge.invoke({"query": "What time is check-in?"})

        self.assertIn("check-in", result.lower())
        self.assertIn("3:00 PM", result)

    def test_search_wifi_info(self):
        """Test searching for WiFi information."""
        result = search_resort_knowledge.invoke({"query": "Do you have WiFi?"})

        self.assertIn("wifi", result.lower())
        self.assertIn("complimentary", result.lower())

    def test_search_no_match(self):
        """Test searching for information not in knowledge base."""
        result = search_resort_knowledge.invoke({
            "query": "What is the meaning of life?"
        })

        self.assertIn("don't have specific information", result)
        self.assertIn("contact", result.lower())
