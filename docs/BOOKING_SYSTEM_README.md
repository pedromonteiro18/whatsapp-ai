# Resort Activity Booking System - Documentation

This document provides comprehensive documentation for the resort activity booking system, including setup, API reference, and operational guidelines.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup Instructions](#setup-instructions)
4. [API Reference](#api-reference)
5. [Environment Variables](#environment-variables)
6. [Celery Tasks](#celery-tasks)
7. [WhatsApp Integration](#whatsapp-integration)
8. [Frontend Application](#frontend-application)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Resort Activity Booking System enables guests to discover, book, and manage resort activities through both WhatsApp chatbot and a web application. The system provides a seamless two-step booking process:

1. **Discovery via WhatsApp**: Guests can browse activities, get personalized recommendations, and initiate bookings through natural conversations
2. **Confirmation via Web**: Guests receive a link to confirm their pending booking through a React web application

### Key Features

- **Activity Management**: Browse activities by category, search, and filter by price range
- **Time Slot Management**: Real-time availability checking with capacity management
- **Dual Booking Interface**: WhatsApp chatbot initiation + web-based confirmation
- **Passwordless Authentication**: OTP-based authentication via WhatsApp
- **Automated Notifications**: Booking confirmations, reminders, and cancellation notices
- **AI-Powered Recommendations**: Personalized activity suggestions based on user preferences
- **Automatic Expiry**: Pending bookings expire after 30 minutes if not confirmed
- **Flexible Cancellations**: Cancel bookings up to 24 hours before activity start

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        WhatsApp User                             │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                   │
               │ Initiate Booking                  │ Confirm Booking
               │                                   │
               ▼                                   ▼
┌──────────────────────┐              ┌──────────────────────────┐
│  Twilio WhatsApp API │              │   React Web Application  │
│                      │              │   (Port 5173)            │
└──────────┬───────────┘              └────────────┬─────────────┘
           │                                       │
           │ Webhook                               │ REST API
           │                                       │
           ▼                                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Django Backend (Port 8000)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  WhatsApp    │  │  Booking     │  │  Authentication      │  │
│  │  Webhook     │  │  API         │  │  (OTP)               │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Booking     │  │  AI          │  │  Notification        │  │
│  │  Processor   │  │  Adapter     │  │  Service             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└────────────┬──────────────────────────────────┬─────────────────┘
             │                                   │
             │                                   │
    ┌────────▼─────────┐              ┌─────────▼──────────┐
    │   PostgreSQL     │              │   Redis Cache      │
    │   Database       │              │   - Sessions       │
    │   - Activities   │              │   - OTP Codes      │
    │   - Bookings     │              │   - Rate Limiting  │
    │   - Time Slots   │              │   - Celery Queue   │
    └──────────────────┘              └────────────────────┘
                                                │
                                                │
                                      ┌─────────▼──────────┐
                                      │   Celery Workers   │
                                      │   - Expire pending │
                                      │   - Send reminders │
                                      └────────────────────┘
```

### Data Models

#### Activity
- **Purpose**: Represents resort activities (watersports, spa, dining, etc.)
- **Key Fields**: name, slug, description, category, price, duration, max_capacity, location
- **Relationships**: Has many ActivityImages, has many TimeSlots

#### TimeSlot
- **Purpose**: Represents available booking times for activities
- **Key Fields**: start_time, end_time, available_capacity, booked_count, is_active
- **Constraints**:
  - `booked_count <= available_capacity`
  - Unique constraint on `(activity, start_time)`

#### Booking
- **Purpose**: Tracks user bookings with lifecycle management
- **Key Fields**: user_phone, activity, time_slot, num_people, status, total_price, expires_at
- **Status Flow**: pending → confirmed/cancelled/expired
- **Business Rules**:
  - Pending bookings expire after 30 minutes
  - Cancellations allowed up to 24 hours before activity
  - Capacity automatically managed via database constraints

#### UserPreference
- **Purpose**: Stores user preferences for AI recommendations
- **Key Fields**: user_phone, interests (JSON), preferred_categories, budget_range

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- PostgreSQL 14+
- Redis 7+
- Twilio account with WhatsApp enabled

### Backend Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (see Environment Variables section)
   ```

3. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Set up booking system data** (optional but recommended for testing):
   ```bash
   # Step 1: Create sample activities (watersports, spa, dining, adventure, wellness)
   python manage.py seed_activities

   # Step 2: Generate time slots for the next 60 days (4 slots per day per activity)
   python manage.py generate_timeslots --days 60 --slots-per-day 4

   # Step 3: Download themed activity images from Pexels (requires PEXELS_API_KEY)
   python manage.py download_activity_images
   ```

6. **Start Django development server**:
   ```bash
   python manage.py runserver
   ```

7. **Start Celery worker** (separate terminal):
   ```bash
   celery -A backend.whatsapp_ai_chatbot worker --loglevel=info
   ```

8. **Start Celery beat** (separate terminal):
   ```bash
   celery -A backend.whatsapp_ai_chatbot beat --loglevel=info
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env (usually defaults work for local development)
   ```

4. **Start development server**:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`

### Docker Setup (Alternative)

```bash
# Start all services
docker-compose -f infrastructure/docker-compose.yml up --build

# Run migrations
docker-compose exec web python backend/manage.py migrate

# Create superuser
docker-compose exec web python backend/manage.py createsuperuser

# Set up booking system data (recommended for testing)
# Step 1: Seed sample activities
docker-compose exec web python backend/manage.py seed_activities

# Step 2: Generate time slots for next 60 days
docker-compose exec web python backend/manage.py generate_timeslots --days 60 --slots-per-day 4

# Step 3: Download activity images (requires PEXELS_API_KEY in .env)
docker-compose exec web python backend/manage.py download_activity_images
```

---

## API Reference

### Base URL

Development: `http://localhost:8000/api/v1`

### Authentication

Most booking-related endpoints require authentication via session token.

#### Request OTP

**Endpoint**: `POST /auth/request-otp/`

**Description**: Sends a 6-digit OTP to the user's WhatsApp number

**Request Body**:
```json
{
  "phone_number": "+1234567890"
}
```

**Phone Number Format**:
All phone numbers are automatically normalized to E.164 format (`+[country code][number]`) before processing. The system accepts various input formats:
- With/without country code: `1234567890` → `+11234567890`
- With spaces or dashes: `+1 (234) 567-8900` → `+12345678900`
- WhatsApp prefix: `whatsapp:+1234567890` → `+12345678900`

**Response** (200 OK):
```json
{
  "message": "OTP sent successfully via WhatsApp",
  "expires_in": 300
}
```

**Rate Limiting**: 3 requests per 10 minutes per phone number

---

#### Verify OTP

**Endpoint**: `POST /auth/verify-otp/`

**Description**: Verifies OTP and returns session token

**Request Body**:
```json
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

**Response** (200 OK):
```json
{
  "session_token": "abc123def456...",
  "message": "Authentication successful"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid OTP or expired
- `429 Too Many Requests`: Too many verification attempts

---

#### Logout

**Endpoint**: `POST /auth/logout/`

**Description**: Invalidates session token

**Headers**:
```
Authorization: Bearer <session_token>
```

**Response** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

---

#### Current User

**Endpoint**: `GET /auth/me/`

**Description**: Returns current authenticated user information

**Headers**:
```
Authorization: Bearer <session_token>
```

**Response** (200 OK):
```json
{
  "phone_number": "+1234567890",
  "is_authenticated": true
}
```

---

### Activities API

#### List Activities

**Endpoint**: `GET /activities/`

**Description**: Retrieve list of activities with filtering and search

**Query Parameters**:
- `category` (optional): Filter by category (watersports, spa, dining, adventure, wellness)
- `search` (optional): Search by name or description
- `min_price` (optional): Minimum price filter
- `max_price` (optional): Maximum price filter
- `ordering` (optional): Sort by field (price, -price, created_at, -created_at)

**Response** (200 OK):
```json
{
  "count": 15,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "Scuba Diving Adventure",
      "slug": "scuba-diving-adventure",
      "description": "Explore vibrant coral reefs...",
      "category": "watersports",
      "price_per_person": "150.00",
      "duration_minutes": 120,
      "max_capacity": 6,
      "location": "Main Beach",
      "is_active": true,
      "images": [
        {
          "id": "uuid",
          "image": "/media/activities/scuba-diving.jpg",
          "alt_text": "Scuba diving underwater",
          "is_primary": true,
          "order": 1
        }
      ],
      "primary_image": "/media/activities/scuba-diving.jpg",
      "created_at": "2025-01-10T10:00:00Z"
    }
  ]
}
```

**Example Requests**:
```bash
# List all activities
curl http://localhost:8000/api/v1/activities/

# Filter by category
curl http://localhost:8000/api/v1/activities/?category=watersports

# Search and filter
curl "http://localhost:8000/api/v1/activities/?search=diving&min_price=100&max_price=200"

# Sort by price (ascending)
curl http://localhost:8000/api/v1/activities/?ordering=price
```

---

#### Get Activity Detail

**Endpoint**: `GET /activities/{id}/`

**Description**: Retrieve detailed information about a specific activity

**Response** (200 OK):
```json
{
  "id": "uuid",
  "name": "Scuba Diving Adventure",
  "slug": "scuba-diving-adventure",
  "description": "Explore vibrant coral reefs with professional instructors...",
  "category": "watersports",
  "price_per_person": "150.00",
  "duration_minutes": 120,
  "max_capacity": 6,
  "location": "Main Beach",
  "requirements": "Must be able to swim. Minimum age 12 years.",
  "is_active": true,
  "images": [
    {
      "id": "uuid",
      "image": "/media/activities/scuba-diving.jpg",
      "alt_text": "Scuba diving underwater",
      "is_primary": true,
      "order": 1
    }
  ],
  "primary_image": "/media/activities/scuba-diving.jpg",
  "created_at": "2025-01-10T10:00:00Z",
  "updated_at": "2025-01-15T14:30:00Z"
}
```

---

#### Check Availability

**Endpoint**: `GET /activities/{id}/availability/`

**Description**: Get available time slots for an activity

**Query Parameters**:
- `date` (required): Date to check availability (YYYY-MM-DD format)
- `days` (optional): Number of days to check (default: 1, max: 14)

**Response** (200 OK):
```json
{
  "activity_id": "uuid",
  "activity_name": "Scuba Diving Adventure",
  "availability": [
    {
      "date": "2025-01-20",
      "time_slots": [
        {
          "id": "uuid",
          "start_time": "2025-01-20T09:00:00Z",
          "end_time": "2025-01-20T11:00:00Z",
          "available_capacity": 6,
          "booked_count": 2,
          "is_available": true
        },
        {
          "id": "uuid",
          "start_time": "2025-01-20T14:00:00Z",
          "end_time": "2025-01-20T16:00:00Z",
          "available_capacity": 6,
          "booked_count": 6,
          "is_available": false
        }
      ]
    }
  ]
}
```

**Example Request**:
```bash
# Check availability for next 7 days
curl "http://localhost:8000/api/v1/activities/{id}/availability/?date=2025-01-20&days=7"
```

---

### Bookings API

All booking endpoints require authentication (session token).

#### List Bookings

**Endpoint**: `GET /bookings/`

**Description**: List all bookings for the authenticated user

**Headers**:
```
Authorization: Bearer <session_token>
```

**Query Parameters**:
- `status` (optional): Filter by status (pending, confirmed, cancelled, completed, no_show)

**Response** (200 OK):
```json
{
  "count": 3,
  "results": [
    {
      "id": "uuid",
      "activity": {
        "id": "uuid",
        "name": "Scuba Diving Adventure",
        "category": "watersports",
        "price_per_person": "150.00"
      },
      "time_slot": {
        "id": "uuid",
        "start_time": "2025-01-20T09:00:00Z",
        "end_time": "2025-01-20T11:00:00Z"
      },
      "num_people": 2,
      "total_price": "300.00",
      "status": "pending",
      "special_requests": "Vegetarian lunch option",
      "booking_source": "whatsapp",
      "created_at": "2025-01-17T10:30:00Z",
      "confirmed_at": null,
      "cancelled_at": null,
      "expires_at": "2025-01-17T11:00:00Z"
    }
  ]
}
```

---

#### Create Booking

**Endpoint**: `POST /bookings/`

**Description**: Create a new pending booking

**Headers**:
```
Authorization: Bearer <session_token>
```

**Request Body**:
```json
{
  "activity_id": "uuid",
  "time_slot_id": "uuid",
  "num_people": 2,
  "special_requests": "Vegetarian lunch option"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "activity": {
    "id": "uuid",
    "name": "Scuba Diving Adventure",
    "category": "watersports",
    "price_per_person": "150.00"
  },
  "time_slot": {
    "id": "uuid",
    "start_time": "2025-01-20T09:00:00Z",
    "end_time": "2025-01-20T11:00:00Z"
  },
  "num_people": 2,
  "total_price": "300.00",
  "status": "pending",
  "special_requests": "Vegetarian lunch option",
  "booking_source": "web",
  "created_at": "2025-01-17T10:30:00Z",
  "expires_at": "2025-01-17T11:00:00Z",
  "message": "Booking created successfully. Please confirm within 30 minutes."
}
```

**Error Responses**:
- `400 Bad Request`: Time slot unavailable, past time slot, or validation error
- `401 Unauthorized`: Invalid or missing session token

---

#### Confirm Booking

**Endpoint**: `POST /bookings/{id}/confirm/`

**Description**: Confirm a pending booking

**Headers**:
```
Authorization: Bearer <session_token>
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "status": "confirmed",
  "confirmed_at": "2025-01-17T10:35:00Z",
  "message": "Booking confirmed successfully. You will receive a confirmation via WhatsApp."
}
```

**Error Responses**:
- `400 Bad Request`: Booking not in pending status or expired
- `403 Forbidden`: Booking doesn't belong to authenticated user
- `404 Not Found`: Booking not found

---

#### Cancel Booking

**Endpoint**: `POST /bookings/{id}/cancel/`

**Description**: Cancel a booking

**Headers**:
```
Authorization: Bearer <session_token>
```

**Request Body** (optional):
```json
{
  "reason": "Change of plans"
}
```

**Response** (200 OK):
```json
{
  "id": "uuid",
  "status": "cancelled",
  "cancelled_at": "2025-01-17T11:00:00Z",
  "message": "Booking cancelled successfully. You will receive a confirmation via WhatsApp."
}
```

**Error Responses**:
- `400 Bad Request`: Cancellation deadline passed (within 24 hours of activity)
- `403 Forbidden`: Booking doesn't belong to authenticated user
- `404 Not Found`: Booking not found

---

### Recommendations API

#### Get Personalized Recommendations

**Endpoint**: `GET /recommendations/`

**Description**: Get AI-powered activity recommendations based on user preferences

**Headers**:
```
Authorization: Bearer <session_token>
```

**Query Parameters**:
- `limit` (optional): Maximum number of recommendations (default: 5, max: 10)

**Response** (200 OK):
```json
{
  "recommendations": [
    {
      "activity": {
        "id": "uuid",
        "name": "Scuba Diving Adventure",
        "category": "watersports",
        "price_per_person": "150.00",
        "duration_minutes": 120
      },
      "score": 0.95,
      "reasoning": "Based on your interest in adventure activities and previous watersports bookings, scuba diving would be a perfect fit. The activity matches your preferred price range and is available during your preferred times."
    }
  ]
}
```

---

## Environment Variables

### Backend Environment Variables

Create a `.env` file in the project root with the following variables:

#### Django Settings
```bash
SECRET_KEY=your-secret-key-here
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### Database Configuration
```bash
DB_NAME=whatsapp_chatbot
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost  # Use "db" for Docker
DB_PORT=5432
```

#### Redis Configuration
```bash
REDIS_HOST=localhost  # Use "redis" for Docker
REDIS_PORT=6379
REDIS_DB=0
```

#### Celery Configuration
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

#### Twilio Configuration
```bash
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

#### AI Configuration (OpenRouter)
```bash
OPENROUTER_API_KEY=your-openrouter-api-key
AI_MODEL=openai/gpt-4
AI_MAX_TOKENS=500
AI_TEMPERATURE=0.7
```

#### Application Settings
```bash
MAX_CONVERSATION_HISTORY=10
SESSION_TIMEOUT_MINUTES=30
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
```

#### Booking System Settings
```bash
# Public URL of the React frontend (used in WhatsApp notifications)
BOOKING_WEB_APP_URL=http://localhost:5173

# Booking timeouts and policies
BOOKING_PENDING_TIMEOUT_MINUTES=30
BOOKING_CANCELLATION_DEADLINE_HOURS=24
```

#### Development Shortcuts (Optional)
```bash
# Development only: Skip WhatsApp OTP delivery for faster testing
# When set, this code will be accepted instead of waiting for WhatsApp messages
# ⚠️ NEVER set this in production - it's a security risk!
DEV_OTP_CODE=000000

# Optional: API key for downloading themed activity images from Pexels
# Get a free key at https://www.pexels.com/api/
PEXELS_API_KEY=your-pexels-api-key-here
```

#### CORS Configuration (Production)
```bash
# Comma-separated list of allowed origins
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,https://api.twilio.com
```

### Frontend Environment Variables

Create a `frontend/.env` file:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000/api/v1
```

For production, set this to your deployed backend URL.

---

## Celery Tasks

The booking system uses Celery for background job processing with the following periodic tasks:

### 1. Expire Pending Bookings

**Task**: `backend.booking_system.tasks.expire_pending_bookings`

**Schedule**: Every 5 minutes

**Description**: Automatically expires pending bookings that haven't been confirmed within the timeout period (30 minutes by default)

**Actions**:
1. Queries all pending bookings where `expires_at < now()`
2. Updates booking status to "cancelled"
3. Decrements the time slot's `booked_count`
4. Logs the expiration

**Configuration**:
```python
# In celery.py CELERY_BEAT_SCHEDULE
"expire-pending-bookings": {
    "task": "backend.booking_system.tasks.expire_pending_bookings",
    "schedule": crontab(minute="*/5"),
}
```

---

### 2. Send 24-Hour Reminders

**Task**: `backend.booking_system.tasks.send_reminder_24h`

**Schedule**: Every hour

**Description**: Sends reminder messages via WhatsApp 24 hours before the activity starts

**Actions**:
1. Queries confirmed bookings with start time in ~24 hours
2. Excludes bookings that have already been reminded
3. Sends WhatsApp reminder with activity details
4. Marks booking as reminded in metadata

**Message Format**:
```
🔔 Reminder: Your activity is tomorrow!

Activity: Scuba Diving Adventure
Date: January 20, 2025 at 9:00 AM
Duration: 2 hours
Participants: 2 people
Location: Main Beach

📋 What to bring:
- Swimwear and towel
- Sunscreen
- Water bottle

⚠️ Cancellation Policy:
Free cancellation up to 24 hours before the activity.
After that, cancellations are not allowed.

Need to cancel? Reply with "cancel booking" or visit: http://localhost:5173/bookings

See you tomorrow! 🌊
```

**Configuration**:
```python
"send-24h-reminders": {
    "task": "backend.booking_system.tasks.send_reminder_24h",
    "schedule": crontab(minute=0),  # Every hour at :00
}
```

---

### 3. Send 1-Hour Reminders

**Task**: `backend.booking_system.tasks.send_reminder_1h`

**Schedule**: Every 15 minutes

**Description**: Sends final reminder messages 1 hour before the activity starts

**Actions**:
1. Queries confirmed bookings with start time in ~1 hour
2. Excludes bookings that have already received 1-hour reminder
3. Sends urgent WhatsApp reminder
4. Updates reminder metadata

**Message Format**:
```
🚨 Final Reminder: Your activity starts in 1 hour!

Activity: Scuba Diving Adventure
Start Time: 9:00 AM (in 1 hour)
Meeting Point: Main Beach

Please arrive 10 minutes early for check-in.

📍 Directions: [Location details]

⚠️ Cancellations are no longer allowed.

Questions? Contact us or visit: http://localhost:5173/bookings

Get ready for an amazing experience! 🎉
```

**Configuration**:
```python
"send-1h-reminders": {
    "task": "backend.booking_system.tasks.send_reminder_1h",
    "schedule": crontab(minute="*/15"),  # Every 15 minutes
}
```

---

### Monitoring Celery Tasks

View active tasks:
```bash
celery -A backend.whatsapp_ai_chatbot inspect active
```

View scheduled tasks:
```bash
celery -A backend.whatsapp_ai_chatbot inspect scheduled
```

View registered tasks:
```bash
celery -A backend.whatsapp_ai_chatbot inspect registered
```

Monitor task execution:
```bash
celery -A backend.whatsapp_ai_chatbot events
```

---

## WhatsApp Integration

### Booking Flow via WhatsApp

The booking system integrates with the existing WhatsApp chatbot to provide a conversational booking experience:

```
User: "I want to book scuba diving"
    ↓
[BookingMessageProcessor detects booking intent]
    ↓
Bot: "Great! I found these diving activities:
     1. Scuba Diving Adventure - $150/person
     2. Beginner Scuba Course - $200/person
     Which would you like to book?"
    ↓
User: "1"
    ↓
Bot: "Perfect! When would you like to go scuba diving?
     Available dates: Jan 20, Jan 21, Jan 22..."
    ↓
User: "January 20"
    ↓
Bot: "Available time slots for Jan 20:
     1. 9:00 AM - 11:00 AM (4 spots left)
     2. 2:00 PM - 4:00 PM (6 spots available)
     Which time works for you?"
    ↓
User: "9 AM"
    ↓
Bot: "How many people will be joining? (Max 6)"
    ↓
User: "2"
    ↓
[BookingService creates pending booking]
    ↓
Bot: "🎉 Booking initiated!

     Activity: Scuba Diving Adventure
     Date: January 20, 2025 at 9:00 AM
     Participants: 2 people
     Total: $300.00

     ⏰ IMPORTANT: This booking is pending and will expire in 30 minutes.

     Please confirm your booking here:
     http://localhost:5173/bookings

     You'll receive a confirmation once you complete the booking online."
    ↓
[User clicks link and confirms in web app]
    ↓
[NotificationService sends confirmation]
    ↓
Bot: "✅ Booking Confirmed!

     Your scuba diving adventure is confirmed for January 20, 2025 at 9:00 AM.

     📍 Location: Main Beach
     ⏱️ Duration: 2 hours
     👥 Participants: 2 people

     📋 Requirements: Must be able to swim. Minimum age 12 years.

     You'll receive reminders 24 hours and 1 hour before your activity.

     See you soon! 🌊"
```

### Booking Assistant Configuration

The booking system uses a specialized AI system prompt to handle booking-related conversations. The prompt defines the assistant's persona and behavior for the booking workflow.

#### System Prompt Location

The booking assistant system prompt is configured in `backend/whatsapp_ai_chatbot/settings.py` under the `BOOKING_ASSISTANT_SYSTEM_PROMPT` constant.

#### Current Configuration

The assistant is configured as:
- **Persona**: Friendly and helpful resort concierge
- **Tone**: Professional yet approachable
- **Capabilities**:
  - Activity browsing and recommendations
  - Multi-turn booking conversations
  - Time slot availability checks
  - Booking status inquiries
  - Cancellation requests
  - General resort information

#### Customizing the System Prompt

To customize the booking assistant's behavior:

1. Edit `backend/whatsapp_ai_chatbot/settings.py`
2. Locate the `BOOKING_ASSISTANT_SYSTEM_PROMPT` constant (around line 350-400)
3. Modify the prompt text to adjust:
   - Personality and tone
   - Handling of specific scenarios
   - Response formatting
   - Activity recommendation criteria
   - Special policies or requirements

**Example customizations**:
- Add resort-specific information (location, amenities, special offers)
- Include upselling strategies for premium activities
- Define handling of group bookings or special requests
- Set policies for weather-related cancellations
- Add multilingual support instructions

**Note**: After modifying the system prompt, restart the Django server and Celery workers for changes to take effect.

#### Integration with AI Adapter

The booking processor (`backend/chatbot_core/booking_processor.py`) uses the configured system prompt when sending messages to the AI adapter. This ensures consistent, booking-focused responses throughout the conversation.

### Booking Intent Detection

The `BookingMessageProcessor` (backend/chatbot_core/booking_processor.py) detects booking-related intents:

**Browse Intent**:
- Keywords: "show activities", "what can I do", "available activities", "browse"
- Action: Lists all active activities or filters by category

**Booking Intent**:
- Keywords: "book", "reserve", "I want to", "schedule"
- Action: Initiates multi-turn booking conversation

**Check Booking Intent**:
- Keywords: "my bookings", "check booking", "show reservations"
- Action: Lists user's bookings with status

**Cancel Intent**:
- Keywords: "cancel", "cancel booking"
- Action: Shows cancellable bookings and processes cancellation

**Recommendation Intent**:
- Keywords: "recommend", "suggest", "what should I do"
- Action: Provides AI-powered activity recommendations

### Notification Types

#### Booking Created (Pending)
Sent immediately after creating a pending booking via WhatsApp

#### Booking Confirmed
Sent after user confirms booking in web application

#### Booking Cancelled
Sent after user cancels booking (via WhatsApp or web)

#### 24-Hour Reminder
Automated reminder sent 24 hours before activity

#### 1-Hour Reminder
Final reminder sent 1 hour before activity starts

---

## Frontend Application

### Technology Stack

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **State Management**:
  - TanStack Query (React Query) for server state
  - React Context for auth state
- **HTTP Client**: Axios with interceptors
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui (Radix UI primitives)

### Project Structure

```
frontend/
├── src/
│   ├── api/                    # API client and service functions
│   │   ├── client.ts           # Axios instance with interceptors
│   │   └── index.ts            # All API service functions
│   ├── components/
│   │   ├── activities/         # Activity-related components
│   │   │   ├── ActivityCard.tsx
│   │   │   ├── ActivityFilter.tsx
│   │   │   ├── ActivityGrid.tsx
│   │   │   ├── ActivityDetail.tsx
│   │   │   └── AvailabilityCalendar.tsx
│   │   ├── bookings/           # Booking-related components
│   │   │   ├── BookingCard.tsx
│   │   │   ├── BookingActions.tsx
│   │   │   └── BookingList.tsx
│   │   ├── auth/               # Authentication components
│   │   │   ├── PhoneInput.tsx
│   │   │   └── OTPForm.tsx
│   │   ├── ui/                 # shadcn/ui components
│   │   └── ProtectedRoute.tsx
│   ├── contexts/               # React contexts
│   │   └── AuthContext.tsx     # Auth state management
│   ├── pages/                  # Page components
│   │   ├── LoginPage.tsx
│   │   ├── ActivitiesPage.tsx
│   │   ├── ActivityDetailPage.tsx
│   │   └── BookingsPage.tsx
│   ├── types/                  # TypeScript type definitions
│   ├── utils/                  # Utility functions
│   ├── App.tsx                 # Route definitions
│   └── main.tsx                # Application entry point
├── public/                     # Static assets
├── .env.example                # Environment variable template
├── package.json                # Dependencies
├── tailwind.config.js          # Tailwind configuration
├── tsconfig.json               # TypeScript configuration
└── vite.config.ts              # Vite configuration
```

### Key Features

#### Authentication Flow
1. User enters phone number → OTP sent via WhatsApp
2. User enters OTP code → Session token received
3. Token stored in localStorage
4. All API requests include token in Authorization header
5. Automatic logout on 401 responses

#### Activity Browsing
- Grid layout with responsive design
- Real-time filtering by category, search, price range
- Lazy loading for images
- Skeleton loaders during data fetching

#### Booking Management
- Pending bookings highlighted at top
- One-click confirmation/cancellation
- Countdown timer for pending bookings
- Real-time updates via React Query

#### Error Handling
- Global error boundary for React errors
- Toast notifications for user feedback
- Automatic retry for failed requests
- User-friendly error messages

### Running Frontend

**Development**:
```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
```

**Build for Production**:
```bash
npm run build
# Output in dist/ directory
```

**Preview Production Build**:
```bash
npm run preview
```

### Environment Configuration

**Development** (`frontend/.env`):
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

**Production**:
```bash
VITE_API_URL=https://api.your-resort.com/api/v1
```

---

## Troubleshooting

### Common Issues

#### 1. Booking Creation Fails with "Time slot unavailable"

**Symptoms**:
- API returns 400 error
- Message: "This time slot is no longer available"

**Causes**:
- Time slot capacity reached
- Concurrent booking attempts
- Time slot disabled by admin

**Solutions**:
1. Check time slot availability via `/activities/{id}/availability/`
2. Refresh activity details to get latest capacity
3. Try alternative time slots

---

#### 2. Pending Bookings Not Expiring

**Symptoms**:
- Pending bookings remain pending after 30 minutes
- Capacity not released

**Diagnosis**:
```bash
# Check if Celery beat is running
celery -A backend.whatsapp_ai_chatbot inspect active

# Check Celery beat logs
docker-compose logs celery_beat
```

**Solutions**:
1. Ensure Celery beat is running:
   ```bash
   celery -A backend.whatsapp_ai_chatbot beat --loglevel=info
   ```

2. Check task schedule in `backend/whatsapp_ai_chatbot/celery.py`

3. Manually trigger task:
   ```bash
   python backend/manage.py shell
   >>> from backend.booking_system.tasks import expire_pending_bookings
   >>> expire_pending_bookings.delay()
   ```

---

#### 3. OTP Not Received via WhatsApp

**Symptoms**:
- Request OTP returns success
- No WhatsApp message received

**Diagnosis**:
```bash
# Check Twilio configuration
python backend/manage.py test_whatsapp --check-config

# Check Celery worker logs
docker-compose logs celery_worker | grep OTP
```

**Solutions**:
1. Verify Twilio credentials in `.env`
2. Check Twilio account balance
3. Verify phone number format (E.164: +1234567890)
4. Check WhatsApp sandbox configuration (development)

---

#### 4. CORS Errors in Frontend

**Symptoms**:
- Browser console shows CORS errors
- API requests fail from frontend

**Diagnosis**:
Check browser console for error message:
```
Access to XMLHttpRequest at 'http://localhost:8000/api/v1/...'
from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solutions**:
1. Verify `CORS_ALLOWED_ORIGINS` in backend settings includes frontend URL
2. Check that frontend is running on expected port (5173)
3. For custom domains, add to `CORS_ALLOWED_ORIGINS` in `.env`:
   ```bash
   CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://your-custom-domain.com
   ```
4. Restart Django server after changing CORS settings

---

#### 5. Reminders Not Sending

**Symptoms**:
- No reminder messages sent
- Logs show no reminder tasks executed

**Diagnosis**:
```bash
# Check scheduled tasks
celery -A backend.whatsapp_ai_chatbot inspect scheduled

# Check beat schedule
cat backend/whatsapp_ai_chatbot/celery.py | grep -A 5 "CELERY_BEAT_SCHEDULE"
```

**Solutions**:
1. Verify Celery beat is running
2. Check reminder task configuration in celery.py
3. Verify bookings have future start times
4. Check Twilio WhatsApp integration is working

---

#### 6. Booking Cancellation Fails

**Symptoms**:
- API returns 400 error
- Message: "Cancellations not allowed within 24 hours of activity"

**Explanation**: This is expected behavior. Cancellation deadline is configurable via `BOOKING_CANCELLATION_DEADLINE_HOURS` (default: 24 hours)

**Solutions**:
1. For testing, reduce deadline in `.env`:
   ```bash
   BOOKING_CANCELLATION_DEADLINE_HOURS=1
   ```
2. For production, clearly communicate cancellation policy to users
3. Admin can override via Django admin if needed

---

### Debug Mode

Enable detailed logging for troubleshooting:

**Backend**:
```bash
# In .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart server
python backend/manage.py runserver
```

**View Logs**:
```bash
# Application logs
tail -f logs/whatsapp_chatbot.log

# Error logs only
tail -f logs/errors.log

# Celery worker logs
docker-compose logs -f celery_worker

# Celery beat logs
docker-compose logs -f celery_beat
```

---

### Database Queries

Useful SQL queries for debugging:

```sql
-- Check pending bookings
SELECT id, user_phone, status, created_at, expires_at
FROM booking_system_booking
WHERE status = 'pending'
ORDER BY expires_at ASC;

-- Check time slot capacity
SELECT a.name, ts.start_time, ts.available_capacity, ts.booked_count
FROM booking_system_timeslot ts
JOIN booking_system_activity a ON ts.activity_id = a.id
WHERE ts.start_time > NOW()
ORDER BY ts.start_time ASC;

-- Check recent bookings
SELECT b.id, u.phone_number AS user, a.name AS activity, b.status, b.created_at
FROM booking_system_booking b
JOIN booking_system_activity a ON b.activity_id = a.id
ORDER BY b.created_at DESC
LIMIT 20;

-- Find expired bookings not yet processed
SELECT id, user_phone, status, expires_at
FROM booking_system_booking
WHERE status = 'pending' AND expires_at < NOW();
```

---

### Getting Help

If you encounter issues not covered here:

1. **Check logs**: Review application, Celery, and Twilio logs
2. **Search documentation**: Review main README and API docs
3. **Test components**: Use management commands to test individual components
4. **Django admin**: Use admin interface to inspect data
5. **Create issue**: Open GitHub issue with:
   - Detailed description
   - Steps to reproduce
   - Log excerpts
   - Environment details
   - Configuration (sanitized)

---

## Additional Resources

- **Main README**: `/README.md` - Project overview and quick start
- **Setup Guide**: `/docs/SETUP.md` - Detailed setup instructions
- **API Documentation**: `/docs/API_DOCUMENTATION.md` - General API reference
- **Django Admin**: `http://localhost:8000/admin/` - Admin interface
- **Celery Flower**: `http://localhost:5555/` - Task monitoring (if configured)

---

## License

This booking system is part of the WhatsApp AI Chatbot project.
