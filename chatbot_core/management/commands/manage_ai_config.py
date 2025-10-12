"""
Management command to manage AI configuration.

Provides utilities for:
- Creating/updating AI configurations in the database
- Testing AI API connectivity
- Listing and viewing AI configurations
"""

from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from ai_integration.adapters.base import AuthenticationError
from ai_integration.factory import AIAdapterFactory
from chatbot_core.models import AIConfiguration


class Command(BaseCommand):
    """Manage AI provider configurations."""

    help = "Manage AI configurations: create, update, test, and list"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add command arguments.

        Args:
            parser: Command parser
        """
        subparsers = parser.add_subparsers(
            dest="action",
            help="Action to perform",
            required=True,
        )

        # List configurations
        subparsers.add_parser(
            "list",
            help="List all AI configurations",
        )

        # Create configuration
        create_parser = subparsers.add_parser(
            "create",
            help="Create a new AI configuration",
        )
        create_parser.add_argument("--name", required=True, help="Configuration name")
        create_parser.add_argument(
            "--provider",
            required=True,
            choices=["openrouter", "openai", "anthropic"],
            help="AI provider",
        )
        create_parser.add_argument("--api-key", required=True, help="API key")
        create_parser.add_argument("--model", required=True, help="Model name")
        create_parser.add_argument(
            "--max-tokens", type=int, default=500, help="Maximum tokens"
        )
        create_parser.add_argument(
            "--temperature", type=float, default=0.7, help="Temperature"
        )

        # Update configuration
        update_parser = subparsers.add_parser(
            "update",
            help="Update an existing AI configuration",
        )
        update_parser.add_argument("--name", required=True, help="Configuration name")
        update_parser.add_argument("--api-key", help="New API key")
        update_parser.add_argument("--model", help="New model name")
        update_parser.add_argument("--max-tokens", type=int, help="New maximum tokens")
        update_parser.add_argument("--temperature", type=float, help="New temperature")
        update_parser.add_argument(
            "--activate", action="store_true", help="Activate this configuration"
        )
        update_parser.add_argument(
            "--deactivate", action="store_true", help="Deactivate this configuration"
        )

        # Test configuration
        test_parser = subparsers.add_parser(
            "test",
            help="Test AI configuration connectivity",
        )
        test_parser.add_argument(
            "--name",
            help="Configuration name (defaults to active or environment config)",
        )
        test_parser.add_argument(
            "--use-env",
            action="store_true",
            help="Test environment configuration instead of database",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Execute the command.

        Args:
            *args: Positional arguments
            **options: Command options
        """
        action = options["action"]

        if action == "list":
            self._list_configurations()
        elif action == "create":
            self._create_configuration(options)
        elif action == "update":
            self._update_configuration(options)
        elif action == "test":
            self._test_configuration(options)

    def _list_configurations(self) -> None:
        """List all AI configurations."""
        self.stdout.write(self.style.SUCCESS("=== AI Configurations ===\n"))

        configs = AIConfiguration.objects.all().order_by("-is_active", "name")

        if not configs:
            self.stdout.write("No configurations found.")
            return

        for config in configs:
            status = "ACTIVE" if config.is_active else "inactive"
            self.stdout.write(f"\n{self.style.WARNING(config.name)} [{status}]")
            self.stdout.write(f"  Provider: {config.provider}")
            self.stdout.write(f"  Model: {config.model_name}")
            self.stdout.write(f"  Max Tokens: {config.max_tokens}")
            self.stdout.write(f"  Temperature: {config.temperature}")
            self.stdout.write(f"  Created: {config.created_at}")
            self.stdout.write(f"  Updated: {config.updated_at}")

    def _create_configuration(self, options: dict[str, Any]) -> None:
        """
        Create a new AI configuration.

        Args:
            options: Command options
        """
        self.stdout.write(self.style.SUCCESS("=== Creating AI Configuration ===\n"))

        name = options["name"]
        provider = options["provider"]
        api_key = options["api_key"]
        model = options["model"]
        max_tokens = options["max_tokens"]
        temperature = options["temperature"]

        # Check if configuration already exists
        if AIConfiguration.objects.filter(name=name).exists():
            self.stdout.write(
                self.style.ERROR(f"\nError: Configuration '{name}' already exists")
            )
            self.stdout.write(
                "Use the 'update' action to modify existing configuration"
            )
            return

        # Create configuration
        try:
            AIConfiguration.objects.create(
                name=name,
                provider=provider,
                api_key=api_key,
                model_name=model,
                max_tokens=max_tokens,
                temperature=temperature,
                is_active=False,  # Start as inactive until tested
            )

            self.stdout.write(
                self.style.SUCCESS(f"\n✓ Configuration '{name}' created successfully")
            )
            self.stdout.write("\nTest the configuration with:")
            self.stdout.write(f"  python manage.py manage_ai_config test --name {name}")
            self.stdout.write("\nActivate it with:")
            self.stdout.write(
                f"  python manage.py manage_ai_config update --name {name} --activate"
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n✗ Failed to create configuration: {e}")
            )

    def _update_configuration(self, options: dict[str, Any]) -> None:
        """
        Update an existing AI configuration.

        Args:
            options: Command options
        """
        self.stdout.write(self.style.SUCCESS("=== Updating AI Configuration ===\n"))

        name = options["name"]

        # Get configuration
        try:
            config = AIConfiguration.objects.get(name=name)
        except AIConfiguration.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"\nError: Configuration '{name}' not found")
            )
            return

        # Update fields
        updated = False

        if options.get("api_key"):
            config.api_key = options["api_key"]
            self.stdout.write("✓ Updated API key")
            updated = True

        if options.get("model"):
            config.model_name = options["model"]
            self.stdout.write(f"✓ Updated model to {options['model']}")
            updated = True

        if options.get("max_tokens") is not None:
            config.max_tokens = options["max_tokens"]
            self.stdout.write(f"✓ Updated max tokens to {options['max_tokens']}")
            updated = True

        if options.get("temperature") is not None:
            config.temperature = options["temperature"]
            self.stdout.write(f"✓ Updated temperature to {options['temperature']}")
            updated = True

        if options.get("activate"):
            # Deactivate other configurations
            AIConfiguration.objects.filter(is_active=True).update(is_active=False)
            config.is_active = True
            self.stdout.write(self.style.SUCCESS(f"✓ Activated configuration '{name}'"))
            updated = True

        if options.get("deactivate"):
            config.is_active = False
            self.stdout.write(f"✓ Deactivated configuration '{name}'")
            updated = True

        if updated:
            config.save()
            self.stdout.write(
                self.style.SUCCESS(f"\n✓ Configuration '{name}' updated successfully")
            )
        else:
            self.stdout.write("\nNo changes made")

    def _test_configuration(self, options: dict[str, Any]) -> None:
        """
        Test AI configuration connectivity.

        Args:
            options: Command options
        """
        self.stdout.write(self.style.SUCCESS("=== Testing AI Configuration ===\n"))

        use_env = options.get("use_env", False)
        config_name = options.get("name")

        try:
            if use_env:
                self.stdout.write("Testing environment configuration...\n")
                adapter = AIAdapterFactory.create_adapter(config_source="env")
                self.stdout.write(f"  Model: {adapter.model}")
            else:
                if config_name:
                    self.stdout.write(f"Testing configuration '{config_name}'...\n")
                    adapter = AIAdapterFactory.create_adapter(
                        config_source="db",
                        config_name=config_name,
                    )
                else:
                    # Try to find active configuration
                    active_config = AIConfiguration.objects.filter(
                        is_active=True
                    ).first()
                    if not active_config:
                        self.stdout.write(
                            self.style.ERROR(
                                "\nNo active configuration found. "
                                "Specify --name or use --use-env"
                            )
                        )
                        return

                    self.stdout.write(
                        f"Testing active configuration '{active_config.name}'...\n"
                    )
                    adapter = AIAdapterFactory.create_adapter(
                        config_source="db",
                        config_name=active_config.name,
                    )

            # Test credentials
            self.stdout.write("Validating credentials...")
            adapter.validate_credentials()
            self.stdout.write(
                self.style.SUCCESS("\n✓ AI configuration is valid and working")
            )

            # Test a simple message
            self.stdout.write("\nTesting message generation...")
            test_messages = [{"role": "user", "content": "Hi"}]
            response = adapter.send_message(test_messages)

            self.stdout.write(self.style.SUCCESS("✓ Message generation successful"))
            self.stdout.write(f"\nResponse: {response['content'][:100]}...")

            if "metadata" in response:
                tokens = response["metadata"].get("tokens_used", {})
                self.stdout.write(f"\nTokens used: {tokens.get('total_tokens', 'N/A')}")

        except AuthenticationError as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Authentication failed: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Test failed: {e}"))
