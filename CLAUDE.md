# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WhatsApp AI Chatbot built with Django 5.1, Celery, and Twilio. The system handles asynchronous WhatsApp message processing with AI-powered responses (OpenAI, Anthropic), conversation management, and comprehensive security features.

## Project Structure

This is a **monorepo** with clear separation of concerns:

```
whatsapp-ai/
├── backend/                    # Django backend
│   ├── chatbot_core/           # Core business logic
│   ├── whatsapp/               # Twilio/WhatsApp integration
│   ├── ai_integration/         # AI provider adapters
│   ├── booking_system/         # Activity booking system
│   ├── whatsapp_ai_chatbot/    # Django project settings
│   ├── manage.py               # Django management script
│   ├── requirements.txt        # Python dependencies
│   └── mypy.ini                # Type checking config
├── frontend/                   # React web app (Vite + TypeScript)
│   ├── src/                    # React components, pages, services
│   ├── package.json            # Node dependencies
│   └── vite.config.ts          # Vite configuration
├── infrastructure/             # Infrastructure configs
│   ├── docker/                 # Docker files
│   │   ├── Dockerfile.backend  # Backend container
│   │   └── docker-entrypoint.sh# Container startup script
│   └── docker-compose.yml      # Service orchestration
├── docs/                       # Project documentation
│   ├── SETUP.md                # Setup instructions
│   ├── API_DOCUMENTATION.md    # API reference
│   └── DEV_AUTH.md             # Authentication guide
├── logs/                       # Application logs
├── .kiro/specs/                # Feature specifications
├── README.md                   # Main project readme
├── CLAUDE.md                   # This file (AI assistant guide)
└── .env.example                # Environment variable template
```

**Key Points:**
- All Python imports use `backend.` prefix (e.g., `from backend.chatbot_core.models import Message`)
- Commands run from project root: `python backend/manage.py runserver`
- Docker Compose: `docker-compose -f infrastructure/docker-compose.yml up`
- Frontend is independent with its own build process
- Infrastructure configs are centralized in `infrastructure/`
- Documentation centralized in `docs/` directory

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

1. **Webhook Receiver** (`backend/whatsapp/views.py:WhatsAppWebhookView`)
   - Validates Twilio signature before processing
   - Queues messages to Celery for async processing
   - Returns 200 immediately to prevent Twilio timeout

2. **Message Processor** (`backend/chatbot_core/message_processor.py:MessageProcessor`)
   - **Facade pattern**: Orchestrates conversation, AI, database, Redis, WhatsApp
   - Atomic database transactions with Django's `transaction.atomic()`
   - Two-level exception handling: known AI errors vs unexpected errors
   - Reference: `process_message()` method

3. **Conversation Manager** (`backend/chatbot_core/conversation_manager.py`)
   - Redis-based conversation context with TTL expiration
   - Sliding window: maintains last N messages (configurable)
   - Uses Redis sorted sets for time-based retrieval

4. **AI Adapters** (`backend/ai_integration/adapters/`)
   - **Strategy pattern**: Abstract `AIAdapter` base class
   - OpenRouter adapter supports multiple providers (OpenAI, Anthropic, Llama)
   - Factory pattern in `factory.py` for adapter instantiation

5. **Error Handler** (`backend/chatbot_core/error_handler.py`)
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
  - `booking_processor.py`: Processes booking-related messages from WhatsApp chatbot

- **whatsapp**: Twilio/WhatsApp integration
  - `client.py`: WhatsAppClient for sending messages via Twilio SDK
  - `views.py`: Webhook endpoint with Twilio signature verification
  - `utils.py`: Webhook validation using Twilio's request validator

- **ai_integration**: Multi-provider AI abstraction
  - `adapters/base.py`: Abstract AIAdapter interface (send_message, validate_credentials)
  - `adapters/openrouter_adapter.py`: OpenRouter implementation (unified API for multiple models)
  - `factory.py`: Adapter factory based on configuration

- **booking_system**: Resort activity booking system
  - `models.py`: Activity, TimeSlot, Booking, UserPreference, ActivityImage
  - `services.py`: Business logic layer (BookingService for all booking operations)
  - `views.py`: DRF viewsets for REST API endpoints
  - `serializers.py`: DRF serializers with validation
  - `auth.py`: OTP generation and phone number validation
  - `auth_views.py`: Authentication endpoints (request OTP, verify OTP, logout, current user)
  - `authentication.py`: SessionTokenAuthentication class for token-based auth
  - `permissions.py`: IsAuthenticatedWithSessionToken permission class
  - `notifications.py`: WhatsApp notification sending (booking confirmations, reminders)
  - `tasks.py`: Celery tasks (expire pending bookings, send reminders)
  - Booking flow: WhatsApp chatbot → Pending booking → Web app confirmation → WhatsApp notification

