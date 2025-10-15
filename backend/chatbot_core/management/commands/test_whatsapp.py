"""
Management command to test WhatsApp integration.

Provides utilities for:
- Sending test messages to verify Twilio configuration
- Checking webhook connectivity
- Validating end-to-end message flow
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from backend.chatbot_core.config import Config
from backend.whatsapp.client import WhatsAppClient, WhatsAppClientError


class Command(BaseCommand):
    """Test WhatsApp integration with Twilio."""

    help = (
        "Test WhatsApp integration by sending test messages and verifying configuration"
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add command arguments.

        Args:
            parser: Command parser
        """
        parser.add_argument(
            "--to",
            type=str,
            help="Phone number to send test message to (e.g., +1234567890)",
        )
        parser.add_argument(
            "--message",
            type=str,
            default="This is a test message from WhatsApp AI Chatbot.",
            help="Custom test message to send",
        )
        parser.add_argument(
            "--check-config",
            action="store_true",
            help="Check WhatsApp configuration without sending a message",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Execute the command.

        Args:
            *args: Positional arguments
            **options: Command options
        """
        self.stdout.write(self.style.SUCCESS("=== WhatsApp Integration Test ===\n"))

        # Check configuration
        if not self._check_configuration():
            return

        # If only checking config, exit here
        if options["check_config"]:
            self.stdout.write(self.style.SUCCESS("\n✓ Configuration check complete"))
            return

        # Send test message
        to_number = options.get("to")
        if not to_number:
            self.stdout.write(
                self.style.ERROR(
                    "\nError: --to parameter is required to send test message"
                )
            )
            self.stdout.write("Usage: python manage.py test_whatsapp --to +1234567890")
            return

        message = options.get("message") or "Test message from WhatsApp AI Chatbot."
        self._send_test_message(to_number, message)

    def _check_configuration(self) -> bool:
        """
        Check WhatsApp/Twilio configuration.

        Returns:
            True if configuration is valid
        """
        self.stdout.write("Checking WhatsApp configuration...\n")

        # Check Twilio credentials
        try:
            account_sid = Config.TWILIO_ACCOUNT_SID
            auth_token = Config.TWILIO_AUTH_TOKEN
            from_number = Config.TWILIO_WHATSAPP_NUMBER

            if not account_sid:
                self.stdout.write(
                    self.style.ERROR("✗ TWILIO_ACCOUNT_SID is not configured")
                )
                return False
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ TWILIO_ACCOUNT_SID: {account_sid[:10]}...")
                )

            if not auth_token:
                self.stdout.write(
                    self.style.ERROR("✗ TWILIO_AUTH_TOKEN is not configured")
                )
                return False
            else:
                self.stdout.write(self.style.SUCCESS("✓ TWILIO_AUTH_TOKEN: [hidden]"))

            if not from_number:
                self.stdout.write(
                    self.style.ERROR("✗ TWILIO_WHATSAPP_NUMBER is not configured")
                )
                return False
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ TWILIO_WHATSAPP_NUMBER: {from_number}")
                )

            # Try to initialize WhatsApp client
            try:
                WhatsAppClient()
                self.stdout.write(
                    self.style.SUCCESS("✓ WhatsApp client initialized successfully")
                )
            except WhatsAppClientError as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to initialize WhatsApp client: {e}")
                )
                return False

            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Configuration check failed: {e}"))
            return False

    def _send_test_message(self, to_number: str, message: str) -> None:
        """
        Send a test message via WhatsApp.

        Args:
            to_number: Recipient phone number
            message: Message content
        """
        self.stdout.write(f"\nSending test message to {to_number}...")
        self.stdout.write(f"Message: {message}\n")

        try:
            # Initialize WhatsApp client
            client = WhatsAppClient()

            # Send message
            success = client.send_message(to_number, message)

            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✓ Test message sent successfully to {to_number}"
                    )
                )
                self.stdout.write("\nCheck your WhatsApp to confirm message receipt.")
            else:
                self.stdout.write(
                    self.style.ERROR(f"\n✗ Failed to send test message to {to_number}")
                )

        except WhatsAppClientError as e:
            self.stdout.write(self.style.ERROR(f"\n✗ WhatsApp client error: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Unexpected error: {e}"))
