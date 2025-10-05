# Implementation Plan

- [x] 1. Set up Django project structure and dependencies
  - Create Django project with required apps (core, whatsapp, ai_integration)
  - Configure settings.py with environment variable support
  - Set up requirements.txt with all dependencies (Django, DRF, Celery, Redis, Twilio, OpenAI, etc.)
  - Create .env.example file with all required configuration variables
  - Set up Docker and docker-compose.yml for PostgreSQL, Redis, and application containers
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 2. Implement configuration management system
  - Create Config class to load and validate environment variables
  - Implement validation for required settings (Twilio credentials, AI API key, etc.)
  - Add support for encrypted storage of sensitive configuration
  - Create management command to test configuration validity
  - _Requirements: 2.1, 2.2, 2.4, 7.1, 7.2, 7.4_

- [x] 3. Create database models
  - [x] 3.1 Implement Conversation model with user phone tracking
    - Create model with UUID primary key, user_phone field, timestamps
    - Add indexes for user_phone and is_active fields
    - _Requirements: 4.1, 4.4_
  
  - [x] 3.2 Implement Message model with conversation relationship
    - Create model with role (user/assistant), content, timestamp
    - Add foreign key to Conversation with cascade delete
    - Add metadata JSONField for extensibility
    - _Requirements: 4.1, 4.2_
  
  - [x] 3.3 Implement AIConfiguration model with encryption
    - Create model for storing AI provider settings
    - Implement field encryption for api_key using django-encrypted-model-fields
    - Add fields for provider, model_name, max_tokens, temperature
    - _Requirements: 2.1, 5.1_
  
  - [x] 3.4 Implement WebhookLog model for audit trail
    - Create model to log all webhook requests and responses
    - Add fields for headers, body, response_status, processing_time
    - _Requirements: 6.1, 6.2_
  
  - [x] 3.5 Create and run database migrations
    - Generate migrations for all models
    - Apply migrations to create database schema
    - _Requirements: 4.1, 4.2_

- [x] 4. Build AI service adapter layer
  - [x] 4.1 Create base AI adapter abstract class
    - Define abstract methods: send_message(), validate_credentials()
    - Add common error handling and retry logic
    - _Requirements: 2.2, 2.3, 3.2, 3.3_
  
  - [x] 4.2 Implement OpenRouter adapter (supports OpenAI and Anthropic)
    - Implement send_message() using OpenAI Python SDK with OpenRouter base URL
    - Handle authentication with API key from configuration
    - Format conversation history for chat completion format
    - Implement error handling for rate limits and API errors
    - _Requirements: 2.2, 3.2, 3.3, 3.5_
  
  - [x] 4.3 Create AI adapter factory
    - Implement factory pattern to instantiate correct adapter based on configuration
    - Add validation to ensure selected provider is supported
    - Support loading from environment variables or database
    - _Requirements: 2.2, 2.4_

- [x] 5. Implement conversation management with Redis
  - [x] 5.1 Create ConversationManager class
    - Implement get_history() to retrieve recent messages from Redis
    - Implement add_message() to store messages with automatic expiration
    - Implement clear_history() for conversation reset
    - Use Redis sorted sets for efficient time-based retrieval
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [x] 5.2 Implement conversation context window management
    - Limit conversation history to MAX_CONTEXT_MESSAGES from config
    - Implement sliding window to keep most recent messages
    - _Requirements: 4.2_
  
  - [x] 5.3 Add conversation expiration handling
    - Set TTL on Redis keys based on CONVERSATION_TTL config
    - Implement automatic cleanup of expired conversations
    - _Requirements: 4.3_

