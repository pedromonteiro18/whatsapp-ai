# WhatsApp AI Chatbot

A production-ready Django application that enables users to interact with AI assistants through WhatsApp. The system receives WhatsApp messages via webhooks, processes them through configurable AI providers (OpenAI, Anthropic via OpenRouter), and returns intelligent responses while maintaining conversation context.

## Features

### Core Features
- **WhatsApp Integration**: Seamless integration with WhatsApp Business API via Twilio
- **Multi-AI Provider Support**: Configurable adapters for OpenAI, Anthropic, and custom AI APIs via OpenRouter
- **Conversation Management**: Maintains conversation context with automatic expiration using Redis
- **Asynchronous Processing**: Celery-based task queue for reliable message processing
- **Security**: Webhook signature verification, API key encryption, rate limiting, and input sanitization
- **Error Handling**: Comprehensive error handling with user-friendly messages and admin notifications
- **Scalability**: Horizontal scaling support with Redis caching and Celery workers
- **Docker Support**: Complete Docker setup for easy deployment
- **Admin Interface**: Django admin for managing configurations and monitoring conversations

### Resort Activity Booking System
- **Activity Management**: Create and manage resort activities with images, pricing, and availability
- **WhatsApp Booking**: Conversational booking experience through WhatsApp chatbot
- **AI-Powered Recommendations**: Personalized activity suggestions based on user preferences
- **Real-Time Availability**: Dynamic time slot management with capacity tracking
- **Two-Step Confirmation**: Bookings initiated via WhatsApp require web app confirmation
- **React Web App**: Visual interface for browsing activities and managing bookings
- **User Preferences**: Track and learn from user interests for better recommendations
- **Admin Dashboard**: Comprehensive admin interface for managing activities, bookings, and time slots

## Architecture

```
WhatsApp User → Twilio API → Django Webhook → Celery Task → AI API
                                    ↓                           ↓
                              PostgreSQL ← Redis Cache ← Response
                                    ↓
                            WhatsApp User ← Twilio API
```

## Project Structure

```
whatsapp-ai-chatbot/
├── chatbot_core/              # Core application logic
│   ├── management/            # Django management commands
│   ├── migrations/            # Database migrations
│   ├── config.py              # Configuration management
│   ├── conversation_manager.py # Conversation state management
│   ├── message_processor.py  # Message processing logic
│   ├── error_handler.py       # Error handling utilities
│   ├── rate_limiter.py        # Rate limiting
│   ├── sanitizer.py           # Input sanitization
│   ├── tasks.py               # Celery tasks
│   └── models.py              # Database models
├── whatsapp/                  # WhatsApp integration
│   ├── client.py              # WhatsApp message sending
│   ├── views.py               # Webhook endpoints
│   └── utils.py               # Webhook verification
├── ai_integration/            # AI provider adapters
│   ├── adapters/              # AI adapter implementations
│   │   ├── base.py            # Base adapter interface
│   │   └── openrouter_adapter.py # OpenRouter adapter
│   └── factory.py             # Adapter factory
├── booking_system/            # Resort activity booking system
│   ├── migrations/            # Database migrations
│   ├── models.py              # Activity, Booking, TimeSlot models
│   ├── admin.py               # Django admin configuration
│   ├── services.py            # Business logic layer
│   ├── serializers.py         # DRF serializers
│   ├── views.py               # API viewsets
│   ├── tasks.py               # Celery tasks for bookings
│   └── urls.py                # URL routing
├── whatsapp_ai_chatbot/       # Django project settings
│   ├── settings.py            # Django settings
│   ├── urls.py                # URL routing
│   ├── celery.py              # Celery configuration
│   └── wsgi.py                # WSGI application
├── .kiro/specs/               # Feature specifications
│   └── resort-activity-booking/ # Booking system spec
│       ├── requirements.md    # Feature requirements
│       ├── design.md          # Architecture & design
│       └── tasks.md           # Implementation tasks
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker services configuration
├── Dockerfile                 # Application container
├── docker-entrypoint.sh       # Container startup script
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Prerequisites

### Required Software

#### Backend
- **Python 3.12+**: Application runtime
- **PostgreSQL 16+**: Primary database for persistent storage
- **Redis 7+**: Cache and message broker for Celery
- **Docker & Docker Compose** (optional): For containerized deployment

#### Frontend
- **Node.js 18+**: JavaScript runtime for React app
- **npm 8+**: Package manager (comes with Node.js)

### Required Accounts

- **Twilio Account**: For WhatsApp Business API access
  - WhatsApp-enabled phone number
  - Account SID and Auth Token
- **AI API Key**: One of the following:
  - OpenRouter API key (supports multiple AI providers)
  - OpenAI API key
  - Anthropic API key

## Quick Start Guide

### Option 1: Docker (Recommended)

The fastest way to get started with the backend:

```bash
# 1. Clone the repository
git clone <repository-url>
cd whatsapp-ai-chatbot

