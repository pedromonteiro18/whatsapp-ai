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

- [x] 11. Implement security features
  - [x] 11.1 Add rate limiting
    - Create chatbot_core/rate_limiter.py with RateLimiter class
    - Implement per-user rate limiting using Redis
    - Configure rate limits from Config class
    - Return appropriate error messages when rate limited
    - _Requirements: 5.3, 3.3_

  - [x] 11.2 Add input sanitization
    - Create chatbot_core/sanitizer.py with input sanitization functions
    - Sanitize user messages before processing
    - Validate phone number formats (E.164 standard)
    - Escape special characters in responses
    - Implemented XSS prevention and dangerous pattern removal
    - _Requirements: 5.3_

  - [x] 11.3 Configure HTTPS and security headers
    - Update settings.py with security middleware configuration
    - Configure SECURE_SSL_REDIRECT and other security settings
    - Update CORS configuration for production
    - Added HSTS, secure cookies, XSS protection, and rate limiting settings
    - _Requirements: 5.3_

- [x] 12. Create Docker deployment setup
  - [x] 12.1 Create Dockerfile for Django application
    - Create Dockerfile with multi-stage build (builder + runtime stages)
    - Install Python dependencies with pip wheel optimization
    - Configure gunicorn for production with auto-scaling workers
    - Set up proper user permissions (non-root django user)
    - Added security: runs as non-root, minimal image size
    - _Requirements: 7.1_

  - [x] 12.2 Create startup scripts
    - Create docker-entrypoint.sh to run migrations
    - Added database readiness check with retries
    - Add health check endpoint in Django (checks DB + Redis)
    - Configure graceful shutdown with SIGTERM handling
    - Automated superuser creation and configuration validation
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

- [x] 14. Create documentation and setup guide
  - [x] 14.1 Update README.md
    - Add project overview and features
    - Include prerequisites and dependencies
    - Document environment variables
    - Add quick start guide
    - _Requirements: 7.1, 7.2_
  
  - [x] 14.2 Create setup instructions
    - Document Twilio account setup and webhook configuration
    - Document OpenRouter/AI API key setup
    - Provide step-by-step local development setup
    - Add Docker deployment instructions
    - _Requirements: 2.1, 7.1_
  
  - [x] 14.3 Create API documentation
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

- [ ] 16. Implement system prompt and AI personality configuration
  - [ ] 16.1 Add system prompt configuration to Config class
    - Add AI_SYSTEM_PROMPT environment variable to Config
    - Add AI_SYSTEM_PROMPT_FILE environment variable for loading from file
    - Implement validation to ensure at least one is configured
    - Add default system prompt if none provided
    - _Requirements: 2.1, 2.2_
  
  - [ ] 16.2 Add system_prompt field to AIConfiguration model
    - Add TextField for storing custom system prompts per configuration
    - Create migration to add the new field
    - Update AIConfiguration admin to allow editing system prompts
    - _Requirements: 2.1, 5.1_
  
  - [ ] 16.3 Update MessageProcessor to inject system prompt
    - Modify _format_history_for_ai() to prepend system message
    - Load system prompt from AIConfiguration or Config
    - Ensure system message is always first in conversation history
    - Add system prompt to conversation context
    - _Requirements: 3.1, 4.2_
  
  - [ ] 16.4 Update AI adapters to handle system messages
    - Ensure OpenRouterAdapter properly formats system role messages
    - Test system message injection with different AI providers
    - Verify system prompt is not stored in conversation history
    - _Requirements: 2.2, 3.2_
  
  - [ ] 16.5 Create management command to manage system prompts
    - Add subcommand to manage_ai_config for viewing/updating system prompts
    - Support loading system prompt from file
    - Add validation for system prompt length and format
    - Provide example system prompts for common use cases
    - _Requirements: 2.1, 2.4_
  
  - [ ] 16.6 Update documentation for system prompt configuration
    - Document AI_SYSTEM_PROMPT environment variable in README
    - Add examples of effective system prompts
    - Document how to configure different personalities per AI configuration
    - Add troubleshooting guide for system prompt issues
    - _Requirements: 7.2_

- [ ] 17. Optional enhancements and production readiness
  - [ ] 17.1 Integrate rate limiting with webhook view
    - Add RateLimiter check in WhatsAppWebhookView before processing
    - Return appropriate error response when rate limit exceeded
    - Send rate limit notification to user via WhatsApp
    - _Requirements: 5.3_
  
  - [ ] 17.2 Add input sanitization to message processing
    - Integrate Sanitizer.sanitize_message() in MessageProcessor
    - Sanitize user input before sending to AI
    - Sanitize AI responses before sending to user
    - _Requirements: 5.3_
  
  - [ ] 17.3 Configure Django admin for models
    - Register all models in chatbot_core/admin.py
    - Add custom admin views for Conversation and Message models
    - Add filters and search capabilities for WebhookLog
    - Create admin actions for common operations
    - _Requirements: 6.4_
  
  - [ ] 17.4 Add monitoring and metrics
    - Implement Prometheus metrics for message processing
    - Add custom metrics for AI API latency and errors
    - Track conversation statistics (active users, message volume)
    - Set up alerting for critical metrics
    - _Requirements: 6.1, 6.2_
  
  - [ ] 17.5 Implement webhook logging
    - Integrate WebhookLog model with webhook view
    - Log all incoming webhook requests with timing
    - Log processing results and errors
    - Add admin interface for viewing webhook logs
    - _Requirements: 6.1, 6.2_
