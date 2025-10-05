# Design Document: WhatsApp AI Chatbot

## Overview

This Django application provides a bridge between WhatsApp messaging and AI APIs, enabling users to interact with AI assistants through WhatsApp. The system uses webhooks to receive WhatsApp messages, processes them through a configurable AI service, and returns responses to users.

The application follows a modular architecture with clear separation between WhatsApp communication, AI integration, conversation management, and business logic layers.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    User[WhatsApp User] -->|Sends Message| WA[WhatsApp Business API]
    WA -->|Webhook| Django[Django Application]
    Django -->|Query| AI[AI API Service]
    AI -->|Response| Django
    Django -->|Send Message| WA
    WA -->|Delivers| User
    Django -->|Store/Retrieve| DB[(PostgreSQL Database)]
    Django -->|Cache| Redis[(Redis Cache)]
```

### Technology Stack

- **Framework**: Django 4.2+ with Django REST Framework
- **WhatsApp Integration**: Twilio API for WhatsApp or Meta WhatsApp Business API
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for session management and rate limiting
- **Task Queue**: Celery for asynchronous message processing
- **AI Integration**: Configurable adapter pattern supporting OpenAI, Anthropic, or custom APIs
- **Deployment**: Docker containers with docker-compose for local development

### Design Decisions

1. **WhatsApp Provider Choice**: Using Twilio API for WhatsApp provides easier setup and better documentation compared to direct Meta API integration. Twilio handles webhook verification and message formatting.

2. **Asynchronous Processing**: Celery tasks handle AI API calls to prevent webhook timeouts and improve responsiveness.

3. **Adapter Pattern for AI**: Allows switching between different AI providers (OpenAI, Anthropic, etc.) without changing core logic.

4. **Redis for Conversation State**: Fast access to conversation history and session management with automatic expiration.

## Components and Interfaces

### 1. WhatsApp Webhook Handler

**Purpose**: Receives and validates incoming WhatsApp messages from Twilio.

**Endpoints**:
- `POST /api/whatsapp/webhook/` - Receives incoming messages
- `GET /api/whatsapp/webhook/` - Webhook verification (Twilio requirement)

**Responsibilities**:
- Validate webhook signatures
- Parse incoming message payload
- Extract sender information and message content
- Queue message for processing
- Return 200 OK immediately to prevent timeout

**Interface**:
```python
class WhatsAppWebhookView(APIView):
    def post(self, request):
        """Handle incoming WhatsApp messages"""
        pass
    
    def get(self, request):
        """Handle webhook verification"""
        pass
```

### 2. Message Processor

**Purpose**: Core business logic for processing messages and coordinating AI interactions.

**Responsibilities**:
- Retrieve conversation context
- Format messages for AI API
- Handle conversation flow
- Manage error scenarios
- Update conversation state

**Interface**:
```python
class MessageProcessor:
    def process_message(self, sender: str, message: str) -> str:
        """Process incoming message and return response"""
        pass
    
    def get_conversation_context(self, sender: str) -> List[Dict]:
        """Retrieve conversation history"""
        pass
    
    def save_message(self, sender: str, role: str, content: str):
        """Save message to conversation history"""
        pass