# 2. Copy and configure environment variables
cp .env.example .env
# Edit .env with your credentials (see Environment Variables section)

# 3. Start all services
docker-compose up --build

# 4. In a new terminal, run migrations
docker-compose exec web python manage.py migrate

# 5. Create admin user
docker-compose exec web python manage.py createsuperuser

# 6. Access the backend
# - API: http://localhost:8000
# - Admin: http://localhost:8000/admin
```

#### Start the Frontend

```bash
# 7. In a new terminal, navigate to frontend directory
cd frontend

# 8. Install dependencies
npm install

# 9. Copy environment file
cp .env.example .env
# Edit if needed (default points to http://localhost:8000)

# 10. Start development server
npm run dev

# 11. Access the web app
# - Frontend: http://localhost:5173
```

### Option 2: Local Development

For development without Docker:

#### Backend Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd whatsapp-ai-chatbot

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up PostgreSQL and Redis
# Make sure PostgreSQL and Redis are running locally

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your configuration

# 6. Run migrations
python manage.py migrate

# 7. Create superuser
python manage.py createsuperuser

# 8. Start Django development server
python manage.py runserver

# 9. In separate terminals, start Celery services
# Terminal 2: Celery worker
celery -A whatsapp_ai_chatbot worker --loglevel=info

# Terminal 3: Celery beat (periodic tasks)
celery -A whatsapp_ai_chatbot beat --loglevel=info
```

#### Frontend Setup

```bash
# 10. In a new terminal, navigate to frontend directory
cd frontend

# 11. Install Node.js dependencies
npm install

# 12. Copy environment file
cp .env.example .env

# 13. Start Vite dev server
npm run dev

# Frontend will be available at http://localhost:5173
```

## Environment Variables

### Django Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Django secret key for cryptographic signing |
| `DEBUG` | No | `False` | Enable debug mode (never use True in production) |
| `ALLOWED_HOSTS` | Yes | - | Comma-separated list of allowed hosts (e.g., `localhost,yourdomain.com`) |

### Database Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_NAME` | Yes | - | PostgreSQL database name |
| `DB_USER` | Yes | - | PostgreSQL username |
| `DB_PASSWORD` | Yes | - | PostgreSQL password |
| `DB_HOST` | Yes | `localhost` | PostgreSQL host |
| `DB_PORT` | No | `5432` | PostgreSQL port |

### Redis Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_HOST` | Yes | `localhost` | Redis host |
| `REDIS_PORT` | No | `6379` | Redis port |
| `REDIS_DB` | No | `0` | Redis database number |

### Twilio/WhatsApp Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TWILIO_ACCOUNT_SID` | Yes | - | Twilio account SID from console |
| `TWILIO_AUTH_TOKEN` | Yes | - | Twilio auth token from console |
| `TWILIO_WHATSAPP_NUMBER` | Yes | - | WhatsApp-enabled number (format: `whatsapp:+14155238886`) |
| `SKIP_WEBHOOK_SIGNATURE_VERIFICATION` | No | `False` | Skip Twilio signature verification (dev only, never in production) |

### AI Provider Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_PROVIDER` | Yes | `openrouter` | AI provider (`openrouter`, `openai`, `anthropic`) |
| `AI_API_KEY` | Yes | - | API key for the selected AI provider |
| `AI_MODEL` | No | `openai/gpt-4` | Model identifier (provider-specific) |
| `AI_MAX_TOKENS` | No | `1000` | Maximum tokens in AI response |
| `AI_TEMPERATURE` | No | `0.7` | AI temperature (0.0-1.0) |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | OpenRouter API base URL |

### Application Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MAX_CONVERSATION_HISTORY` | No | `10` | Maximum messages to include in conversation context |
| `SESSION_TIMEOUT_MINUTES` | No | `30` | Conversation session timeout in minutes |
| `RATE_LIMIT_MESSAGES_PER_MINUTE` | No | `10` | Legacy rate limit setting (messages per minute) |
| `RATE_LIMIT_MAX_REQUESTS` | No | `10` | Maximum requests per rate limit window |
| `RATE_LIMIT_WINDOW_SECONDS` | No | `60` | Rate limit window duration in seconds |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### Booking System Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOOKING_WEB_APP_URL` | Yes | - | Public URL of the React frontend for booking confirmations |
| `BOOKING_PENDING_TIMEOUT_MINUTES` | No | `30` | Time limit for pending booking confirmation |
| `BOOKING_CANCELLATION_DEADLINE_HOURS` | No | `24` | Hours before activity when cancellation is allowed |

