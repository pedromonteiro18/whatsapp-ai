# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WhatsApp AI Chatbot built with Django 5.1, Celery, and Twilio. The system handles asynchronous WhatsApp message processing with AI-powered responses (OpenAI, Anthropic), conversation management, and comprehensive security features.

## Architecture

### Request Flow

```
WhatsApp User → Twilio API → Django Webhook → Celery Task → AI API
                                    ↓                           ↓
                              PostgreSQL ← Redis Cache ← Response
                                    ↓
                            WhatsApp User ← Twilio API
```

### Key Components and Design Patterns

1. **Webhook Receiver** (`whatsapp/views.py:WhatsAppWebhookView`)
   - Validates Twilio signature before processing
   - Queues messages to Celery for async processing
   - Returns 200 immediately to prevent Twilio timeout

2. **Message Processor** (`chatbot_core/message_processor.py:MessageProcessor`)
   - **Facade pattern**: Orchestrates conversation, AI, database, Redis, WhatsApp
   - Atomic database transactions with Django's `transaction.atomic()`
   - Two-level exception handling: known AI errors vs unexpected errors
   - Reference: `process_message()` method

3. **Conversation Manager** (`chatbot_core/conversation_manager.py`)
   - Redis-based conversation context with TTL expiration
   - Sliding window: maintains last N messages (configurable)
   - Uses Redis sorted sets for time-based retrieval

4. **AI Adapters** (`ai_integration/adapters/`)
   - **Strategy pattern**: Abstract `AIAdapter` base class
   - OpenRouter adapter supports multiple providers (OpenAI, Anthropic, Llama)
   - Factory pattern in `factory.py` for adapter instantiation

5. **Error Handler** (`chatbot_core/error_handler.py`)
   - **Error categorization**: WEBHOOK, AI, DATABASE, WHATSAPP, SYSTEM, CONFIGURATION
   - **Severity levels**: LOW, MEDIUM, HIGH, CRITICAL
   - Redis-based rate limiting for admin alerts (1 alert/hour per error type)

6. **Security Layer** (3 layers of defense-in-depth):
   - **Layer 1**: Rate limiting (Redis token bucket, `rate_limiter.py`)
   - **Layer 2**: Input sanitization (XSS prevention, phone validation, `sanitizer.py`)
   - **Layer 3**: HTTP security headers (HSTS, CSP, XSS filters, `settings.py:268-321`)

### Django Apps Structure

- **chatbot_core**: Core business logic
  - `message_processor.py`: Main orchestration (coordinates all subsystems)
  - `conversation_manager.py`: Redis state management with sliding window
  - `config.py`: Centralized config with validation (loads from environment)
  - `error_handler.py`: Categorized error handling with admin notifications
  - `rate_limiter.py`: Per-user rate limiting with Redis atomic operations
  - `sanitizer.py`: Input validation (E.164 phone format, XSS prevention)
  - `health.py`: Health check endpoint (verifies DB + Redis connectivity)
  - `tasks.py`: Celery tasks with retry logic
  - `models.py`: Conversation, Message, AIConfiguration, WebhookLog (all use UUID PKs)

- **whatsapp**: Twilio/WhatsApp integration
  - `client.py`: WhatsAppClient for sending messages via Twilio SDK
  - `views.py`: Webhook endpoint with Twilio signature verification
  - `utils.py`: Webhook validation using Twilio's request validator

- **ai_integration**: Multi-provider AI abstraction
  - `adapters/base.py`: Abstract AIAdapter interface (send_message, validate_credentials)
  - `adapters/openrouter_adapter.py`: OpenRouter implementation (unified API for multiple models)
  - `factory.py`: Adapter factory based on configuration

### Data Models (all use UUID primary keys)

- **Conversation**: User session (user_phone, is_active, last_activity with auto_now)
- **Message**: Chat history (role: user/assistant/system, content, metadata as JSONField)
- **AIConfiguration**: Provider settings (encrypted API keys via django-encrypted-model-fields)
- **WebhookLog**: Audit trail (headers, body, response_status, processing_time)

