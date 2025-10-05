# WhatsApp AI Chatbot

An AI-powered WhatsApp chatbot built with Django, Celery, and OpenAI.

## Project Structure

```
whatsapp-ai/
├── chatbot_core/       # Core application logic
├── whatsapp/           # WhatsApp integration
├── ai_integration/     # OpenAI integration
├── whatsapp_ai_chatbot/  # Django project settings
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker services configuration
├── Dockerfile          # Application container
└── .env.example        # Environment variables template
```

## Prerequisites

- Python 3.12+
- PostgreSQL 16
- Redis 7
- Docker & Docker Compose (optional)

## Local Development Setup

### 1. Clone and Setup Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

### 6. Run Celery Worker (in separate terminal)

```bash
celery -A whatsapp_ai_chatbot worker --loglevel=info
```

### 7. Run Celery Beat (in separate terminal)

```bash
celery -A whatsapp_ai_chatbot beat --loglevel=info
```

## Docker Setup

### 1. Build and Start Services

```bash
docker-compose up --build
```

### 2. Run Migrations

```bash
docker-compose exec web python manage.py migrate
```

### 3. Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

## Configuration

### Required Environment Variables

- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: Database configuration
- `REDIS_HOST`, `REDIS_PORT`: Redis configuration
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`: Twilio credentials
- `OPENAI_API_KEY`: OpenAI API key

## Services

- **Web**: Django application (port 8000)
- **PostgreSQL**: Database (port 5432)
- **Redis**: Message broker and cache (port 6379)
- **Celery Worker**: Background task processor
- **Celery Beat**: Periodic task scheduler

## Development

### Running Tests

```bash
python manage.py test
```

### Code Style and Type Checking

```bash
# Type checking
mypy .

# Format code (optional)
black .

# Lint code (optional)
flake8 .
```

## License

MIT