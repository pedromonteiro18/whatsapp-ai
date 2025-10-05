# WhatsApp AI Chatbot - API Documentation

This document provides detailed information about the API endpoints, webhook payloads, admin interface, and troubleshooting guide.

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Webhook Integration](#webhook-integration)
3. [Admin Interface](#admin-interface)
4. [Management Commands](#management-commands)
5. [Troubleshooting Guide](#troubleshooting-guide)

---

## API Endpoints

### Health Check Endpoint

Check the health status of the application and its dependencies.

**Endpoint**: `GET /health/`

**Authentication**: None

**Response**:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "connected",
    "redis": "connected"
  }
}
```

**Status Codes**:
- `200 OK`: All services are healthy
- `503 Service Unavailable`: One or more services are down

**Example**:

```bash
curl http://localhost:8000/health/
```

---

### WhatsApp Webhook Endpoint

Receives incoming WhatsApp messages from Twilio.

**Endpoint**: `POST /api/whatsapp/webhook/`

**Authentication**: Twilio signature verification (automatic)

**Headers**:
```
Content-Type: application/x-www-form-urlencoded
X-Twilio-Signature: <signature>
```

**Request Body** (form-encoded):

```
MessageSid=SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AccountSid=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
From=whatsapp:+1234567890
To=whatsapp:+14155238886
Body=Hello, how are you?
NumMedia=0
```

**Response**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

**Status Codes**:
- `200 OK`: Message received and queued for processing
- `403 Forbidden`: Invalid webhook signature
- `400 Bad Request`: Malformed request

**Notes**:
- This endpoint is called by Twilio, not by your application
- Signature verification is automatic
- Messages are processed asynchronously via Celery
- Response is returned immediately to prevent timeout

---

### WhatsApp Webhook Verification

Verifies webhook configuration (Twilio requirement).

**Endpoint**: `GET /api/whatsapp/webhook/`

**Authentication**: None

**Query Parameters**:
- `hub.mode`: Verification mode (usually "subscribe")
- `hub.verify_token`: Verification token (if configured)
- `hub.challenge`: Challenge string to echo back

**Response**:

```
<challenge_string>
```

**Status Codes**:
- `200 OK`: Verification successful

---

## Webhook Integration

### Twilio Webhook Payload Format

When a user sends a WhatsApp message, Twilio sends a POST request with the following parameters:

#### Standard Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `MessageSid` | string | Unique message identifier | `SM1234567890abcdef...` |
| `AccountSid` | string | Twilio account identifier | `AC1234567890abcdef...` |
| `From` | string | Sender's WhatsApp number | `whatsapp:+1234567890` |
| `To` | string | Recipient's WhatsApp number | `whatsapp:+14155238886` |
| `Body` | string | Message text content | `Hello, how are you?` |
| `NumMedia` | integer | Number of media attachments | `0` |

#### Optional Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `MediaUrl0` | string | URL of first media attachment |
| `MediaContentType0` | string | MIME type of first media |
| `Latitude` | float | Location latitude (if shared) |
| `Longitude` | float | Location longitude (if shared) |
| `ProfileName` | string | Sender's WhatsApp profile name |

### Example Webhook Payload

```http
POST /api/whatsapp/webhook/ HTTP/1.1
Host: yourdomain.com
Content-Type: application/x-www-form-urlencoded
X-Twilio-Signature: abc123def456...

MessageSid=SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&
AccountSid=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx&
From=whatsapp%3A%2B1234567890&
To=whatsapp%3A%2B14155238886&
Body=What%27s+the+weather+like%3F&
NumMedia=0&
ProfileName=John+Doe
```

### Webhook Signature Verification

The application automatically verifies webhook signatures using Twilio's validation:

```python
from twilio.request_validator import RequestValidator

validator = RequestValidator(auth_token)
is_valid = validator.validate(
    url=request_url,
    params=request_params,
    signature=x_twilio_signature
)
```

**Security Notes**:
- Always verify signatures in production
- Never disable signature verification
- Keep your Twilio Auth Token secure

### Webhook Response Format

The application responds with TwiML (Twilio Markup Language):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
```

An empty response tells Twilio the message was received successfully. The actual AI response is sent asynchronously via the Twilio API.

---

## Admin Interface

The Django admin interface provides a web-based UI for managing the application.

### Accessing Admin Interface

**URL**: `http://localhost:8000/admin/`

**Login**: Use superuser credentials created during setup

### Available Models

#### 1. Conversations

**Path**: Admin → Chatbot Core → Conversations

**Fields**:
- **ID**: Unique conversation identifier (UUID)
- **User Phone**: WhatsApp number of the user
- **Started At**: When conversation began
- **Last Activity**: Last message timestamp
- **Is Active**: Whether conversation is currently active
- **Metadata**: Additional JSON data

**Actions**:
- View conversation details
- View all messages in conversation
- Mark conversation as inactive
- Delete conversation (cascades to messages)

**Filters**:
- Active/Inactive status
- Date range
- User phone number

**Search**: By user phone number

#### 2. Messages

**Path**: Admin → Chatbot Core → Messages

**Fields**:
- **ID**: Unique message identifier (UUID)
- **Conversation**: Link to parent conversation
- **Role**: `user` or `assistant`
- **Content**: Message text
- **Timestamp**: When message was sent/received
- **Metadata**: Additional JSON data

**Actions**:
- View message details
- Filter by conversation
- Filter by role
- Export messages

**Filters**:
- Role (user/assistant)
- Date range
- Conversation

**Search**: By content (full-text search)

#### 3. AI Configurations

**Path**: Admin → AI Integration → AI Configurations

**Fields**:
- **Provider**: AI provider name (openrouter, openai, anthropic)
- **API Key**: Encrypted API key (masked in display)
- **Model Name**: AI model identifier
- **Max Tokens**: Maximum response length
- **Temperature**: Response randomness (0.0-1.0)
- **Is Active**: Whether configuration is currently in use
- **Created At**: When configuration was created
- **Updated At**: Last modification time

**Actions**:
- Create new configuration
- Update existing configuration
- Activate/deactivate configuration
- Test configuration

**Security**:
- API keys are encrypted at rest
- Only masked values shown in admin
- Full keys never logged

#### 4. Webhook Logs

**Path**: Admin → Chatbot Core → Webhook Logs

**Fields**:
- **ID**: Unique log identifier (UUID)
- **Timestamp**: When webhook was received
- **Method**: HTTP method (GET/POST)
- **Headers**: Request headers (JSON)
- **Body**: Request body (JSON)
- **Response Status**: HTTP status code returned
- **Processing Time**: Time taken to process (ms)
- **Error**: Error message if any

**Actions**:
- View webhook details
- Filter by status code
- Filter by date range
- Export logs

**Filters**:
- HTTP method
- Response status
- Date range
- Has error

**Use Cases**:
- Debugging webhook issues
- Monitoring webhook performance
- Auditing incoming requests

### Admin Customization

The admin interface includes custom actions and displays:

#### Conversation Admin

```python
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user_phone', 'started_at', 'last_activity', 'is_active', 'message_count']
    list_filter = ['is_active', 'started_at']
    search_fields = ['user_phone']
    readonly_fields = ['id', 'started_at']
    
    def message_count(self, obj):
        return obj.message_set.count()
```

#### Message Admin

```python
class MessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'content_preview', 'timestamp']
    list_filter = ['role', 'timestamp']
    search_fields = ['content']
    readonly_fields = ['id', 'timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
```

---

## Management Commands

### test_whatsapp

Test WhatsApp integration and send test messages.

**Usage**:

```bash
# Check configuration only
python manage.py test_whatsapp --check-config

# Send test message
python manage.py test_whatsapp --phone "+1234567890" --message "Test message"
```

**Options**:
- `--check-config`: Only validate configuration, don't send message
- `--phone`: Recipient phone number (E.164 format)
- `--message`: Message text to send

**Output**:

```
✓ Twilio configuration is valid
✓ WhatsApp number is configured
✓ Test message sent successfully
Message SID: SM1234567890abcdef...
```

---

### manage_ai_config

Manage AI provider configurations.

**Usage**:

```bash
# List all configurations
python manage.py manage_ai_config list

# Create new configuration (interactive)
python manage.py manage_ai_config create

# Update configuration
python manage.py manage_ai_config update <config_id>

# Test AI connectivity
python manage.py manage_ai_config test
```

**Examples**:

```bash
# List configurations
$ python manage.py manage_ai_config list
ID  Provider    Model              Active  Created
1   openrouter  openai/gpt-4       Yes     2024-01-15
2   openai      gpt-3.5-turbo      No      2024-01-10

# Test configuration
$ python manage.py manage_ai_config test
Testing AI configuration...
✓ API key is valid
✓ Model is accessible
✓ Test message sent successfully
Response: "Hello! I'm working correctly."
```

---

### validate_config

Validate all environment variables and system configuration.

**Usage**:

```bash
python manage.py validate_config
```

**Output**:

```
Validating configuration...

✓ Django settings
  - SECRET_KEY: Set
  - DEBUG: False
  - ALLOWED_HOSTS: Configured

✓ Database
  - Connection: Successful
  - Migrations: Up to date

✓ Redis
  - Connection: Successful
  - Version: 7.0.5

✓ Twilio
  - Account SID: Valid
  - Auth Token: Valid
  - WhatsApp Number: Configured

✓ AI Provider
  - Provider: openrouter
  - API Key: Valid
  - Model: openai/gpt-4

All checks passed!
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Webhook Not Receiving Messages

**Symptoms**:
- Messages sent to WhatsApp number
- No response received
- No logs in admin interface

**Diagnosis**:

```bash
# Check webhook logs in admin
# Navigate to: Admin → Webhook Logs

# Check Celery worker logs
docker-compose logs celery_worker

# Test webhook locally
curl -X POST http://localhost:8000/api/whatsapp/webhook/ \
  -d "From=whatsapp:+1234567890" \
  -d "Body=Test message"
```

**Solutions**:

1. **Verify webhook URL in Twilio**:
   - Go to Twilio Console → WhatsApp Sandbox
   - Check webhook URL is correct
   - Ensure URL is accessible from internet

2. **Check ngrok (local development)**:
   ```bash
   # Restart ngrok
   ngrok http 8000
   
   # Update webhook URL in Twilio with new ngrok URL
   ```

3. **Verify signature validation**:
   - Check `TWILIO_AUTH_TOKEN` is correct
   - Review webhook logs for 403 errors

4. **Check application is running**:
   ```bash
   # Docker
   docker-compose ps
   
   # Local
   ps aux | grep "manage.py runserver"
   ```

---

#### 2. AI API Errors

**Symptoms**:
- Messages received but no AI response
- Error messages sent to user
- Errors in logs

**Diagnosis**:

```bash
# Check AI configuration
python manage.py manage_ai_config test

# Check Celery worker logs
docker-compose logs celery_worker | grep -i error

# Check application logs
tail -f logs/errors.log
```

**Solutions**:

1. **Invalid API Key**:
   ```bash
   # Verify API key in .env
   cat .env | grep AI_API_KEY
   
   # Test with management command
   python manage.py manage_ai_config test
   ```

2. **Insufficient Credits**:
   - Check your AI provider account balance
   - Add credits if needed
   - OpenRouter: https://openrouter.ai/credits
   - OpenAI: https://platform.openai.com/account/billing

3. **Rate Limiting**:
   - Check if you've exceeded API rate limits
   - Wait and retry
   - Consider upgrading your API plan

4. **Model Not Available**:
   ```bash
   # Verify model name is correct
   # OpenRouter: https://openrouter.ai/models
   # OpenAI: https://platform.openai.com/docs/models
   
   # Update in .env
   AI_MODEL=openai/gpt-3.5-turbo
   ```

---

#### 3. Database Connection Errors

**Symptoms**:
- Application won't start
- 500 errors on all requests
- "could not connect to server" errors

**Diagnosis**:

```bash
# Test database connection
psql -U postgres -h localhost -d whatsapp_ai_db

# Check database service (Docker)
docker-compose ps db

# Check database logs
docker-compose logs db
```

**Solutions**:

1. **Database not running**:
   ```bash
   # Start PostgreSQL (local)
   sudo systemctl start postgresql
   
   # Start database (Docker)
   docker-compose up -d db
   ```

2. **Wrong credentials**:
   ```bash
   # Verify credentials in .env
   cat .env | grep DB_
   
   # Test connection
   psql -U $DB_USER -h $DB_HOST -d $DB_NAME
   ```

3. **Database doesn't exist**:
   ```bash
   # Create database
   psql -U postgres
   CREATE DATABASE whatsapp_ai_db;
   ```

4. **Migrations not applied**:
   ```bash
   # Run migrations
   python manage.py migrate
   
   # Or with Docker
   docker-compose exec web python manage.py migrate
   ```

---

#### 4. Redis Connection Errors

**Symptoms**:
- Celery tasks not processing
- "Error connecting to Redis" messages
- Conversation context not maintained

**Diagnosis**:

```bash
# Test Redis connection
redis-cli ping

# Check Redis service (Docker)
docker-compose ps redis

# Check Redis logs
docker-compose logs redis
```

**Solutions**:

1. **Redis not running**:
   ```bash
   # Start Redis (local)
   sudo systemctl start redis-server
   
   # Start Redis (Docker)
   docker-compose up -d redis
   ```

2. **Wrong Redis configuration**:
   ```bash
   # Verify Redis settings in .env
   cat .env | grep REDIS_
   
   # Test connection
   redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
   ```

3. **Redis out of memory**:
   ```bash
   # Check Redis memory usage
   redis-cli info memory
   
   # Clear Redis cache if needed
   redis-cli FLUSHDB
   ```

---

#### 5. Celery Tasks Not Processing

**Symptoms**:
- Messages received but not processed
- No AI responses
- Tasks stuck in queue

**Diagnosis**:

```bash
# Check Celery worker status
celery -A whatsapp_ai_chatbot inspect active

# Check Celery worker logs
docker-compose logs celery_worker

# Check Redis queue
redis-cli LLEN celery
```

**Solutions**:

1. **Celery worker not running**:
   ```bash
   # Start worker (local)
   celery -A whatsapp_ai_chatbot worker --loglevel=info
   
   # Start worker (Docker)
   docker-compose up -d celery_worker
   ```

2. **Worker crashed**:
   ```bash
   # Restart worker
   docker-compose restart celery_worker
   
   # Check logs for errors
   docker-compose logs celery_worker
   ```

3. **Tasks failing**:
   ```bash
   # Check task errors in logs
   docker-compose logs celery_worker | grep -i error
   
   # Purge failed tasks
   celery -A whatsapp_ai_chatbot purge
   ```

---

#### 6. Rate Limiting Issues

**Symptoms**:
- Users receiving "too many messages" errors
- Legitimate users being blocked

**Diagnosis**:

```bash
# Check rate limit settings in .env
cat .env | grep RATE_LIMIT

# Check Redis for rate limit keys
redis-cli KEYS "rate_limit:*"
```

**Solutions**:

1. **Adjust rate limits**:
   ```bash
   # Edit .env
   RATE_LIMIT_MESSAGES=20  # Increase from 10
   RATE_LIMIT_WINDOW=60    # Keep at 60 seconds
   
   # Restart application
   docker-compose restart web
   ```

2. **Clear rate limit for specific user**:
   ```bash
   # Connect to Redis
   redis-cli
   
   # Delete rate limit key
   DEL rate_limit:whatsapp:+1234567890
   ```

---

#### 7. Conversation Context Not Maintained

**Symptoms**:
- AI doesn't remember previous messages
- Each message treated as new conversation

**Diagnosis**:

```bash
# Check Redis connection
redis-cli ping

# Check conversation keys in Redis
redis-cli KEYS "conversation:*"

# Check conversation TTL
redis-cli TTL "conversation:whatsapp:+1234567890"
```

**Solutions**:

1. **Redis not connected**:
   - See [Redis Connection Errors](#4-redis-connection-errors)

2. **Conversation expired**:
   ```bash
   # Check TTL setting
   cat .env | grep CONVERSATION_TTL
   
   # Increase TTL (in seconds)
   CONVERSATION_TTL=7200  # 2 hours instead of 1
   ```

3. **Context window too small**:
   ```bash
   # Check context setting
   cat .env | grep MAX_CONTEXT_MESSAGES
   
   # Increase context window
   MAX_CONTEXT_MESSAGES=20  # Instead of 10
   ```

---

### Debugging Tips

#### Enable Debug Logging

```bash
# Edit .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart application
docker-compose restart web celery_worker
```

**Warning**: Never use `DEBUG=True` in production!

#### Check Application Logs

```bash
# Local development
tail -f logs/whatsapp_chatbot.log
tail -f logs/errors.log

# Docker
docker-compose logs -f web
docker-compose logs -f celery_worker
```

#### Monitor Redis

```bash
# Monitor Redis commands in real-time
redis-cli MONITOR

# Check Redis info
redis-cli INFO

# List all keys
redis-cli KEYS "*"
```

#### Monitor Database

```bash
# Connect to database
psql -U postgres -d whatsapp_ai_db

# Check recent conversations
SELECT * FROM chatbot_core_conversation ORDER BY last_activity DESC LIMIT 10;

# Check recent messages
SELECT * FROM chatbot_core_message ORDER BY timestamp DESC LIMIT 20;

# Check webhook logs
SELECT * FROM chatbot_core_webhooklog ORDER BY timestamp DESC LIMIT 10;
```

#### Test Individual Components

```bash
# Test WhatsApp
python manage.py test_whatsapp --check-config

# Test AI
python manage.py manage_ai_config test

# Test configuration
python manage.py validate_config

# Test database
python manage.py dbshell

# Test Redis
redis-cli ping
```

---

### Getting Help

If you're still experiencing issues:

1. **Check Logs**: Review all relevant logs for error messages
2. **Search Issues**: Check GitHub issues for similar problems
3. **Create Issue**: Open a new issue with:
   - Detailed description of the problem
   - Steps to reproduce
   - Relevant log excerpts
   - Environment details (OS, Python version, etc.)
   - Configuration (without sensitive data)

---

## API Rate Limits

### Application Rate Limits

The application implements per-user rate limiting:

- **Default**: 10 messages per 60 seconds per user
- **Configurable**: Via `RATE_LIMIT_MESSAGES` and `RATE_LIMIT_WINDOW`
- **Storage**: Redis-based with automatic expiration

### External API Rate Limits

Be aware of rate limits from external services:

#### Twilio
- **Sandbox**: 1 message per second
- **Production**: Varies by account type
- **Documentation**: https://www.twilio.com/docs/usage/api-rate-limits

#### OpenRouter
- **Free tier**: Varies by model
- **Paid tier**: Higher limits
- **Documentation**: https://openrouter.ai/docs#rate-limits

#### OpenAI
- **Free tier**: 3 requests per minute
- **Paid tier**: 3,500 requests per minute (varies by model)
- **Documentation**: https://platform.openai.com/docs/guides/rate-limits

---

## Security Considerations

### Webhook Security

1. **Always verify signatures**: Never disable signature verification
2. **Use HTTPS**: Required for production webhooks
3. **Validate input**: All user input is sanitized
4. **Rate limiting**: Prevents abuse

### API Key Security

1. **Encryption**: API keys encrypted at rest
2. **Environment variables**: Never commit to version control
3. **Rotation**: Regularly rotate API keys
4. **Least privilege**: Use API keys with minimal required permissions

### Data Privacy

1. **Logging**: Sensitive data not logged
2. **Retention**: Configure conversation TTL appropriately
3. **Compliance**: Review for GDPR/CCPA requirements
4. **Encryption**: Use SSL/TLS for all communications

---

## Performance Optimization

### Scaling Recommendations

1. **Horizontal scaling**: Add more web workers
   ```bash
   docker-compose up -d --scale web=3
   ```

2. **Celery workers**: Scale based on message volume
   ```bash
   docker-compose up -d --scale celery_worker=5
   ```

3. **Redis**: Use Redis Cluster for high availability

4. **Database**: Use connection pooling and read replicas

### Monitoring

Recommended monitoring tools:
- **Application**: Sentry, New Relic, DataDog
- **Infrastructure**: Prometheus, Grafana
- **Logs**: ELK Stack, Splunk
- **Uptime**: UptimeRobot, Pingdom

---

## Appendix

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid request format |
| 403 | Forbidden | Invalid webhook signature |
| 404 | Not Found | Endpoint doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Application error |
| 503 | Service Unavailable | Service down |

### Error Response Format

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "limit": 10,
      "window": 60,
      "retry_after": 45
    }
  }
}
```

### Webhook Retry Policy

Twilio retries failed webhooks:
- **Attempts**: Up to 3 retries
- **Backoff**: Exponential (1s, 2s, 4s)
- **Timeout**: 15 seconds per attempt

Ensure your webhook responds within 15 seconds to avoid retries.
