# Requirements Document

## Introduction

This feature adds a resort activity booking system to the Django application, enabling users to discover, book, and manage resort activities (like watersports) through both a WhatsApp chatbot interface and a React web application. The system provides AI-powered activity recommendations, real-time availability checking, and a two-step booking confirmation process where bookings initiated via WhatsApp require web app approval.

## Requirements

### Requirement 1: Activity Management

**User Story:** As a resort administrator, I want to manage activity offerings with detailed information, so that guests can view and book available activities.

#### Acceptance Criteria

1. WHEN an administrator creates an activity THEN the system SHALL store activity name, description, category (e.g., watersports, spa, dining), price, duration, and images
2. WHEN an administrator sets activity availability THEN the system SHALL support time slots with capacity limits and date ranges
3. WHEN an administrator updates activity information THEN the system SHALL reflect changes immediately in both WhatsApp and web interfaces
4. IF an activity is marked as inactive THEN the system SHALL hide it from guest-facing interfaces while preserving historical booking data
5. WHEN defining time slots THEN the system SHALL support recurring schedules (daily, weekly) and specific date overrides

### Requirement 2: WhatsApp Chatbot Activity Discovery

**User Story:** As a guest, I want to discover activities through the WhatsApp chatbot, so that I can explore options conversationally.

#### Acceptance Criteria

1. WHEN a guest asks about activities THEN the chatbot SHALL list available activities with name, price, and duration
2. WHEN a guest requests activity details THEN the chatbot SHALL provide full description, pricing, duration, and available time slots
3. WHEN a guest asks for recommendations THEN the chatbot SHALL suggest activities based on conversation context and user preferences
4. IF a guest specifies preferences (e.g., "water activities", "morning slots") THEN the chatbot SHALL filter results accordingly
5. WHEN displaying activities THEN the chatbot SHALL format information clearly with pricing in the configured currency

### Requirement 3: AI-Powered Activity Recommendations

**User Story:** As a guest, I want personalized activity recommendations based on my interests, so that I can discover activities I'll enjoy.

#### Acceptance Criteria

1. WHEN a guest mentions interests or preferences THEN the system SHALL store these preferences linked to their phone number
2. WHEN generating recommendations THEN the AI SHALL consider user preferences, past bookings, time of day, and activity popularity
3. WHEN a guest asks "what should I do?" THEN the chatbot SHALL proactively suggest 2-3 relevant activities with reasoning
4. IF a guest has no booking history THEN the system SHALL recommend popular activities and ask clarifying questions
5. WHEN preferences are updated THEN the system SHALL use the latest preferences for future recommendations

### Requirement 4: Real-Time Availability Checking

**User Story:** As a guest, I want to see real-time availability for activities, so that I can book time slots that are actually available.

#### Acceptance Criteria

1. WHEN a guest views an activity THEN the system SHALL display available time slots for the next 14 days
2. WHEN checking availability THEN the system SHALL account for existing bookings and capacity limits
3. IF a time slot is fully booked THEN the system SHALL mark it as unavailable and suggest alternative times
4. WHEN multiple guests view the same activity THEN the system SHALL prevent double-booking through database-level constraints
5. WHEN availability changes THEN the system SHALL reflect updates within 5 seconds across all interfaces

### Requirement 5: WhatsApp Booking Initiation

**User Story:** As a guest, I want to book activities through WhatsApp, so that I can make reservations conversationally.

#### Acceptance Criteria

1. WHEN a guest selects an activity and time slot THEN the chatbot SHALL create a pending booking with status "awaiting_confirmation"
2. WHEN creating a booking THEN the system SHALL capture guest phone number, activity, time slot, number of participants, and special requests
3. WHEN a booking is created THEN the chatbot SHALL confirm details and inform the guest to check the web app for final confirmation
4. IF the selected time slot becomes unavailable during booking THEN the system SHALL notify the guest and suggest alternatives
5. WHEN a booking is pending THEN the system SHALL hold the time slot for 30 minutes before releasing it

### Requirement 6: React Web Application - Activity Browsing

**User Story:** As a guest, I want to browse activities in a web interface, so that I can explore options visually with detailed information.

#### Acceptance Criteria