- [x] 6. Build WhatsApp integration layer
  - [x] 6.1 Create WhatsAppClient for sending messages
    - Create whatsapp/client.py with WhatsAppClient class
    - Implement send_message() using Twilio Python SDK
    - Configure Twilio credentials from Config class
    - Add retry logic for failed message sends
    - Implement error handling for Twilio API errors
    - _Requirements: 1.2, 1.3_
  
  - [x] 6.2 Implement webhook signature verification
    - Create whatsapp/utils.py with verify_webhook_signature() function
    - Use Twilio's request validator with auth token
    - _Requirements: 5.3, 1.1_
  
  - [x] 6.3 Create WhatsApp webhook view
    - Implement WhatsAppWebhookView in whatsapp/views.py
    - Add POST endpoint to receive incoming messages
    - Add GET endpoint for webhook verification
    - Parse Twilio webhook payload to extract sender and message
    - Validate webhook signature before processing
    - Queue message processing as Celery task
    - Return 200 OK immediately to prevent timeout
    - _Requirements: 1.1, 1.3, 6.3_
  
  - [x] 6.4 Add webhook URL configuration
    - Add webhook endpoint to whatsapp_ai_chatbot/urls.py
    - Configure URL routing for WhatsApp webhook
    - _Requirements: 1.1_

- [x] 7. Implement message processing logic
  - [x] 7.1 Create MessageProcessor class
    - Create chatbot_core/message_processor.py with MessageProcessor class
    - Implement process_message() method as main entry point
    - Retrieve or create conversation for user in database
    - Get conversation history from ConversationManager
    - _Requirements: 3.1, 4.1, 4.2_

  - [x] 7.2 Implement AI interaction flow
    - Format conversation history for AI adapter
    - Call AI adapter's send_message() with context
    - Handle AI API responses and errors
    - Save user message and AI response to database (Message model)
    - Save messages to Redis via ConversationManager
    - _Requirements: 3.2, 3.5, 4.2_

  - [x] 7.3 Add error handling and user notifications
    - Catch AI API errors and send user-friendly messages via WhatsAppClient
    - Handle timeout scenarios with appropriate user feedback
    - Implement fallback responses for system errors
    - _Requirements: 3.3, 3.5, 6.3_

- [x] 8. Create Celery tasks for async processing
  - [x] 8.1 Create message processing task
    - Create chatbot_core/tasks.py with process_whatsapp_message task
    - Wrap MessageProcessor.process_message() in Celery task
    - Configure task retry policy for transient failures
    - Add task timeout to prevent hanging tasks
    - Log task execution and errors
    - _Requirements: 3.1, 3.3_

  - [x] 8.2 Create conversation cleanup task
    - Add cleanup_expired_conversations periodic task
    - Query and delete inactive conversations older than TTL
    - Schedule task with Celery beat (every 6 hours)
    - _Requirements: 4.3_

- [x] 9. Implement error handling utilities
  - [x] 9.1 Create ErrorHandler utility class
    - Create chatbot_core/error_handler.py with ErrorHandler class
    - Implement methods for different error categories (webhook, AI, system)
    - Generate user-friendly error messages
    - Log errors with appropriate severity levels
    - _Requirements: 6.1, 6.3_

  - [x] 9.2 Implement admin notification for critical errors
    - Add send_admin_alert() method to ErrorHandler
    - Implemented with comprehensive logging and Redis-based rate limiting
    - Rate limits same error type to once per hour to prevent alert fatigue
    - _Requirements: 6.2_

- [x] 10. Create management commands and utilities
  - [x] 10.1 Create command to test WhatsApp integration
    - Create chatbot_core/management/commands/test_whatsapp.py
    - Send test message to configured WhatsApp number
    - Check Twilio configuration
    - Supports --check-config flag for config-only validation
    - _Requirements: 1.2_

  - [x] 10.2 Create command to manage AI configuration
    - Create chatbot_core/management/commands/manage_ai_config.py
    - CRUD operations: list, create, update configurations
    - Test AI API connectivity with validation
    - Supports both environment and database configurations
    - _Requirements: 2.1, 2.4_

