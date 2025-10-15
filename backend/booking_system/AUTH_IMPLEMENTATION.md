# Authentication System Implementation

## Overview

This document describes the authentication system implemented for the resort activity booking system. The system uses OTP (One-Time Password) verification via WhatsApp for user authentication.

## Components Implemented

### 1. OTP Generation and Storage (`booking_system/auth.py`)

**Functions:**
- `generate_otp()` - Generates a 6-digit random OTP code
- `store_otp(phone_number, otp)` - Stores OTP in Redis with 5-minute expiry
- `verify_otp(phone_number, otp)` - Verifies OTP from Redis
- `delete_otp(phone_number)` - Deletes OTP after verification
- `generate_session_token()` - Generates secure session token
- `store_session(token, phone_number)` - Stores session in Redis with 24-hour expiry
- `get_phone_from_session(token)` - Retrieves phone number from session token
- `delete_session(token)` - Deletes session from Redis
- `check_rate_limit(phone_number)` - Enforces rate limiting (3 requests per 10 minutes)

**Redis Keys:**
- `otp:{phone_number}` - Stores OTP with 5-minute TTL
- `session:{token}` - Stores phone number with 24-hour TTL
- `rate_limit:{phone_number}` - Tracks OTP requests with 10-minute TTL

### 2. API Endpoints (`booking_system/auth_views.py`)

#### POST /api/v1/auth/request-otp/
Request OTP for phone number verification.

**Request:**
```json
{
  "phone_number": "+12345678900"
}
```

**Response (Success):**
```json
{
  "message": "OTP sent successfully",
  "phone_number": "+12345678900",
  "remaining_requests": 2
}
```

**Response (Rate Limited):**
```json
{
  "error": "Rate limit exceeded. Please try again later.",
  "detail": "Maximum 3 OTP requests per 10 minutes."
}
```

**Features:**
- Validates phone number format (E.164)
- Enforces rate limiting (max 3 requests per 10 minutes)
- Sends OTP via WhatsApp using existing Twilio integration
- Returns remaining request count

#### POST /api/v1/auth/verify-otp/
Verify OTP and create session.

**Request:**
```json
{
  "phone_number": "+12345678900",
  "otp": "123456"
}
```

**Response (Success):**
```json
{
  "message": "OTP verified successfully",
  "session_token": "abc123...",
  "phone_number": "+12345678900"
}
```

**Response (Invalid OTP):**
```json
{
  "error": "Invalid or expired OTP"
}
```

**Features:**
- Verifies OTP from Redis
- Deletes OTP after successful verification
- Generates and stores session token
- Returns session token for subsequent requests

#### POST /api/v1/auth/logout/
Logout and delete session.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

#### GET /api/v1/auth/me/
Get current user information.

**Headers:**
```
Authorization: Bearer <session_token>
```

**Response:**
```json
{
  "phone_number": "+12345678900",
  "authenticated": true
}
```

### 3. Authentication Class (`booking_system/authentication.py`)

**SessionTokenAuthentication**
- Custom DRF authentication class
- Validates session tokens from Redis
- Expects `Authorization: Bearer <token>` header
- Sets `request.auth` to phone number for authenticated requests
- Returns 401 for invalid/expired tokens

**Helper Function:**
- `get_user_phone(request)` - Extracts phone number from authenticated request

### 4. Permission Classes (`booking_system/permissions.py`)

**IsOwnerOrReadOnly**
- Allows read access to booking owners
- Allows write access only to booking owners
- Checks `request.auth` (phone number) against `booking.user_phone`

**IsAuthenticated**
- Requires valid session token
- Checks for presence of `request.auth`

### 5. Serializers (`booking_system/serializers.py`)

**RequestOTPSerializer**
- Validates phone number format (E.164)
- Pattern: `^\+[1-9]\d{1,14}$`

**VerifyOTPSerializer**
- Validates phone number format
- Validates OTP is 6 digits

### 6. Updated Views (`booking_system/views.py`)

**BookingViewSet**
- Added `SessionTokenAuthentication` to authentication_classes
- Added `IsAuthenticated` and `IsOwnerOrReadOnly` to permission_classes
- Updated `get_queryset()` to filter by authenticated user's phone
- Updated `create()` to use authenticated user's phone
- Updated `confirm()` to use authenticated user's phone
- Updated `cancel()` to use authenticated user's phone

## Security Features

1. **OTP Security**
   - 6-digit random codes
   - 5-minute expiration
   - Deleted after verification
   - Rate limiting (3 requests per 10 minutes)

2. **Session Security**
   - Cryptographically secure tokens (32 bytes)
   - 24-hour expiration
   - Stored in Redis (not in database)
   - Can be invalidated via logout

3. **Phone Number Validation**
   - E.164 format enforcement
   - Prevents invalid phone numbers

4. **Authorization**
   - Users can only access their own bookings
   - Phone number verification required for all booking operations

## Usage Example

### 1. Request OTP
```bash
curl -X POST http://localhost:8000/api/v1/auth/request-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+12345678900"}'
```

### 2. Verify OTP
```bash
curl -X POST http://localhost:8000/api/v1/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+12345678900", "otp": "123456"}'
```

### 3. Use Session Token
```bash
curl -X GET http://localhost:8000/api/v1/bookings/ \
  -H "Authorization: Bearer <session_token>"
```

### 4. Logout
```bash
curl -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Authorization: Bearer <session_token>"
```

## Requirements Satisfied

✅ **Requirement 8.1**: Phone number verification via OTP
✅ **Requirement 8.2**: OTP sent via WhatsApp
✅ **Requirement 8.3**: Session creation after OTP verification
✅ **Requirement 8.4**: Authorization - users can only access their own bookings
✅ **Requirement 8.5**: Session expiration and re-authentication
✅ **Requirement 12.1**: Error handling with clear messages

## Testing

To test the authentication system:

1. Ensure Redis is running
2. Ensure Twilio credentials are configured in `.env`
3. Run Django development server: `python manage.py runserver`
4. Use the API endpoints as shown in the usage examples above

## Notes

- The system does not use Django's built-in User model
- Authentication is based solely on phone numbers
- Sessions are stored in Redis for fast access and automatic expiration
- Rate limiting prevents OTP spam
- All booking operations require authentication