### Frontend Architecture (React + TypeScript + Vite)

**Tech Stack:**
- React 19 with TypeScript for type safety
- Vite for fast development and optimized builds
- React Router for client-side routing
- TanStack Query (React Query) for server state management
- Axios for HTTP requests
- Tailwind CSS v4 with Radix UI components
- shadcn/ui component library

**Key Components:**
- `AuthContext.tsx`: Global authentication state (phone number, session token, login/logout)
- `ProtectedRoute.tsx`: Route wrapper requiring authentication
- `api/` directory: Axios clients and API service functions
- `pages/`: LoginPage, ActivitiesPage, ActivityDetailPage, BookingsPage
- `components/activities/`: ActivityCard, ActivityGrid, ActivityFilter
- `components/auth/`: PhoneInput, OTPForm
- `components/ui/`: shadcn components (button, card, input, etc.)

**Authentication Flow:**
1. User enters phone number → `api.requestOTP()` → Receives OTP via WhatsApp
2. User enters OTP → `api.verifyOTP()` → Receives session token
3. Token stored in localStorage and included in all authenticated requests
4. `AuthContext` provides `isAuthenticated`, `login()`, `logout()` globally
5. `ProtectedRoute` redirects unauthenticated users to `/login`

### Data Models (all use UUID primary keys)

**Chatbot Core:**
- **Conversation**: User session (user_phone, is_active, last_activity with auto_now)
- **Message**: Chat history (role: user/assistant/system, content, metadata as JSONField)
- **AIConfiguration**: Provider settings (encrypted API keys via django-encrypted-model-fields)
- **WebhookLog**: Audit trail (headers, body, response_status, processing_time)

**Booking System:**
- **Activity**: Resort activities (name, description, category, price_per_person, duration_minutes, max_capacity)
- **ActivityImage**: Multiple images per activity (image file, order, is_primary)
- **TimeSlot**: Available booking times (activity, start_time, end_time, available_capacity, is_active)
- **Booking**: User reservations (user_phone, activity, time_slot, num_people, status: pending/confirmed/cancelled/completed, total_price)
- **UserPreference**: AI recommendation preferences (user_phone, interests as JSONField, preferred_difficulty, preferred_duration)

### Configuration System

**Config class** (`backend/chatbot_core/config.py`):
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
python backend/manage.py migrate

# Create superuser
python backend/manage.py createsuperuser

# Validate configuration (tests DB, Redis, Twilio, AI API connectivity)
python backend/manage.py validate_config

# Skip external service tests (faster, config-only validation)
python backend/manage.py validate_config --skip-external
```

### Running Services

**Option 1: Native Local Development** (fastest iteration)
```bash
# Terminal 1: Django development server
python backend/manage.py runserver

# Terminal 2: Celery worker
celery -A backend.whatsapp_ai_chatbot worker --loglevel=info

# Terminal 3: Celery beat scheduler (periodic tasks)
celery -A backend.whatsapp_ai_chatbot beat --loglevel=info
```

**Option 2: Docker** (simplest setup)
```bash
# Start all services (Django + PostgreSQL + Redis + Celery + Beat)
docker-compose -f infrastructure/docker-compose.yml up --build

# Run migrations in Docker
docker-compose -f infrastructure/docker-compose.yml exec web python backend/manage.py migrate

# Create superuser in Docker
docker-compose -f infrastructure/docker-compose.yml exec web python backend/manage.py createsuperuser

# View logs
docker-compose logs -f web
```

**Option 3: Hybrid** (recommended for active development)
```bash
# Start infrastructure in Docker
docker-compose -f infrastructure/docker-compose.yml up db redis

# Run Django/Celery natively (in separate terminals)
python backend/manage.py runserver
celery -A backend.whatsapp_ai_chatbot worker --loglevel=info
celery -A backend.whatsapp_ai_chatbot beat --loglevel=info
```

### Management Commands

**Test WhatsApp Integration:**
```bash
# Send test message
python backend/manage.py test_whatsapp --to "+1234567890" --message "Test"