- [ ] 11. Implement security features
  - [ ] 11.1 Add rate limiting
    - Create chatbot_core/rate_limiter.py with RateLimiter class
    - Implement per-user rate limiting using Redis
    - Configure rate limits from Config class
    - Return appropriate error messages when rate limited
    - Integrate with webhook view
    - _Requirements: 5.3, 3.3_
  
  - [ ] 11.2 Add input sanitization
    - Create chatbot_core/sanitizer.py with input sanitization functions
    - Sanitize user messages before processing
    - Validate phone number formats
    - Escape special characters in responses
    - _Requirements: 5.3_
  
  - [ ] 11.3 Configure HTTPS and security headers
    - Update settings.py with security middleware configuration
    - Configure SECURE_SSL_REDIRECT and other security settings
    - Update CORS configuration for production
    - _Requirements: 5.3_

- [ ] 12. Create Docker deployment setup
  - [ ] 12.1 Create Dockerfile for Django application
    - Create Dockerfile with multi-stage build
    - Install Python dependencies
    - Configure gunicorn for production
    - Set up proper user permissions
    - _Requirements: 7.1_
  
  - [ ] 12.2 Create startup scripts
    - Create docker-entrypoint.sh to run migrations
    - Add health check endpoint in Django
    - Configure graceful shutdown
    - _Requirements: 7.1_

- [ ]* 13. Write comprehensive tests
  - [ ]* 13.1 Write unit tests for AI adapters
    - Create ai_integration/tests/test_adapters.py
    - Mock AI API responses
    - Test error handling and retries
    - Test message formatting
    - _Requirements: 3.2, 3.5_
  
  - [ ]* 13.2 Write unit tests for ConversationManager
    - Create chatbot_core/tests/test_conversation_manager.py
    - Mock Redis operations using fakeredis
    - Test conversation history retrieval and storage
    - Test expiration handling
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 13.3 Write unit tests for MessageProcessor
    - Create chatbot_core/tests/test_message_processor.py
    - Mock dependencies (AI adapter, ConversationManager, WhatsAppClient)
    - Test message processing flow
    - Test error scenarios
    - _Requirements: 3.1, 3.2, 3.5_
  
  - [ ]* 13.4 Write integration tests for webhook endpoint
    - Create whatsapp/tests/test_webhook.py
    - Test with sample Twilio payloads
    - Test signature verification
    - Test end-to-end message flow
    - _Requirements: 1.1, 1.2, 5.3_
  
  - [ ]* 13.5 Write integration tests for database operations
    - Create chatbot_core/tests/test_models.py
    - Test model creation and retrieval
    - Test conversation and message relationships
    - _Requirements: 4.1, 4.2, 5.1_

- [ ] 14. Create documentation and setup guide
  - [ ] 14.1 Update README.md
    - Add project overview and features
    - Include prerequisites and dependencies
    - Document environment variables
    - Add quick start guide
    - _Requirements: 7.1, 7.2_
  
  - [ ] 14.2 Create setup instructions
    - Document Twilio account setup and webhook configuration
    - Document OpenRouter/AI API key setup
    - Provide step-by-step local development setup
    - Add Docker deployment instructions
    - _Requirements: 2.1, 7.1_
  
  - [ ] 14.3 Create API documentation
    - Document webhook endpoints and payload format
    - Document admin interface usage
    - Add troubleshooting guide
    - _Requirements: 6.4_

- [ ] 15. Final integration and testing
  - [ ] 15.1 Test complete user flow
    - Send test message from WhatsApp
    - Verify AI response is received
    - Test multi-turn conversation with context
    - Verify conversation history persistence
    - _Requirements: 1.1, 1.2, 3.1, 3.2, 4.1, 4.2_
  
  - [ ] 15.2 Test error scenarios
    - Test with invalid AI API key
    - Test with Twilio service interruption
    - Test database connection failures
    - Test Redis connection failures
    - Verify user receives appropriate error messages
    - _Requirements: 1.3, 1.4, 3.3, 3.5, 6.3_
  
  - [ ] 15.3 Verify configuration management
    - Test with different AI providers (OpenAI, Anthropic via OpenRouter)
    - Test configuration updates via admin
    - Test environment variable loading
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.1_