### Configuration System

**Config class** (`chatbot_core/config.py`):
- Loads from environment via `python-decouple`
- `validate()` returns `(bool, list[str])` tuple
- `validate_required()` raises `ImproperlyConfigured` if validation fails
- `get_ai_api_key()`: Prioritizes OPENROUTER_API_KEY, falls back to OPENAI_API_KEY
- `get_ai_model()`: Returns provider/model format (e.g., "openai/gpt-4", "anthropic/claude-3-sonnet")
- `CONVERSATION_TTL_SECONDS`: Auto-calculated from SESSION_TIMEOUT_MINUTES * 60

## Development Commands

### Setup and Database
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Validate configuration (tests DB, Redis, Twilio, AI API connectivity)
python manage.py validate_config

# Skip external service tests (faster, config-only validation)
python manage.py validate_config --skip-external
```

### Running Services

**Option 1: Native Local Development** (fastest iteration)
```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: Celery worker
celery -A whatsapp_ai_chatbot worker --loglevel=info

# Terminal 3: Celery beat scheduler (periodic tasks)
celery -A whatsapp_ai_chatbot beat --loglevel=info
```

**Option 2: Docker** (simplest setup)
```bash
# Start all services (Django + PostgreSQL + Redis + Celery + Beat)
docker-compose up --build

# Run migrations in Docker
docker-compose exec web python manage.py migrate

# Create superuser in Docker
docker-compose exec web python manage.py createsuperuser

# View logs
docker-compose logs -f web
```

**Option 3: Hybrid** (recommended for active development)
```bash
# Start infrastructure in Docker
docker-compose up db redis

# Run Django/Celery natively (in separate terminals)
python manage.py runserver
celery -A whatsapp_ai_chatbot worker --loglevel=info
celery -A whatsapp_ai_chatbot beat --loglevel=info
```

### Management Commands

**Test WhatsApp Integration:**
```bash
# Send test message
python manage.py test_whatsapp --to "+1234567890" --message "Test"

# Check configuration only (no message sent)
python manage.py test_whatsapp --check-config
```

**Manage AI Configuration:**
```bash
# List all AI configurations
python manage.py manage_ai_config list

# Create new configuration (interactive prompts)
python manage.py manage_ai_config create \
  --name "Production" \
  --provider openrouter \
  --api-key sk-or-v1-xxx \
  --model openai/gpt-4

# Test AI connectivity
python manage.py manage_ai_config test

# Activate specific configuration
python manage.py manage_ai_config update --activate
```

### Testing and Quality

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test chatbot_core
python manage.py test chatbot_core.tests.test_message_processor

# Type checking (entire project)
mypy .

# Type check specific files
mypy chatbot_core/message_processor.py ai_integration/

# Code formatting (modifies files in-place)
black .

# Check formatting without modifying
black --check .

# Linting
flake8 .
```

### Docker Management

```bash
# Start services in background
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (deletes database data)
docker-compose down -v

# Restart specific service
docker-compose restart web

# Scale Celery workers (horizontal scaling)
docker-compose up -d --scale celery_worker=3

# Execute Django commands in container
docker-compose exec web python manage.py <command>

# Access Django shell in container
docker-compose exec web python manage.py shell

# Access PostgreSQL in container
docker-compose exec db psql -U postgres -d whatsapp_chatbot
```

## Code Style Configuration

- **Black**: Line length 88, excludes migrations and venv
- **Flake8**: Max line 88, ignores E203 (whitespace before ':') and W503 (line break before binary operator)
- **MyPy** (`mypy.ini`):
  - Python 3.12 target
  - Django plugin enabled (`django_settings_module = whatsapp_ai_chatbot.settings`)
  - Ignores missing imports for: celery, twilio, openai, decouple, psycopg2
  - Special handling for management commands: `[[tool.mypy.overrides]]` disables attr-defined errors
  - Migrations completely ignored