# Check configuration only (no message sent)
python backend/manage.py test_whatsapp --check-config
```

**Manage AI Configuration:**
```bash
# List all AI configurations
python backend/manage.py manage_ai_config list

# Create new configuration (interactive prompts)
python backend/manage.py manage_ai_config create \
  --name "Production" \
  --provider openrouter \
  --api-key sk-or-v1-xxx \
  --model openai/gpt-4

# Test AI connectivity
python backend/manage.py manage_ai_config test

# Activate specific configuration
python backend/manage.py manage_ai_config update --activate
```

**Booking System Data Management:**
```bash
# Seed sample activities (creates example resort activities)
python backend/manage.py seed_activities

# Generate time slots for activities (creates available booking times)
# Options: --days N (number of days ahead, default 30), --slots-per-day N (default 4)
python backend/manage.py generate_timeslots --days 30 --slots-per-day 4

# Download themed activity images from Pexels API
# Requires PEXELS_API_KEY environment variable
# Downloads high-quality images based on activity categories
python backend/manage.py download_activity_images

# Example workflow for setting up a new booking system:
# 1. Create sample activities
python backend/manage.py seed_activities
# 2. Generate time slots
python backend/manage.py generate_timeslots --days 60
# 3. Download activity images (optional, requires Pexels API key)
python backend/manage.py download_activity_images
```

### Testing and Quality

**Backend (Python/Django):**
```bash
# Run all tests
python backend/manage.py test

# Run specific app tests
python backend/manage.py test backend.chatbot_core
python backend/manage.py test backend.whatsapp
python backend/manage.py test backend.booking_system

# Run specific test file
python backend/manage.py test backend.chatbot_core.tests.test_message_processor

# Run specific test class or method
python backend/manage.py test backend.chatbot_core.tests.test_message_processor.MessageProcessorTestCase
python backend/manage.py test backend.chatbot_core.tests.test_message_processor.MessageProcessorTestCase.test_process_message_success

# Run tests with verbosity
python backend/manage.py test --verbosity=2

# Run tests and keep test database
python backend/manage.py test --keepdb

# Type checking
cd backend && mypy .

# Type check specific module
cd backend && mypy chatbot_core/

# Code formatting (modifies files in-place)
cd backend && black .

# Check formatting without modifying
cd backend && black --check .

# Linting
cd backend && flake8 .

# Check specific app
cd backend && flake8 chatbot_core/
```

**Frontend (React/TypeScript):**
```bash
cd frontend

# Type checking
npm run build  # TypeScript compilation is part of build

# Linting
npm run lint

# Linting with auto-fix
npm run lint -- --fix
```

### Frontend Development

**Setup:**
```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env
```

**Development:**
```bash
# Start dev server (usually http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint TypeScript/React code
npm run lint
```

**Environment Variables** (`frontend/.env`):
- `VITE_API_URL`: Backend API URL (default: `http://localhost:8000`)

**CORS Configuration:**
- Backend must include frontend URL in `CORS_ALLOWED_ORIGINS` setting (`settings.py`)
- Default development setup allows `http://localhost:5173`
- For production, add your production frontend domain to CORS settings
- If using ngrok/Serveo for development, add tunnel domain to both `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`

**Key Frontend Files:**
- `src/api/client.ts`: Axios instance with auth interceptor
- `src/api/index.ts`: All API service functions
- `src/contexts/AuthContext.tsx`: Authentication state management
- `src/App.tsx`: Route definitions and QueryClient provider
- `src/main.tsx`: Application entry point

**Full-Stack Development Workflow:**
```bash
# Terminal 1: Start backend infrastructure (if using hybrid Docker approach)
docker-compose -f infrastructure/docker-compose.yml up db redis

# Terminal 2: Start Django
python backend/manage.py runserver

# Terminal 3: Start Celery worker
celery -A backend.whatsapp_ai_chatbot worker --loglevel=info

# Terminal 4: Start Celery beat (if using booking system)
celery -A backend.whatsapp_ai_chatbot beat --loglevel=info

# Terminal 5: Start frontend
cd frontend && npm run dev

# Access:
# - Backend API: http://localhost:8000
# - Frontend: http://localhost:5173
# - Django Admin: http://localhost:8000/admin
```

### Docker Management

