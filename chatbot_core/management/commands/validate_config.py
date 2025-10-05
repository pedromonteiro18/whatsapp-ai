"""
Management command to validate application configuration.

This command checks all required environment variables and validates
their values to ensure the application is properly configured.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import redis
import psycopg2
from twilio.rest import Client as TwilioClient
from openai import OpenAI

from chatbot_core.config import Config


class Command(BaseCommand):
    help = "Validate application configuration and test external service connections"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-external",
            action="store_true",
            help="Skip external service connectivity tests",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Configuration Validation"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Validate configuration
        self.stdout.write("Validating configuration settings...")
        is_valid, errors = Config.validate()

        if not is_valid:
            self.stdout.write(self.style.ERROR("\n✗ Configuration validation failed:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
            raise CommandError("Configuration validation failed")

        self.stdout.write(self.style.SUCCESS("✓ Configuration validation passed"))
        self.stdout.write("")

        # Display configuration summary
        self.stdout.write("Configuration Summary:")
        self.stdout.write(f"  AI Provider: {Config.AI_PROVIDER}")
        self.stdout.write(f"  AI Model: {Config.get_ai_model()}")
        self.stdout.write(f"  Max Tokens: {Config.OPENAI_MAX_TOKENS}")
        self.stdout.write(f"  Temperature: {Config.OPENAI_TEMPERATURE}")
        self.stdout.write(
            f"  Max Conversation History: {Config.MAX_CONVERSATION_HISTORY}"
        )
        self.stdout.write(
            f"  Session Timeout: {Config.SESSION_TIMEOUT_MINUTES} minutes"
        )
        self.stdout.write(
            f"  Rate Limit: {Config.RATE_LIMIT_MESSAGES_PER_MINUTE} messages/minute"
        )
        self.stdout.write("")

        if options["skip_external"]:
            self.stdout.write(
                self.style.WARNING("Skipping external service connectivity tests")
            )
            return

        # Test external services
        self.stdout.write("Testing external service connections...")
        self.stdout.write("")

        # Test database connection
        self.test_database()

        # Test Redis connection
        self.test_redis()

        # Test Twilio connection
        self.test_twilio()

        # Test AI API connection
        self.test_ai_api()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS("✓ All configuration checks passed successfully!")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))

    def test_database(self):
        """Test PostgreSQL database connection"""
        self.stdout.write("Testing database connection...")
        try:
            db_settings = settings.DATABASES["default"]
            conn = psycopg2.connect(
                dbname=db_settings["NAME"],
                user=db_settings["USER"],
                password=db_settings["PASSWORD"],
                host=db_settings["HOST"],
                port=db_settings["PORT"],
            )
            conn.close()
            self.stdout.write(self.style.SUCCESS("  ✓ Database connection successful"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Database connection failed: {e}"))
            raise CommandError("Database connection test failed")

    def test_redis(self):
        """Test Redis connection"""
        self.stdout.write("Testing Redis connection...")
        try:
            r = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                socket_connect_timeout=5,
            )
            r.ping()
            self.stdout.write(self.style.SUCCESS("  ✓ Redis connection successful"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Redis connection failed: {e}"))
            raise CommandError("Redis connection test failed")

    def test_twilio(self):
        """Test Twilio API credentials"""
        self.stdout.write("Testing Twilio credentials...")
        try:
            client = TwilioClient(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
            # Fetch account to validate credentials
            account = client.api.accounts(Config.TWILIO_ACCOUNT_SID).fetch()
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Twilio credentials valid (Account: {account.friendly_name})"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Twilio credentials invalid: {e}")
            )
            raise CommandError("Twilio credentials test failed")

    def test_ai_api(self):
        """Test AI API credentials"""
        self.stdout.write(f"Testing {Config.AI_PROVIDER.upper()} API credentials...")
        try:
            if Config.AI_PROVIDER == "openai":
                client = OpenAI(api_key=Config.OPENAI_API_KEY)
                # Make a minimal API call to test credentials
                response = client.models.list()
                self.stdout.write(
                    self.style.SUCCESS("  ✓ OpenAI API credentials valid")
                )
            elif Config.AI_PROVIDER == "anthropic":
                # Anthropic test would go here
                self.stdout.write(
                    self.style.WARNING("  ⚠ Anthropic API test not implemented yet")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Unknown AI provider: {Config.AI_PROVIDER}")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ {Config.AI_PROVIDER.upper()} API test failed: {e}")
            )
            raise CommandError("AI API credentials test failed")