## Environment Variables

**Critical for functionality** (see `.env.example` for complete list):

**Database:**
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: PostgreSQL credentials
- `DB_HOST`: Use `db` for Docker, `localhost` for native/hybrid
- `DB_PORT`: Default 5432

**Redis:**
- `REDIS_HOST`: Use `redis` for Docker, `localhost` for native/hybrid
- `REDIS_PORT`: Default 6379
- `REDIS_DB`: Default 0

**Celery:**
- `CELERY_BROKER_URL`: Redis URL (e.g., `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND`: Same as broker URL

**Twilio:**
- `TWILIO_ACCOUNT_SID`: Starts with `AC...`
- `TWILIO_AUTH_TOKEN`: From Twilio console
- `TWILIO_WHATSAPP_NUMBER`: Format `whatsapp:+14155238886`
- `SKIP_WEBHOOK_SIGNATURE_VERIFICATION`: Set to `True` to skip signature verification (development only, never in production)

**AI Provider** (choose one):
- **OpenRouter**: `OPENROUTER_API_KEY`, `AI_MODEL=openai/gpt-4`
- **OpenAI**: `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4`
- **Anthropic**: `OPENAI_API_KEY` (reused), `AI_MODEL=anthropic/claude-3-sonnet`

**Application:**
- `MAX_CONVERSATION_HISTORY`: Number of messages in context window (default: 10)
- `SESSION_TIMEOUT_MINUTES`: Conversation TTL (default: 30)
- `RATE_LIMIT_MESSAGES_PER_MINUTE`: Legacy rate limit setting (default: 10)
- `RATE_LIMIT_MAX_REQUESTS`: Messages per window (default: 10)
- `RATE_LIMIT_WINDOW_SECONDS`: Rate limit window in seconds (default: 60)

## Logging

**Log files** (`logs/` directory):
- `whatsapp_chatbot.log`: General application logs (10MB rotating, 5 backups)
- `errors.log`: ERROR level only (10MB rotating, 5 backups)

**Separate loggers** (all configurable in `settings.py:191-266`):
- `django`: Django framework logs
- `chatbot_core`: Message processing, conversation management
- `whatsapp`: Twilio webhook and client logs
- `ai_integration`: AI adapter logs
- `celery`: Task execution logs

**Log level in dev**: Use `DEBUG` in `.env` or set specific logger levels in `settings.py`

## Type Checking Notes

- **Django models**: Use `TYPE_CHECKING` blocks for reverse relation type hints to avoid circular imports
- **Management commands**: MyPy config disables `attr-defined` errors (Django's command framework uses dynamic attributes)
- **Celery tasks**: Use `from typing import Any` and type `self: Any` in `@shared_task(bind=True)` methods
- **Third-party stubs**: Missing imports for Twilio, OpenAI, Celery are ignored in `mypy.ini`

## Architecture Patterns Reference

**When adding new features:**
1. **New AI provider**: Create adapter in `ai_integration/adapters/`, extend factory
2. **New error category**: Add to `ErrorCategory` enum in `error_handler.py`
3. **New management command**: Create in `chatbot_core/management/commands/`
4. **New Celery task**: Add to `chatbot_core/tasks.py`, configure in `celery.py` if periodic
5. **New security check**: Add to `Sanitizer` class or create middleware

**Key architectural decisions:**
- **Conversation persistence**: Database (PostgreSQL) for durability, Redis for hot context
- **Message queuing**: Celery ensures at-least-once delivery (webhook returns 200 immediately)
- **AI abstraction**: Strategy pattern allows switching providers without code changes
- **Rate limiting**: Redis atomic operations prevent race conditions in distributed systems
- **Error handling**: Two-level catch: known errors (user-friendly) vs unexpected (generic message)