```bash
# Start services in background
docker-compose -f infrastructure/docker-compose.yml up -d

# Stop all services
docker-compose -f infrastructure/docker-compose.yml down

# Stop and remove volumes (deletes database data)
docker-compose -f infrastructure/docker-compose.yml down -v

# Restart specific service
docker-compose restart web

# Scale Celery workers (horizontal scaling)
docker-compose -f infrastructure/docker-compose.yml up -d --scale celery_worker=3

# Execute Django commands in container
docker-compose -f infrastructure/docker-compose.yml exec web python backend/manage.py <command>

# Access Django shell in container
docker-compose -f infrastructure/docker-compose.yml exec web python backend/manage.py shell

# Access PostgreSQL in container
docker-compose -f infrastructure/docker-compose.yml exec db psql -U postgres -d whatsapp_chatbot
```

## Code Style Configuration

- **Black**: Line length 88, excludes migrations and venv
- **Flake8**: Max line 88, ignores E203 (whitespace before ':') and W503 (line break before binary operator)
- **MyPy** (`backend/mypy.ini`):
  - Python 3.12 target
  - Django plugin enabled (`django_settings_module = backend.whatsapp_ai_chatbot.settings`)
  - Ignores missing imports for: celery, twilio, openai, decouple, psycopg2
  - Special handling for management commands: disables attr-defined errors
  - Migrations completely ignored
- **ESLint** (`frontend/eslint.config.js`): React hooks rules, TypeScript strict checks
- **TypeScript** (`frontend/tsconfig.json`): Strict mode enabled

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

**Development Shortcuts:**
- `DEV_OTP_CODE`: Hardcoded OTP for development (e.g., `000000`). When set, this code will be accepted for login instead of requiring WhatsApp OTP delivery. Dramatically speeds up local development workflow. **NEVER set in production**.

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

**Booking System:**
- `BOOKING_WEB_APP_URL`: Public URL of React frontend for booking confirmations (required)
- `BOOKING_PENDING_TIMEOUT_MINUTES`: Time limit for pending booking confirmation (default: 30)
- `BOOKING_CANCELLATION_DEADLINE_HOURS`: Hours before activity when cancellation allowed (default: 24)

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
1. **New AI provider**: Create adapter in `backend/ai_integration/adapters/`, extend factory
2. **New error category**: Add to `ErrorCategory` enum in `backend/chatbot_core/error_handler.py`
3. **New management command**: Create in `backend/chatbot_core/management/commands/`
4. **New Celery task**: Add to app's `tasks.py`, configure in `backend/whatsapp_ai_chatbot/celery.py` if periodic
5. **New security check**: Add to `Sanitizer` class or create middleware
6. **New booking feature**: Add business logic to `BookingService`, create new endpoint in `views.py`, update serializers
7. **New frontend page**: Create in `frontend/src/pages/`, add route in `App.tsx`, create API service in `api/index.ts`

**Key architectural decisions:**
- **Conversation persistence**: Database (PostgreSQL) for durability, Redis for hot context
- **Message queuing**: Celery ensures at-least-once delivery (webhook returns 200 immediately)
- **AI abstraction**: Strategy pattern allows switching providers without code changes
- **Rate limiting**: Redis atomic operations prevent race conditions in distributed systems
- **Error handling**: Two-level catch: known errors (user-friendly) vs unexpected (generic message)
- **Booking workflow**: Two-step process (WhatsApp initiation → Web confirmation) prevents accidental bookings
- **Authentication**: Passwordless OTP via WhatsApp, session tokens in Redis with TTL
- **Frontend state**: TanStack Query for server state caching, AuthContext for global auth state

## Additional Resources

**Detailed Documentation:**
- `docs/SETUP.md`: Comprehensive setup guide with troubleshooting
- `docs/API_DOCUMENTATION.md`: Complete API reference with examples
- `docs/BOOKING_SYSTEM_README.md`: In-depth booking system documentation
- `docs/DEV_AUTH.md`: Authentication system details
- `docs/SERVEO_SETUP.md`: Guide for exposing local development server
- `docs/START_BACKEND.md`: Quick reference for starting backend services

**Feature Specifications:**
- `.kiro/specs/whatsapp-ai-chatbot/`: Original chatbot feature specs
- `.kiro/specs/resort-activity-booking/`: Booking system design and requirements

**System Prompt Configuration:**
The booking assistant uses a specialized system prompt configured in `backend/whatsapp_ai_chatbot/settings.py`. The prompt defines the AI's persona as a resort concierge and provides structured instructions for handling booking conversations. See `BOOKING_SYSTEM_README.md` for details on customizing the assistant's behavior.