1. WHEN a guest accesses the web app THEN the system SHALL display a grid/list of available activities with images and key details
2. WHEN viewing an activity THEN the system SHALL show full description, pricing, duration, images, and a calendar of availability
3. WHEN filtering activities THEN the system SHALL support filtering by category, price range, duration, and date
4. WHEN searching THEN the system SHALL support text search across activity names and descriptions
5. WHEN viewing availability THEN the system SHALL display a calendar with available/unavailable time slots color-coded

### Requirement 7: React Web Application - Booking Management

**User Story:** As a guest, I want to view and manage my bookings in the web app, so that I can confirm, modify, or cancel reservations.

#### Acceptance Criteria

1. WHEN a guest logs into the web app THEN the system SHALL display all their bookings (pending, confirmed, completed, cancelled)
2. WHEN viewing a pending booking THEN the system SHALL prominently display "Accept" and "Decline" buttons
3. WHEN a guest accepts a booking THEN the system SHALL update status to "confirmed" and send WhatsApp confirmation
4. WHEN a guest declines a booking THEN the system SHALL update status to "cancelled", release the time slot, and notify via WhatsApp
5. WHEN viewing confirmed bookings THEN the system SHALL allow cancellation up to 24 hours before the activity time
6. WHEN a booking is within 24 hours THEN the system SHALL display it as non-cancellable with appropriate messaging

### Requirement 8: User Authentication and Authorization

**User Story:** As a guest, I want secure access to my bookings, so that only I can view and manage my reservations.

#### Acceptance Criteria

1. WHEN a guest first accesses the web app THEN the system SHALL require phone number verification via OTP
2. WHEN a guest enters their phone number THEN the system SHALL send a verification code via WhatsApp
3. WHEN the OTP is verified THEN the system SHALL create a session and display bookings for that phone number
4. IF a guest tries to access another user's booking THEN the system SHALL deny access and return a 403 error
5. WHEN a session expires THEN the system SHALL require re-authentication

### Requirement 9: Booking Notifications

**User Story:** As a guest, I want to receive timely notifications about my bookings, so that I stay informed about my reservations.

#### Acceptance Criteria

1. WHEN a booking is created via WhatsApp THEN the system SHALL send a confirmation message with booking details and web app link
2. WHEN a booking is confirmed via web app THEN the system SHALL send a WhatsApp confirmation with activity details and timing
3. WHEN a booking is declined THEN the system SHALL send a WhatsApp notification explaining the cancellation
4. WHEN a booking is 24 hours away THEN the system SHALL send a reminder via WhatsApp
5. WHEN a booking is 1 hour away THEN the system SHALL send a final reminder with location details

### Requirement 10: Data Persistence and Integrity

**User Story:** As a system administrator, I want reliable data storage, so that booking information is never lost and remains consistent.

#### Acceptance Criteria

1. WHEN any booking operation occurs THEN the system SHALL use PostgreSQL transactions to ensure data consistency
2. WHEN concurrent bookings occur THEN the system SHALL use database locks to prevent race conditions
3. WHEN storing user data THEN the system SHALL comply with data retention policies and GDPR requirements
4. IF a database operation fails THEN the system SHALL rollback changes and log the error
5. WHEN querying bookings THEN the system SHALL use indexed fields for optimal performance

### Requirement 11: Admin Dashboard

**User Story:** As a resort administrator, I want to view and manage all bookings, so that I can oversee operations and handle issues.

#### Acceptance Criteria

1. WHEN an admin accesses the dashboard THEN the system SHALL display all bookings with filtering by date, status, and activity
2. WHEN viewing a booking THEN the admin SHALL see guest contact information, activity details, and booking history
3. WHEN necessary THEN the admin SHALL be able to manually confirm, cancel, or modify bookings
4. WHEN viewing analytics THEN the system SHALL display booking trends, popular activities, and revenue metrics
5. WHEN an admin makes changes THEN the system SHALL log the action and notify affected guests

### Requirement 12: Error Handling and Edge Cases

**User Story:** As a guest, I want the system to handle errors gracefully, so that I receive helpful feedback when issues occur.

#### Acceptance Criteria

1. WHEN a booking fails THEN the system SHALL provide a clear error message explaining the issue
2. IF the WhatsApp API is unavailable THEN the system SHALL queue notifications for retry
3. WHEN a time slot expires during booking THEN the system SHALL notify the user and suggest alternatives
4. IF the web app loses connection THEN the system SHALL display offline status and queue actions for retry
5. WHEN an unexpected error occurs THEN the system SHALL log details for debugging and display a user-friendly message
