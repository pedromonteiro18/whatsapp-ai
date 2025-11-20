"""
LangChain tools for the deep-agent hospitality concierge.

These tools wrap existing Django services (BookingService, models, etc.) to
provide structured actions the agent can take.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ===== Activity Tools =====


@tool
def search_activities(
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    limit: int = 8,
) -> str:
    """
    Search for available resort activities.

    Args:
        category: Filter by category (watersports, spa, dining, adventure, wellness)
        max_price: Maximum price per person in USD
        min_duration: Minimum duration in minutes
        max_duration: Maximum duration in minutes
        limit: Maximum number of results (default: 8)

    Returns:
        Formatted string with activity details
    """
    from backend.booking_system.models import Activity

    try:
        # Build queryset
        queryset = Activity.objects.filter(is_active=True)

        if category:
            queryset = queryset.filter(category=category.lower())

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        if min_duration is not None:
            queryset = queryset.filter(duration_minutes__gte=min_duration)

        if max_duration is not None:
            queryset = queryset.filter(duration_minutes__lte=max_duration)

        activities = list(queryset.order_by("category", "name")[:limit])

        if not activities:
            return "No activities found matching your criteria."

        # Format results
        results = []
        for activity in activities:
            duration_hours = activity.duration_minutes / 60
            duration_str = (
                f"{int(duration_hours)}h"
                if duration_hours >= 1
                else f"{activity.duration_minutes}min"
            )

            results.append(
                f"- **{activity.name}** (ID: {activity.id})\n"
                f"  Category: {activity.get_category_display()}\n"  # type: ignore
                f"  Price: ${activity.price} {activity.currency}\n"
                f"  Duration: {duration_str}\n"
                f"  Location: {activity.location}\n"
                f"  Capacity: {activity.capacity_per_slot} people/slot\n"
                f"  Description: {activity.description[:150]}...\n"
            )

        return "\n".join(results)

    except Exception as e:
        logger.error(f"Error searching activities: {e}", exc_info=True)
        return f"Error searching activities: {str(e)}"


@tool
def get_activity_details(
    activity_id: str,
) -> str:
    """
    Get detailed information about a specific activity.

    Args:
        activity_id: UUID of the activity

    Returns:
        Detailed activity information
    """
    from backend.booking_system.models import Activity

    try:
        activity = Activity.objects.get(id=activity_id, is_active=True)

        duration_hours = activity.duration_minutes / 60
        duration_str = (
            f"{int(duration_hours)} hours"
            if duration_hours >= 1
            else f"{activity.duration_minutes} minutes"
        )

        details = (
            f"**{activity.name}**\n\n"
            f"Category: {activity.get_category_display()}\n"  # type: ignore
            f"Price: ${activity.price} {activity.currency} per person\n"
            f"Duration: {duration_str}\n"
            f"Capacity: {activity.capacity_per_slot} people per time slot\n"
            f"Location: {activity.location}\n\n"
            f"Description:\n{activity.description}\n"
        )

        if activity.requirements:
            details += f"\nRequirements:\n{activity.requirements}\n"

        return details

    except Activity.DoesNotExist:
        return f"Activity with ID {activity_id} not found."
    except Exception as e:
        logger.error(f"Error getting activity details: {e}", exc_info=True)
        return f"Error: {str(e)}"


@tool
def check_time_slots(
    activity_id: str,
    date: Optional[str] = None,
    days_ahead: int = 7,
) -> str:
    """
    Check available time slots for an activity.

    Args:
        activity_id: UUID of the activity
        date: Specific date in YYYY-MM-DD format (optional)
        days_ahead: Number of days to look ahead if no date specified (default: 7)

    Returns:
        Formatted string with available time slots
    """
    from backend.booking_system.models import Activity, TimeSlot
    from django.db import models

    try:
        activity = Activity.objects.get(id=activity_id, is_active=True)

        # Parse date or use date range
        now = timezone.now()
        if date:
            try:
                start_date = datetime.strptime(date, "%Y-%m-%d")
                start_date = timezone.make_aware(start_date)
                end_date = start_date + timedelta(days=1)
            except ValueError:
                return f"Invalid date format '{date}'. Use YYYY-MM-DD (e.g., 2025-01-15)"
        else:
            start_date = now
            end_date = now + timedelta(days=days_ahead)

        # Query available time slots
        time_slots = list(
            TimeSlot.objects.filter(
                activity=activity,
                start_time__gte=start_date,
                start_time__lte=end_date,
                is_available=True,
            )
            .exclude(booked_count__gte=models.F("capacity"))
            .order_by("start_time")[:15]
        )

        if not time_slots:
            date_range = (
                f"on {date}"
                if date
                else f"in the next {days_ahead} days"
            )
            return f"No available time slots for {activity.name} {date_range}."

        # Format results
        results = [f"Available time slots for **{activity.name}**:\n"]

        for slot in time_slots:
            available = slot.capacity - slot.booked_count
            results.append(
                f"- {slot.start_time.strftime('%A, %B %d at %I:%M %p')} "
                f"(ID: {slot.id})\n"
                f"  Available spots: {available}/{slot.capacity}\n"
            )

        return "\n".join(results)

    except Activity.DoesNotExist:
        return f"Activity with ID {activity_id} not found."
    except Exception as e:
        logger.error(f"Error checking time slots: {e}", exc_info=True)
        return f"Error: {str(e)}"


# ===== Booking Tools =====


@tool
def create_pending_booking(
    user_phone: str,
    activity_id: str,
    time_slot_id: str,
    participants: int,
    special_requests: str = "",
) -> str:
    """
    Create a pending booking that requires web app confirmation.

    IMPORTANT: Always confirm all details with the user before creating the booking:
    - Activity name
    - Date and time
    - Number of participants
    - Total price

    Args:
        user_phone: User's phone number in E.164 format (+1234567890)
        activity_id: UUID of the activity
        time_slot_id: UUID of the time slot
        participants: Number of participants (must be >= 1)
        special_requests: Optional special requests from user

    Returns:
        Booking confirmation with details and web confirmation link
    """
    from backend.booking_system.services import BookingService
    from backend.chatbot_core.config import Config

    try:
        # Create booking using existing service
        booking = BookingService.create_booking(
            user_phone=user_phone,
            activity_id=activity_id,
            time_slot_id=time_slot_id,
            participants=participants,
            special_requests=special_requests,
            booking_source="whatsapp",
        )

        # Build confirmation URL
        web_app_url = Config.BOOKING_WEB_APP_URL.rstrip("/")
        confirmation_url = f"{web_app_url}/bookings/{booking.id}"

        # Format response
        response = (
            f"✅ Booking created successfully!\n\n"
            f"**Booking Details:**\n"
            f"Activity: {booking.activity.name}\n"
            f"Date & Time: {booking.time_slot.start_time.strftime('%A, %B %d at %I:%M %p')}\n"
            f"Participants: {booking.participants}\n"
            f"Total Price: ${booking.total_price} {booking.activity.currency}\n"
            f"Status: Pending Confirmation\n"
            f"Booking ID: {str(booking.id)[:8]}\n\n"
            f"⏰ **Action Required:**\n"
            f"Please confirm your booking within 30 minutes:\n"
            f"{confirmation_url}\n\n"
            f"Your spot is temporarily reserved until "
            f"{booking.expires_at.strftime('%I:%M %p')}."
        )

        return response

    except ValueError as e:
        # Business logic errors (no availability, invalid params, etc.)
        return f"Cannot create booking: {str(e)}"
    except Exception as e:
        logger.error(f"Error creating booking: {e}", exc_info=True)
        return f"Error creating booking: {str(e)}"


@tool
def get_user_bookings(
    user_phone: str,
    status: Optional[str] = None,
) -> str:
    """
    Get all bookings for a user.

    Args:
        user_phone: User's phone number
        status: Filter by status (pending, confirmed, cancelled, completed, no_show)

    Returns:
        Formatted list of user's bookings
    """
    from backend.booking_system.services import BookingService

    try:
        bookings = list(BookingService.get_user_bookings(user_phone, status))

        if not bookings:
            status_msg = f" with status '{status}'" if status else ""
            return f"No bookings found{status_msg}."

        # Group by status
        pending = [b for b in bookings if b.status == "pending"]
        confirmed = [b for b in bookings if b.status == "confirmed"]
        past = [b for b in bookings if b.status in ["completed", "cancelled", "no_show"]]

        results = ["**Your Bookings:**\n"]

        # Show pending first (most urgent)
        if pending:
            results.append("⏳ **Pending** (Action Required):")
            for booking in pending[:3]:
                time_left = booking.expires_at - timezone.now()
                minutes_left = max(0, int(time_left.total_seconds() / 60))
                results.append(
                    f"\n- {booking.activity.name}\n"
                    f"  Date: {booking.time_slot.start_time.strftime('%b %d, %I:%M %p')}\n"
                    f"  Participants: {booking.participants}\n"
                    f"  Expires in: {minutes_left} minutes\n"
                    f"  ID: {str(booking.id)[:8]}"
                )
            results.append("")

        # Show confirmed bookings
        if confirmed:
            results.append("✅ **Confirmed:**")
            for booking in confirmed[:5]:
                results.append(
                    f"\n- {booking.activity.name}\n"
                    f"  Date: {booking.time_slot.start_time.strftime('%b %d, %I:%M %p')}\n"
                    f"  Participants: {booking.participants}\n"
                    f"  Total: ${booking.total_price}\n"
                    f"  ID: {str(booking.id)[:8]}"
                )
            results.append("")

        # Show past bookings (limited)
        if past:
            results.append("📋 **Past:**")
            for booking in past[:3]:
                results.append(
                    f"\n- {booking.activity.name}\n"
                    f"  Date: {booking.time_slot.start_time.strftime('%b %d, %I:%M %p')}\n"
                    f"  Status: {booking.status.title()}"
                )

        if len(bookings) > 11:
            results.append(f"\n_...and {len(bookings) - 11} more bookings_")

        return "\n".join(results)

    except Exception as e:
        logger.error(f"Error getting user bookings: {e}", exc_info=True)
        return f"Error retrieving bookings: {str(e)}"


@tool
def cancel_booking(
    booking_id: str,
    user_phone: str,
    reason: str = "",
) -> str:
    """
    Cancel a user's booking.

    IMPORTANT: Confirmed bookings can only be cancelled at least 24 hours before
    the activity start time. Pending bookings can be cancelled anytime.

    Args:
        booking_id: UUID of the booking (or first 8 characters)
        user_phone: User's phone number for authorization
        reason: Optional cancellation reason

    Returns:
        Cancellation confirmation or error message
    """
    from backend.booking_system.models import Booking
    from backend.booking_system.services import BookingService

    try:
        # Handle short booking IDs (first 8 chars)
        if len(booking_id) == 8:
            booking = Booking.objects.filter(
                id__startswith=booking_id, user_phone=user_phone
            ).first()
            if not booking:
                return f"No booking found with ID starting with {booking_id}"
            booking_id = str(booking.id)

        # Cancel booking using service
        booking = BookingService.cancel_booking(
            booking_id=booking_id, user_phone=user_phone, reason=reason
        )

        response = (
            f"✅ **Booking Cancelled**\n\n"
            f"Your booking for **{booking.activity.name}** has been cancelled.\n"
            f"Date: {booking.time_slot.start_time.strftime('%A, %B %d at %I:%M %p')}\n"
            f"Participants: {booking.participants}\n\n"
            f"The time slot is now available for other guests."
        )

        return response

    except ValueError as e:
        # Business logic errors (deadline passed, wrong status, etc.)
        return f"Cannot cancel booking: {str(e)}"
    except Exception as e:
        logger.error(f"Error cancelling booking: {e}", exc_info=True)
        return f"Error cancelling booking: {str(e)}"


# ===== Recommendation Tools =====


@tool
def get_ai_recommendations(
    user_phone: str,
    category: Optional[str] = None,
    count: int = 3,
) -> str:
    """
    Get personalized activity recommendations for a user.

    Uses AI to analyze user preferences and booking history to suggest
    activities that match their interests.

    Args:
        user_phone: User's phone number
        category: Optional category filter
        count: Number of recommendations (1-5, default: 3)

    Returns:
        Formatted recommendations with reasoning
    """
    from backend.booking_system.services import RecommendationService

    try:
        count = max(1, min(5, count))  # Clamp between 1-5

        # Get recommendations from service
        service = RecommendationService()
        recommendations = service.get_recommendations(
            user_phone=user_phone, count=count, category_filter=category
        )

        if not recommendations:
            return "No recommendations available at this time. Try browsing our activities!"

        # Format results
        results = ["🎯 **Personalized Recommendations:**\n"]

        category_icons = {
            "watersports": "🏄",
            "spa": "💆",
            "dining": "🍽️",
            "adventure": "🏔️",
            "wellness": "🧘",
        }

        for idx, rec in enumerate(recommendations, 1):
            activity = rec["activity"]
            reasoning = rec.get("reasoning", "Great choice for you!")
            score = rec.get("score", 50)

            icon = category_icons.get(activity.category, "🎯")

            results.append(
                f"{idx}. {icon} **{activity.name}**\n"
                f"   Price: ${activity.price} {activity.currency}\n"
                f"   Duration: {activity.duration_minutes // 60}h\n"
                f"   Match Score: {score}/100\n"
                f"   💡 {reasoning}\n"
                f"   ID: {activity.id}\n"
            )

        results.append(
            "\nTo book an activity, use the create_pending_booking tool with the activity ID."
        )

        return "\n".join(results)

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        return f"Error generating recommendations: {str(e)}"


# ===== Knowledge Base Tools =====


@tool
def search_resort_knowledge(
    query: str,
) -> str:
    """
    Search the resort knowledge base for information about policies, amenities,
    facilities, and general questions.

    Args:
        query: Search query or question

    Returns:
        Relevant information from the knowledge base
    """
    # TODO: Implement actual knowledge base search
    # For now, return sample FAQs

    query_lower = query.lower()

    # Sample FAQ database (replace with actual knowledge base later)
    faqs = {
        "check-in": {
            "question": "What are the check-in and check-out times?",
            "answer": "Check-in is at 3:00 PM and check-out is at 11:00 AM. Early check-in and late check-out may be available upon request, subject to availability.",
        },
        "wifi": {
            "question": "Is WiFi available?",
            "answer": "Yes, complimentary high-speed WiFi is available throughout the resort, including guest rooms, lobby, pool areas, and restaurants.",
        },
        "parking": {
            "question": "Is parking available?",
            "answer": "Yes, we offer free parking for all guests. Valet parking is also available for $25 per day.",
        },
        "pool": {
            "question": "What are the pool hours?",
            "answer": "Our main pool is open from 6:00 AM to 10:00 PM daily. The adults-only pool is open from 8:00 AM to 8:00 PM.",
        },
        "restaurant": {
            "question": "What dining options are available?",
            "answer": "We have three restaurants: Oceanview (fine dining, 6PM-10PM), Poolside Grill (casual, 11AM-9PM), and Sunrise Café (breakfast, 6AM-11AM). Room service is available 24/7.",
        },
        "cancellation": {
            "question": "What is the cancellation policy?",
            "answer": "For room reservations: Free cancellation up to 48 hours before arrival. For activity bookings: Free cancellation up to 24 hours before the activity start time.",
        },
        "spa": {
            "question": "Does the resort have a spa?",
            "answer": "Yes, our Tranquility Spa offers massages, facials, body treatments, and wellness therapies. Open daily 9AM-8PM. Advance booking recommended.",
        },
        "kids": {
            "question": "Are there activities for children?",
            "answer": "Yes! We have a Kids Club (ages 4-12) with supervised activities, a children's pool, and family-friendly activities throughout the resort.",
        },
    }

    # Simple keyword matching (replace with vector search later)
    matches = []
    for key, faq in faqs.items():
        if any(keyword in query_lower for keyword in key.split("-")):
            matches.append(faq)

    if matches:
        results = ["**Resort Information:**\n"]
        for faq in matches[:3]:  # Top 3 matches
            results.append(f"**Q: {faq['question']}**\n{faq['answer']}\n")
        return "\n".join(results)
    else:
        return (
            "I don't have specific information about that in my knowledge base. "
            "For detailed information, please contact our front desk at +1 (555) 123-4567 "
            "or email info@resort.com."
        )


# Export all tools
ALL_TOOLS = [
    search_activities,
    get_activity_details,
    check_time_slots,
    create_pending_booking,
    get_user_bookings,
    cancel_booking,
    get_ai_recommendations,
    search_resort_knowledge,
]