### Example .env File

```bash
# Django
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DB_NAME=whatsapp_chatbot
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
SKIP_WEBHOOK_SIGNATURE_VERIFICATION=False

# AI Provider (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AI_MODEL=openai/gpt-4
AI_MAX_TOKENS=500
AI_TEMPERATURE=0.7

# Legacy OpenAI (if not using OpenRouter)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4

# Application Settings
MAX_CONVERSATION_HISTORY=10
SESSION_TIMEOUT_MINUTES=30

# Rate Limiting
RATE_LIMIT_MESSAGES_PER_MINUTE=10
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Booking System
BOOKING_WEB_APP_URL=http://localhost:5173
BOOKING_PENDING_TIMEOUT_MINUTES=30
BOOKING_CANCELLATION_DEADLINE_HOURS=24
```

## Services Overview

The application consists of multiple services that work together:

| Service | Port | Description |
|---------|------|-------------|
| **Web (Django)** | 8000 | Django application serving API and admin interface |
| **Frontend (React)** | 5173 | React web app for activity browsing and booking management |
| **PostgreSQL** | 5432 | Primary database for persistent storage |
| **Redis** | 6379 | Cache and message broker for Celery |
| **Celery Worker** | - | Background task processor for async message handling |
| **Celery Beat** | - | Periodic task scheduler for cleanup jobs |

## Authentication System

The application includes a phone-based authentication system for the web frontend:

### How It Works

1. **OTP Request**: User enters their phone number on the login page
2. **WhatsApp Delivery**: 6-digit OTP code is sent via WhatsApp using Twilio
3. **Verification**: User enters the OTP code to verify their identity
4. **Session Token**: Upon successful verification, a session token is issued and stored in Redis
5. **Authenticated Requests**: Frontend includes the session token in API requests

### Key Features

- **Phone-based**: No passwords required, users authenticate with their phone number
- **WhatsApp OTP**: Leverages existing Twilio/WhatsApp integration
- **Rate Limited**: Maximum 3 OTP requests per 10 minutes per phone number
- **Time-bound**: OTP expires after 5 minutes
- **Secure Sessions**: Session tokens stored in Redis with configurable expiry
- **Stateless API**: Session token validates each request without server-side session state

### Endpoints

- `POST /api/v1/auth/request-otp/`: Request OTP code for phone number
- `POST /api/v1/auth/verify-otp/`: Verify OTP and receive session token
- `POST /api/v1/auth/logout/`: Invalidate session token

### Security Considerations

- OTP codes are single-use and expire after verification
- Rate limiting prevents brute force attacks
- Session tokens are stored in Redis with TTL
- All booking endpoints require valid authentication

## Booking System

The Resort Activity Booking System enables guests to discover and book resort activities through both WhatsApp and a web interface.

### Key Components

1. **Data Models**
   - **Activity**: Resort activities with pricing, duration, and capacity
   - **ActivityImage**: Multiple images per activity
   - **TimeSlot**: Available booking slots with capacity tracking
   - **Booking**: User reservations with status workflow
   - **UserPreference**: AI recommendation preferences

2. **Admin Interface**
   - Manage activities with inline image uploads
   - View and manage time slots with availability status
   - Process bookings with bulk confirm/cancel actions
   - Track user preferences for recommendations

3. **Booking Workflow**
   - Guest browses activities via WhatsApp chatbot
   - AI provides personalized recommendations
   - Guest initiates booking through conversation
   - System creates pending booking (30-minute hold)
   - Guest confirms via web app within time limit
   - System sends WhatsApp confirmation

### Accessing the Admin

1. Navigate to `http://localhost:8000/admin`
2. Go to "Booking System" section
3. Manage:
   - Activities and images
   - Time slots and availability
   - Bookings and confirmations
   - User preferences

### Database Models

The booking system includes the following models:

- **Activity**: Core activity information (name, description, category, pricing)
- **ActivityImage**: Activity photos with ordering and primary image designation
- **TimeSlot**: Available booking times with capacity constraints
- **Booking**: User reservations with status tracking (pending, confirmed, cancelled, completed)
- **UserPreference**: User interests and preferences for AI recommendations

For detailed specifications, see `.kiro/specs/resort-activity-booking/`

