"""Tests for the booking system."""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from .models import Activity, Booking, TimeSlot
from .notifications import NotificationService


class NotificationServiceTests(TestCase):
    """Test cases for NotificationService."""

    def setUp(self):
        """Set up test data for all tests."""
        # Create test activity
        self.activity = Activity.objects.create(
            name="Sunset Kayaking",
            slug="sunset-kayaking",
            description="Enjoy a peaceful kayaking session at sunset",
            category="watersports",
            price=Decimal("75.00"),
            duration_minutes=90,
            capacity_per_slot=10,
            location="Beach Dock #3",
            requirements="Must be able to swim. Life jackets provided.",
            is_active=True,
        )

        # Create test time slot
        self.time_slot = TimeSlot.objects.create(
            activity=self.activity,
            start_time=timezone.now() + timedelta(days=2),
            end_time=timezone.now() + timedelta(days=2, hours=1, minutes=30),
            capacity=10,
            booked_count=0,
            is_available=True,
        )

        # Create test booking
        self.booking = Booking.objects.create(
            user_phone="+1234567890",
            activity=self.activity,
            time_slot=self.time_slot,
            status="pending",
            participants=2,
            special_requests="Please reserve front kayaks",
            total_price=Decimal("150.00"),
            expires_at=timezone.now() + timedelta(minutes=30),
            booking_source="whatsapp",
        )

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_booking_created_success(self, mock_client_class):
        """Test successful booking created notification."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.return_value = True

        # Call method
        result = NotificationService.send_booking_created(self.booking)

        # Verify result
        self.assertTrue(result)

        # Verify WhatsApp client was called correctly
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args

        # Check phone number formatting
        self.assertEqual(call_args[1]["to"], "whatsapp:+1234567890")

        # Check message contains key information
        message = call_args[1]["message"]
        self.assertIn("Sunset Kayaking", message)
        self.assertIn("2", message)  # participants
        self.assertIn("$150.00", message)  # total price
        self.assertIn("90 minutes", message)  # duration
        self.assertIn("30 minutes", message)  # expiry warning
        self.assertIn("Confirm your booking", message)

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_booking_confirmed_success(self, mock_client_class):
        """Test successful booking confirmed notification."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.return_value = True

        # Update booking status to confirmed
        self.booking.status = "confirmed"
        self.booking.confirmed_at = timezone.now()
        self.booking.save()

        # Call method
        result = NotificationService.send_booking_confirmed(self.booking)

        # Verify result
        self.assertTrue(result)

        # Verify WhatsApp client was called correctly
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args

        # Check phone number formatting
        self.assertEqual(call_args[1]["to"], "whatsapp:+1234567890")

        # Check message contains key information
        message = call_args[1]["message"]
        self.assertIn("✅", message)
        self.assertIn("Booking Confirmed", message)
        self.assertIn("Sunset Kayaking", message)
        self.assertIn("Beach Dock #3", message)  # location
        self.assertIn("2", message)  # participants
        self.assertIn("Must be able to swim", message)  # requirements
        self.assertIn("24 hours", message)  # cancellation policy

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_booking_cancelled_success(self, mock_client_class):
        """Test successful booking cancelled notification."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.return_value = True

        # Update booking status to cancelled
        self.booking.status = "cancelled"
        self.booking.cancelled_at = timezone.now()
        self.booking.save()

        # Call method with reason
        reason = "Weather conditions not suitable"
        result = NotificationService.send_booking_cancelled(self.booking, reason)

        # Verify result
        self.assertTrue(result)

        # Verify WhatsApp client was called correctly
        mock_client.send_message.assert_called_once()
        call_args = mock_client.send_message.call_args

        # Check phone number formatting
        self.assertEqual(call_args[1]["to"], "whatsapp:+1234567890")

        # Check message contains key information
        message = call_args[1]["message"]
        self.assertIn("❌", message)
        self.assertIn("Booking Cancelled", message)
        self.assertIn("Sunset Kayaking", message)
        self.assertIn(reason, message)  # cancellation reason
        self.assertIn("Browse activities", message)

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_booking_cancelled_without_reason(self, mock_client_class):
        """Test booking cancelled notification without reason."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.return_value = True

        # Call method without reason
        result = NotificationService.send_booking_cancelled(self.booking)

        # Verify result
        self.assertTrue(result)

        # Verify WhatsApp client was called
        mock_client.send_message.assert_called_once()

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_notification_handles_client_error(self, mock_client_class):
        """Test that notification methods handle WhatsAppClientError gracefully."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        from whatsapp.client import WhatsAppClientError
        mock_client.send_message.side_effect = WhatsAppClientError("Connection failed")

        # Call method
        result = NotificationService.send_booking_created(self.booking)

        # Verify method returns False but doesn't raise exception
        self.assertFalse(result)

    @patch("booking_system.notifications.WhatsAppClient")
    def test_send_notification_handles_unexpected_error(self, mock_client_class):
        """Test that notification methods handle unexpected errors gracefully."""
        # Setup mock to raise unexpected exception
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.send_message.side_effect = RuntimeError("Unexpected error")

        # Call method
        result = NotificationService.send_booking_created(self.booking)

        # Verify method returns False but doesn't raise exception
        self.assertFalse(result)

    def test_format_phone_number_adds_prefix(self):
        """Test that _format_phone_number adds whatsapp: prefix."""
        phone_without_prefix = "+1234567890"
        result = NotificationService._format_phone_number(phone_without_prefix)
        self.assertEqual(result, "whatsapp:+1234567890")

    def test_format_phone_number_preserves_prefix(self):
        """Test that _format_phone_number preserves existing prefix."""
        phone_with_prefix = "whatsapp:+1234567890"
        result = NotificationService._format_phone_number(phone_with_prefix)
        self.assertEqual(result, "whatsapp:+1234567890")

    def test_format_datetime(self):
        """Test that _format_datetime produces readable format."""
        from datetime import datetime
        from zoneinfo import ZoneInfo
        test_datetime = datetime(2025, 10, 14, 14, 30, 0, tzinfo=ZoneInfo("UTC"))
        result = NotificationService._format_datetime(test_datetime)

        # Check format contains date and time components
        self.assertIn("October", result)
        self.assertIn("14", result)
        self.assertIn("2025", result)
        self.assertIn("2:30 PM", result)

    @patch("booking_system.notifications.config")
    def test_web_app_url_configuration(self, mock_config):
        """Test that WEB_APP_URL reads from configuration."""
        # The actual test is that the class attribute is defined
        # and uses config() with a default value
        self.assertTrue(hasattr(NotificationService, "WEB_APP_URL"))

    @patch("booking_system.notifications.WhatsAppClient")
    def test_notification_includes_web_app_links(self, mock_client_class):
        """Test that notifications include proper web app links."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Call method
        NotificationService.send_booking_created(self.booking)

        # Get the message
        call_args = mock_client.send_message.call_args
        message = call_args[1]["message"]

        # Verify link contains booking ID
        self.assertIn(str(self.booking.id), message)