```

### 3. AI Service Adapter

**Purpose**: Abstract interface for different AI providers with concrete implementations.

**Responsibilities**:
- Send requests to AI APIs
- Handle API-specific authentication
- Format requests and responses
- Manage rate limiting and retries
- Handle streaming responses if supported

**Interface**:
```python
class BaseAIAdapter(ABC):
    @abstractmethod
    def send_message(self, messages: List[Dict], **kwargs) -> str:
        """Send messages to AI and return response"""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate API credentials"""
        pass

class OpenAIAdapter(BaseAIAdapter):
    """OpenAI-specific implementation"""
    pass

class AnthropicAdapter(BaseAIAdapter):
    """Anthropic-specific implementation"""
    pass
```

### 4. WhatsApp Client

**Purpose**: Send messages back to WhatsApp users via Twilio API.

**Responsibilities**:
- Format outgoing messages
- Handle Twilio API authentication
- Send messages with retry logic
- Handle media attachments (future enhancement)

**Interface**:
```python
class WhatsAppClient:
    def send_message(self, to: str, message: str) -> bool:
        """Send message to WhatsApp user"""
        pass
    
    def send_typing_indicator(self, to: str):
        """Send typing indicator (if supported)"""
        pass
```

### 5. Conversation Manager

**Purpose**: Manage conversation state and history using Redis.

**Responsibilities**:
- Store and retrieve conversation history
- Implement conversation expiration
- Manage conversation context window
- Handle conversation reset

**Interface**:
```python
class ConversationManager:
    def get_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        pass
    
    def add_message(self, user_id: str, role: str, content: str):
        """Add message to conversation"""
        pass
    
    def clear_history(self, user_id: str):
        """Clear conversation history"""
        pass
    
    def set_expiration(self, user_id: str, ttl: int):
        """Set conversation expiration time"""
        pass
```

### 6. Configuration Manager

**Purpose**: Centralized configuration management with validation.

**Responsibilities**:
- Load configuration from environment variables
- Validate required settings
- Provide type-safe access to configuration
- Support hot-reloading of non-critical settings

**Interface**:
```python
class Config:
    # WhatsApp settings
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_WHATSAPP_NUMBER: str
    
    # AI settings
    AI_PROVIDER: str  # 'openai', 'anthropic', etc.
    AI_API_KEY: str
    AI_MODEL: str
    AI_MAX_TOKENS: int
    
    # Application settings
    CONVERSATION_TTL: int  # seconds
    MAX_CONTEXT_MESSAGES: int
    
    @classmethod
    def validate(cls):
        """Validate all required settings are present"""
        pass
```

## Data Models

### Message Model

Stores all messages for audit and conversation history.

```python
class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE)
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]
```

### Conversation Model

Tracks conversation sessions with users.

```python
class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_phone = models.CharField(max_length=20, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user_phone', 'is_active']),
        ]
```

### AIConfiguration Model

Stores AI provider configuration (encrypted).

```python
class AIConfiguration(models.Model):
    id = models.AutoField(primary_key=True)
    provider = models.CharField(max_length=50)  # 'openai', 'anthropic', etc.
    api_key = models.CharField(max_length=500)  # Encrypted field
    model_name = models.CharField(max_length=100)
    max_tokens = models.IntegerField(default=1000)
    temperature = models.FloatField(default=0.7)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
```

### WebhookLog Model

Logs all webhook requests for debugging and audit.

```python
class WebhookLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    headers = models.JSONField()
    body = models.JSONField()
    response_status = models.IntegerField()
    processing_time = models.FloatField()  # milliseconds
    error = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
        ]
```

## Error Handling

### Error Categories

1. **WhatsApp Errors**: Invalid webhook signature, malformed payload
2. **AI API Errors**: Authentication failure, rate limiting, timeout
3. **System Errors**: Database connection, Redis unavailable
4. **Business Logic Errors**: Invalid conversation state, configuration missing

### Error Handling Strategy

```python
class ErrorHandler:
    def handle_webhook_error(self, error: Exception) -> Response:
        """Return appropriate HTTP response for webhook errors"""
        pass
    
    def handle_ai_error(self, error: Exception, user_phone: str):
        """Send user-friendly message for AI errors"""
        pass
    
    def handle_system_error(self, error: Exception):
        """Log and alert for system errors"""
        pass
```

### User-Facing Error Messages

- **AI Unavailable**: "I'm having trouble connecting right now. Please try again in a moment."
- **Rate Limited**: "I'm receiving a lot of messages. Please wait a moment before sending another."
- **Invalid Configuration**: "The service is temporarily unavailable. Please contact support."
- **Timeout**: "This is taking longer than expected. Let me try again..."

## Testing Strategy

### Unit Tests

- Test each component in isolation with mocked dependencies
- Test AI adapter implementations with mocked API responses
- Test conversation manager with mocked Redis
- Test message processor logic
- Test configuration validation

### Integration Tests

- Test webhook endpoint with sample Twilio payloads
- Test end-to-end message flow with test AI provider
- Test database operations and transactions
- Test Redis caching and expiration
- Test Celery task execution

### End-to-End Tests

- Test complete user journey from WhatsApp message to AI response
- Test conversation context maintenance across multiple messages
- Test error scenarios and recovery
- Test configuration changes and hot-reloading

### Test Data

- Sample WhatsApp webhook payloads from Twilio documentation
- Mock AI API responses for different scenarios
- Test conversation histories with various lengths
- Invalid configuration scenarios

### Testing Tools

- pytest for test framework
- pytest-django for Django integration
- fakeredis for Redis mocking
- responses library for HTTP mocking
- factory_boy for test data generation

## Security Considerations

1. **Webhook Signature Verification**: Validate all incoming webhooks using Twilio signature
2. **API Key Encryption**: Use Django's encryption utilities or django-encrypted-model-fields
3. **Environment Variables**: Never commit secrets to version control
4. **Rate Limiting**: Implement per-user rate limiting to prevent abuse
5. **Input Sanitization**: Sanitize all user inputs before processing
6. **HTTPS Only**: Enforce HTTPS for all external communications
7. **Logging**: Avoid logging sensitive data (API keys, phone numbers in plain text)

## Deployment Considerations

### Environment Variables

```bash
# Django
SECRET_KEY=<django-secret>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/whatsapp_ai

# Redis
REDIS_URL=redis://localhost:6379/0

# Twilio
TWILIO_ACCOUNT_SID=<account-sid>
TWILIO_AUTH_TOKEN=<auth-token>
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# AI Configuration
AI_PROVIDER=openai
AI_API_KEY=<api-key>
AI_MODEL=gpt-4
AI_MAX_TOKENS=1000

# Application
CONVERSATION_TTL=3600
MAX_CONTEXT_MESSAGES=10
```

### Docker Setup

- Multi-stage Dockerfile for optimized image size
- docker-compose.yml for local development with PostgreSQL and Redis
- Separate containers for web, celery worker, and celery beat
- Volume mounts for development hot-reloading

### Scalability

- Horizontal scaling of web workers behind load balancer
- Celery workers can be scaled independently
- Redis cluster for high availability
- Database connection pooling
- CDN for static assets