## Management Commands

The application includes several management commands for administration:

### Test WhatsApp Integration

```bash
# Test sending a message
python manage.py test_whatsapp --phone "+1234567890" --message "Test message"

# Check configuration only
python manage.py test_whatsapp --check-config
```

### Manage AI Configuration

```bash
# List all AI configurations
python manage.py manage_ai_config list

# Create new configuration
python manage.py manage_ai_config create

# Update existing configuration
python manage.py manage_ai_config update <config_id>

# Test AI connectivity
python manage.py manage_ai_config test
```

### Validate Configuration

```bash
# Validate all environment variables and settings
python manage.py validate_config
```

## Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test chatbot_core
python manage.py test whatsapp

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Code Quality

```bash
# Type checking with mypy
mypy .

# Code formatting with black (optional)
black .

# Linting with flake8 (optional)
flake8 .
```

### Accessing Django Admin

1. Navigate to `http://localhost:8000/admin`
2. Log in with superuser credentials
3. Manage:
   - Conversations and messages
   - AI configurations
   - Webhook logs
   - User accounts

## Monitoring and Logs

### Application Logs

Logs are stored in the `logs/` directory:

- `logs/whatsapp_chatbot.log`: General application logs
- `logs/errors.log`: Error-specific logs

### Docker Logs

```bash
# View all service logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs web
docker-compose logs celery_worker
docker-compose logs celery_beat
```

### Health Check

The application includes a health check endpoint:

```bash
# Check application health
curl http://localhost:8000/health/

# Response includes database and Redis status
```

## Deployment

### Production Checklist

Before deploying to production:

- [ ] Set `DEBUG=False` in environment variables
- [ ] Generate a strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use strong database passwords
- [ ] Enable HTTPS/SSL
- [ ] Set up proper firewall rules
- [ ] Configure backup strategy for PostgreSQL
- [ ] Set up monitoring and alerting
- [ ] Review and adjust rate limiting settings
- [ ] Configure log rotation
- [ ] Set up Redis persistence if needed

### Docker Production Deployment

```bash
# Build production image
docker-compose -f docker-compose.yml build

# Start services in detached mode
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Scaling

To scale Celery workers:

```bash
# Scale to 3 worker instances
docker-compose up -d --scale celery_worker=3
```

## Troubleshooting

### Common Issues

**Issue**: Webhook not receiving messages
- Verify Twilio webhook URL is configured correctly
- Check that the application is accessible from the internet (use ngrok/Serveo for local testing)
- **Important**: Add your tunnel domain (ngrok/Serveo) to `ALLOWED_HOSTS` in .env and restart Django
- Verify webhook signature validation is working

**Issue**: AI API errors
- Check API key is valid and has sufficient credits
- Verify the AI provider and model name are correct
- Check rate limits on your AI provider account

**Issue**: Database connection errors
- Verify PostgreSQL is running
- Check database credentials in .env
- Ensure database exists and migrations are applied

**Issue**: Redis connection errors
- Verify Redis is running
- Check Redis host and port in .env
- Test Redis connection: `redis-cli ping`

**Issue**: Celery tasks not processing

- Check Celery worker is running
- Verify Redis connection (Celery broker)
- Check Celery logs for errors

**Issue**: Frontend cannot connect to backend API

- Verify backend is running on <http://localhost:8000>
- Check VITE_API_URL in frontend/.env matches backend URL
- Check browser console for CORS errors
- Ensure CORS_ALLOWED_ORIGINS in Django settings includes frontend URL

**Issue**: Authentication not working

- Verify Redis is running (OTP and session tokens stored in Redis)
- Check Twilio credentials for OTP delivery
- Verify BOOKING_WEB_APP_URL is set correctly
- Check browser localStorage for session token

### Debug Mode

To enable detailed logging:

```bash
# Set in .env
DEBUG=True
LOG_LEVEL=DEBUG
```

**Warning**: Never use `DEBUG=True` in production!

## Security Best Practices

1. **Never commit secrets**: Keep `.env` file out of version control
2. **Use strong passwords**: For database and admin accounts
3. **Enable HTTPS**: Always use SSL/TLS in production
4. **Regular updates**: Keep dependencies up to date
5. **Rate limiting**: Configure appropriate rate limits
6. **Input validation**: The application sanitizes inputs, but review for your use case
7. **Webhook verification**: Always enabled for Twilio webhooks
8. **API key rotation**: Regularly rotate API keys

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and type checking
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review application logs
- Open an issue on GitHub

## License

MIT License - See LICENSE file for details