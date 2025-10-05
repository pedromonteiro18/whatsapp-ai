# WhatsApp AI Chatbot - Detailed Setup Guide

This guide provides step-by-step instructions for setting up the WhatsApp AI Chatbot application, from creating necessary accounts to deploying the application.

## Table of Contents

1. [Prerequisites Setup](#prerequisites-setup)
2. [Twilio Account Setup](#twilio-account-setup)
3. [AI Provider Setup](#ai-provider-setup)
4. [Local Development Setup](#local-development-setup)
5. [Docker Deployment](#docker-deployment)
6. [Webhook Configuration](#webhook-configuration)
7. [Testing the Setup](#testing-the-setup)

---

## Prerequisites Setup

### 1. Install Required Software

#### Python 3.12+

**macOS** (using Homebrew):
```bash
brew install python@3.12
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

**Windows**:
Download from [python.org](https://www.python.org/downloads/)

#### PostgreSQL 16+

**macOS**:
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Ubuntu/Debian**:
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows**:
Download from [postgresql.org](https://www.postgresql.org/download/windows/)

#### Redis 7+

**macOS**:
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian**:
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows**:
Use [Redis for Windows](https://github.com/microsoftarchive/redis/releases) or WSL

#### Docker & Docker Compose (Optional)

**macOS**:
Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

**Ubuntu/Debian**:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin
```

**Windows**:
Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

---

## Twilio Account Setup

### Step 1: Create Twilio Account

1. Go to [Twilio Sign Up](https://www.twilio.com/try-twilio)
2. Fill in your details and verify your email
3. Complete phone verification
4. You'll receive free trial credits

### Step 2: Get WhatsApp Sandbox Access

For development and testing, use Twilio's WhatsApp Sandbox:

1. Log in to [Twilio Console](https://console.twilio.com/)
2. Navigate to **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Follow the instructions to join the sandbox:
   - Send the provided code (e.g., "join <your-code>") to the Twilio WhatsApp number
   - You'll receive a confirmation message

### Step 3: Get Your Credentials

1. In Twilio Console, go to **Account** → **Account Info**
2. Copy the following:
   - **Account SID**: Starts with `AC...`
   - **Auth Token**: Click to reveal and copy

3. For WhatsApp number:
   - Go to **Messaging** → **Try it out** → **Send a WhatsApp message**
   - Copy the **Sandbox Number** (format: `whatsapp:+14155238886`)

### Step 4: Configure Webhook URL (Do this after deployment)

1. In Twilio Console, go to **Messaging** → **Try it out** → **Send a WhatsApp message**
2. Scroll to **Sandbox Configuration**
3. Under "WHEN A MESSAGE COMES IN", enter your webhook URL:
   - Format: `https://yourdomain.com/api/whatsapp/webhook/`
   - For local testing with ngrok: `https://your-ngrok-url.ngrok.io/api/whatsapp/webhook/`
4. Set HTTP method to **POST**
5. Click **Save**

### Step 5: Production WhatsApp Number (Optional)

For production use, you need an approved WhatsApp Business number:

1. Go to **Messaging** → **Senders** → **WhatsApp senders**
2. Click **New WhatsApp Sender**
3. Follow the approval process (requires business verification)
4. This can take several days to weeks

**Note**: For development and testing, the sandbox is sufficient.

---

## AI Provider Setup

You can use OpenRouter (recommended for flexibility), OpenAI directly, or Anthropic.

### Option 1: OpenRouter (Recommended)

OpenRouter provides access to multiple AI models through a single API.

#### Step 1: Create OpenRouter Account

1. Go to [OpenRouter](https://openrouter.ai/)
2. Click **Sign In** and create an account
3. Verify your email

#### Step 2: Get API Key

1. Navigate to [Keys](https://openrouter.ai/keys)
2. Click **Create Key**
3. Give it a name (e.g., "WhatsApp Chatbot")
4. Copy the API key (starts with `sk-or-v1-...`)
5. **Important**: Save this key securely - you won't see it again

#### Step 3: Add Credits

1. Go to [Credits](https://openrouter.ai/credits)
2. Add credits to your account (minimum $5 recommended)
3. OpenRouter charges per-token based on the model used

#### Step 4: Choose a Model

Popular models available through OpenRouter:
- `openai/gpt-4`: Most capable, higher cost
- `openai/gpt-3.5-turbo`: Fast and cost-effective
- `anthropic/claude-3-opus`: Anthropic's most capable model
- `anthropic/claude-3-sonnet`: Balanced performance and cost
- `meta-llama/llama-3-70b-instruct`: Open source alternative

#### Configuration

In your `.env` file:
```bash
AI_PROVIDER=openrouter
AI_API_KEY=sk-or-v1-your-api-key-here
AI_MODEL=openai/gpt-4
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### Option 2: OpenAI Direct

#### Step 1: Create OpenAI Account

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Verify your email and phone number

#### Step 2: Get API Key

1. Navigate to [API Keys](https://platform.openai.com/api-keys)
2. Click **Create new secret key**
3. Give it a name
4. Copy the key (starts with `sk-...`)
5. **Important**: Save this key - you can't view it again

#### Step 3: Add Payment Method

1. Go to [Billing](https://platform.openai.com/account/billing)
2. Add a payment method
3. Set up usage limits if desired

#### Configuration

In your `.env` file:
```bash
AI_PROVIDER=openai
AI_API_KEY=sk-your-openai-key-here
AI_MODEL=gpt-4
```

### Option 3: Anthropic Direct

#### Step 1: Create Anthropic Account

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up for an account
3. Complete verification

#### Step 2: Get API Key

1. Navigate to [API Keys](https://console.anthropic.com/settings/keys)
2. Click **Create Key**
3. Copy the key (starts with `sk-ant-...`)

#### Step 3: Add Credits

1. Go to billing section
2. Add credits to your account

#### Configuration

In your `.env` file:
```bash
AI_PROVIDER=anthropic
AI_API_KEY=sk-ant-your-anthropic-key-here
AI_MODEL=claude-3-opus-20240229
```

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd whatsapp-ai-chatbot
```

### Step 2: Create Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Set Up Database

#### Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE whatsapp_ai_db;
CREATE USER whatsapp_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE whatsapp_ai_db TO whatsapp_user;
\q
```

#### Verify Redis is Running

```bash
redis-cli ping
# Should return: PONG
```

### Step 5: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

Fill in all required variables (see Environment Variables section in README.md).

### Step 6: Run Migrations

```bash
python manage.py migrate
```

### Step 7: Create Superuser

```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### Step 8: Validate Configuration

```bash
python manage.py validate_config
```

This will check all environment variables and connections.

### Step 9: Start Services

Open three terminal windows:

**Terminal 1 - Django Server**:
```bash
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 - Celery Worker**:
```bash
source venv/bin/activate
celery -A whatsapp_ai_chatbot worker --loglevel=info
```

**Terminal 3 - Celery Beat**:
```bash
source venv/bin/activate
celery -A whatsapp_ai_chatbot beat --loglevel=info
```

### Step 10: Test the Setup

```bash
# In a new terminal
source venv/bin/activate

# Test WhatsApp configuration
python manage.py test_whatsapp --check-config

# Test AI configuration
python manage.py manage_ai_config test
```

---

## Docker Deployment

Docker provides the easiest deployment method with all services pre-configured.

### Step 1: Install Docker

Follow the [Prerequisites Setup](#prerequisites-setup) section to install Docker.

### Step 2: Clone Repository

```bash
git clone <repository-url>
cd whatsapp-ai-chatbot
```

### Step 3: Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

**Important Docker-specific settings**:
```bash
# Use service names from docker-compose.yml
DB_HOST=db
REDIS_HOST=redis

# Other settings remain the same
DB_NAME=whatsapp_ai_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
```

### Step 4: Build and Start Services

```bash
# Build images and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

This will start:
- PostgreSQL database
- Redis cache
- Django web application
- Celery worker
- Celery beat scheduler

### Step 5: Run Migrations

```bash
# In a new terminal
docker-compose exec web python manage.py migrate
```

### Step 6: Create Superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

### Step 7: Verify Services

```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs web
docker-compose logs celery_worker

# Follow logs in real-time
docker-compose logs -f
```

### Step 8: Access Application

- **API**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Health Check**: http://localhost:8000/health/

### Docker Management Commands

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes data)
docker-compose down -v

# Restart a specific service
docker-compose restart web

# View logs for specific service
docker-compose logs -f web

# Execute commands in container
docker-compose exec web python manage.py <command>

# Scale Celery workers
docker-compose up -d --scale celery_worker=3
```

---

## Webhook Configuration

To receive WhatsApp messages, you need to expose your application to the internet.

### Option 1: Using ngrok (Local Development)

ngrok creates a secure tunnel to your local server.

#### Step 1: Install ngrok

**macOS**:
```bash
brew install ngrok
```

**Linux/Windows**:
Download from [ngrok.com](https://ngrok.com/download)

#### Step 2: Start ngrok

```bash
# Make sure your Django server is running on port 8000
ngrok http 8000
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

#### Step 3: Configure Twilio Webhook

1. Copy the HTTPS URL from ngrok (e.g., `https://abc123.ngrok.io`)
2. Go to Twilio Console → Messaging → WhatsApp Sandbox
3. Set webhook URL to: `https://abc123.ngrok.io/api/whatsapp/webhook/`
4. Save

**Note**: ngrok URLs change each time you restart. For persistent URLs, sign up for a free ngrok account.

### Option 2: Production Deployment

For production, deploy to a server with a public IP or domain.

#### Requirements

- Server with public IP address
- Domain name (optional but recommended)
- SSL certificate (required for HTTPS)

#### Popular Deployment Options

1. **AWS EC2/Lightsail**
2. **DigitalOcean Droplet**
3. **Google Cloud Compute Engine**
4. **Heroku**
5. **Railway**
6. **Render**

#### Basic Server Setup

```bash
# On your server
git clone <repository-url>
cd whatsapp-ai-chatbot

# Configure environment
cp .env.example .env
nano .env

# Start with Docker
docker-compose up -d --build

# Configure nginx as reverse proxy (recommended)
# Install certbot for SSL certificate
```

#### Configure Twilio Webhook

Set webhook URL to: `https://yourdomain.com/api/whatsapp/webhook/`

---

## Testing the Setup

### 1. Test Configuration

```bash
# Validate all settings
python manage.py validate_config

# Test WhatsApp configuration
python manage.py test_whatsapp --check-config

# Test AI configuration
python manage.py manage_ai_config test
```

### 2. Test WhatsApp Integration

```bash
# Send a test message
python manage.py test_whatsapp --phone "+1234567890" --message "Hello, this is a test!"
```

### 3. Test End-to-End Flow

1. **Join WhatsApp Sandbox** (if not already done):
   - Send the join code to Twilio's WhatsApp number
   - Wait for confirmation

2. **Send a Test Message**:
   - Open WhatsApp
   - Send any message to the Twilio sandbox number
   - You should receive an AI-generated response

3. **Test Conversation Context**:
   - Send multiple messages in sequence
   - The AI should remember previous messages in the conversation

4. **Check Logs**:
   ```bash
   # Local development
   tail -f logs/whatsapp_chatbot.log
   
   # Docker
   docker-compose logs -f web
   ```

### 4. Test Admin Interface

1. Navigate to http://localhost:8000/admin
2. Log in with superuser credentials
3. Check:
   - Conversations are being created
   - Messages are being stored
   - Webhook logs are being recorded

### 5. Test Error Handling

1. **Invalid AI Key**:
   - Temporarily set wrong AI_API_KEY
   - Send a message
   - Should receive user-friendly error message

2. **Rate Limiting**:
   - Send multiple messages rapidly
   - Should receive rate limit message after threshold

### Common Test Scenarios

```bash
# Test 1: Simple greeting
"Hello"
# Expected: AI greeting response

# Test 2: Question with context
"What's the weather like?"
"And tomorrow?"
# Expected: AI should understand "tomorrow" refers to weather

# Test 3: Long conversation
# Send 15+ messages
# Expected: Older messages should be dropped from context

# Test 4: Special characters
"Test with émojis 🎉 and spëcial çharacters"
# Expected: Proper handling and response
```

---

## Troubleshooting Setup Issues

### Database Connection Issues

**Error**: `could not connect to server`

**Solution**:
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list  # macOS

# Check connection
psql -U postgres -h localhost

# Verify credentials in .env match database
```

### Redis Connection Issues

**Error**: `Error connecting to Redis`

**Solution**:
```bash
# Check Redis is running
redis-cli ping

# Start Redis if not running
sudo systemctl start redis-server  # Linux
brew services start redis  # macOS
```

### Twilio Webhook Issues

**Error**: Messages not being received

**Solution**:
1. Check ngrok is running and URL is correct
2. Verify webhook URL in Twilio console
3. Check webhook signature validation
4. Review webhook logs in admin interface

### AI API Issues

**Error**: `Authentication failed` or `Invalid API key`

**Solution**:
1. Verify API key is correct in .env
2. Check API key has sufficient credits
3. Test with management command:
   ```bash
   python manage.py manage_ai_config test
   ```

### Celery Not Processing Tasks

**Error**: Messages received but no response

**Solution**:
```bash
# Check Celery worker is running
ps aux | grep celery

# Check Celery logs
celery -A whatsapp_ai_chatbot worker --loglevel=debug

# Verify Redis connection (Celery broker)
redis-cli ping
```

### Docker Issues

**Error**: `Cannot connect to Docker daemon`

**Solution**:
```bash
# Start Docker service
sudo systemctl start docker  # Linux

# Or start Docker Desktop on macOS/Windows
```

**Error**: Port already in use

**Solution**:
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in docker-compose.yml
```

---

## Next Steps

After successful setup:

1. **Customize AI Behavior**: Modify prompts and system messages in `message_processor.py`
2. **Add Features**: Extend functionality based on your requirements
3. **Monitor Usage**: Set up monitoring for API usage and costs
4. **Scale**: Add more Celery workers as needed
5. **Backup**: Set up regular database backups
6. **Security**: Review security settings before production deployment

## Additional Resources

- [Twilio WhatsApp API Documentation](https://www.twilio.com/docs/whatsapp)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Django Documentation](https://docs.djangoproject.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Docker Documentation](https://docs.docker.com/)

## Support

If you encounter issues not covered in this guide:
1. Check application logs in `logs/` directory
2. Review Django admin interface for webhook logs
3. Consult the troubleshooting section in README.md
4. Open an issue on GitHub with detailed error information
