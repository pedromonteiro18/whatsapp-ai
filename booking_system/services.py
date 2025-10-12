"""Business logic for booking system."""

# pylint: disable=no-member
# Django models have 'objects' and 'DoesNotExist' added dynamically

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from ai_integration.adapters.base import AIError, BaseAIAdapter
from ai_integration.factory import AIAdapterFactory

from .models import Activity, Booking, TimeSlot, UserPreference
from .notifications import NotificationService

logger = logging.getLogger(__name__)


class BookingService:
    """Business logic for booking operations."""

    @staticmethod
    def check_availability(
        time_slot_id: str, participants: int = 1
    ) -> Tuple[bool, int]:
        """
        Check if a time slot has availability for the requested number of participants.

        Args:
            time_slot_id: UUID of the time slot
            participants: Number of participants (default: 1)

        Returns:
            Tuple of (is_available: bool, available_capacity: int)

        Raises:
            TimeSlot.DoesNotExist: If time slot not found
        """
        try:
            time_slot = TimeSlot.objects.select_related("activity").get(id=time_slot_id)
        except TimeSlot.DoesNotExist:
            return False, 0

        # Check if time slot is in the past
        if time_slot.start_time < timezone.now():
            return False, 0

        # Check if activity is active
        if not time_slot.activity.is_active:
            return False, 0

        # Check if time slot is marked as available
        if not time_slot.is_available:
            return False, 0

        # Calculate available capacity
        available_capacity = time_slot.capacity - time_slot.booked_count

        # Check if enough capacity for participants
        is_available = available_capacity >= participants

        return is_available, available_capacity

    @staticmethod
    @transaction.atomic
    def create_booking(  # pylint: disable=too-many-arguments
        user_phone: str,
        activity_id: str,
        time_slot_id: str,
        participants: int = 1,
        special_requests: str = "",
        booking_source: str = "whatsapp",
    ) -> Booking:
        """
        Create a new booking with atomic transaction.

        Args:
            user_phone: User's phone number
            activity_id: UUID of the activity
            time_slot_id: UUID of the time slot
            participants: Number of participants (default: 1)
            special_requests: Optional special requests
            booking_source: Source of booking ('whatsapp' or 'web')

        Returns:
            Created Booking instance

        Raises:
            Activity.DoesNotExist: If activity not found
            TimeSlot.DoesNotExist: If time slot not found
            ValueError: If time slot is not available or validation fails
        """
        # Get activity and time slot with select_for_update to prevent race conditions
        try:
            activity = Activity.objects.get(id=activity_id)
        except Activity.DoesNotExist as exc:
            raise ValueError(f"Activity with id {activity_id} not found") from exc

        try:
            time_slot = TimeSlot.objects.select_for_update().get(id=time_slot_id)
        except TimeSlot.DoesNotExist as exc:
            raise ValueError(f"Time slot with id {time_slot_id} not found") from exc

        # Validate activity is active
        if not activity.is_active:
            raise ValueError("Activity is not currently active")

        # Validate time slot is in the future
        if time_slot.start_time < timezone.now():
            raise ValueError("Cannot book time slots in the past")

        # Validate time slot belongs to the activity
        if time_slot.activity_id != activity.id:
            raise ValueError("Time slot does not belong to the specified activity")

        # Check availability
        is_available, available_capacity = BookingService.check_availability(
            time_slot_id, participants
        )

        if not is_available:
            raise ValueError(
                f"Time slot not available. Only {available_capacity} spots remaining"
            )

        # Validate participants
        if participants < 1:
            raise ValueError("Number of participants must be at least 1")

        # Calculate total price
        total_price = activity.price * Decimal(participants)

        # Set expiration time (30 minutes from now for pending bookings)
        expires_at = timezone.now() + timedelta(minutes=30)

        # Create booking
        booking = Booking.objects.create(
            user_phone=user_phone,
            activity=activity,
            time_slot=time_slot,
            status="pending",
            participants=participants,
            special_requests=special_requests,
            total_price=total_price,
            expires_at=expires_at,
            booking_source=booking_source,
        )

        # Increment booked count
        time_slot.booked_count += participants
        time_slot.save(update_fields=["booked_count"])

        # Send notification (non-blocking - log failures but don't raise)
        try:
            NotificationService.send_booking_created(booking)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to send booking created notification for booking %s: %s",
                booking.id,
                str(e),
            )

        return booking

    @staticmethod
    @transaction.atomic
    def confirm_booking(booking_id: str, user_phone: str) -> Booking:
        """
        Confirm a pending booking.

        Args:
            booking_id: UUID of the booking
            user_phone: User's phone number for authorization

        Returns:
            Updated Booking instance

        Raises:
            Booking.DoesNotExist: If booking not found
            ValueError: If booking cannot be confirmed (wrong user, wrong status, etc.)
        """
        try:
            booking = Booking.objects.select_for_update().get(id=booking_id)
        except Booking.DoesNotExist as exc:
            raise ValueError(f"Booking with id {booking_id} not found") from exc

        # Validate booking belongs to user
        if booking.user_phone != user_phone:
            raise ValueError("You are not authorized to confirm this booking")

        # Validate booking is in pending status
        if booking.status != "pending":
            raise ValueError(
                f"Booking cannot be confirmed. Current status: {booking.status}"
            )

        # Check if booking has expired
        if booking.expires_at < timezone.now():
            raise ValueError("Booking has expired and cannot be confirmed")

        # Update booking status
        booking.status = "confirmed"
        booking.confirmed_at = timezone.now()
        booking.save(update_fields=["status", "confirmed_at"])

        # Send notification (non-blocking - log failures but don't raise)
        try:
            NotificationService.send_booking_confirmed(booking)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to send booking confirmed notification for booking %s: %s",
                booking.id,
                str(e),
            )

        return booking

    @staticmethod
    @transaction.atomic
    def cancel_booking(booking_id: str, user_phone: str, reason: str = "") -> Booking:
        """
        Cancel a booking and release the time slot capacity.

        Args:
            booking_id: UUID of the booking
            user_phone: User's phone number for authorization
            reason: Optional cancellation reason

        Returns:
            Updated Booking instance

        Raises:
            Booking.DoesNotExist: If booking not found
            ValueError: If booking cannot be cancelled
        """
        try:
            booking = (
                Booking.objects.select_for_update()
                .select_related("time_slot")
                .get(id=booking_id)
            )
        except Booking.DoesNotExist as exc:
            raise ValueError(f"Booking with id {booking_id} not found") from exc

        # Validate booking belongs to user
        if booking.user_phone != user_phone:
            raise ValueError("You are not authorized to cancel this booking")

        # Validate booking can be cancelled
        if booking.status in ["cancelled", "completed"]:
            raise ValueError(
                f"Booking cannot be cancelled. Current status: {booking.status}"
            )

        # Check cancellation deadline (24 hours before activity)
        cancellation_deadline = booking.time_slot.start_time - timedelta(hours=24)
        if timezone.now() > cancellation_deadline:
            raise ValueError(
                "Cancellation deadline has passed. "
                "Bookings must be cancelled at least 24 hours before the activity."
            )

        # Get time slot with lock
        time_slot = TimeSlot.objects.select_for_update().get(id=booking.time_slot_id)

        # Update booking status
        booking.status = "cancelled"
        booking.cancelled_at = timezone.now()
        if reason:
            booking.metadata["cancellation_reason"] = reason
        booking.save(update_fields=["status", "cancelled_at", "metadata"])

        # Decrement booked count
        time_slot.booked_count -= booking.participants
        time_slot.save(update_fields=["booked_count"])

        # Send notification (non-blocking - log failures but don't raise)
        try:
            NotificationService.send_booking_cancelled(booking, reason)
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Failed to send booking cancelled notification for booking %s: %s",
                booking.id,
                str(e),
            )

        return booking

    @staticmethod
    def get_user_bookings(
        user_phone: str, status: Optional[str] = None
    ) -> QuerySet[Booking]:
        """
        Get all bookings for a user, optionally filtered by status.

        Args:
            user_phone: User's phone number
            status: Optional status filter ('pending', 'confirmed', 'cancelled', etc.)

        Returns:
            QuerySet of Booking instances ordered by created_at descending
        """
        queryset = Booking.objects.select_related("activity", "time_slot").filter(
            user_phone=user_phone
        )

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-created_at")


class RecommendationService:
    """Business logic for AI-powered activity recommendations."""

    def __init__(self, ai_adapter: Optional[BaseAIAdapter] = None):
        """
        Initialize the recommendation service.

        Args:
            ai_adapter: AI adapter instance (creates default if None)
        """
        self.ai_adapter = ai_adapter or AIAdapterFactory.create_adapter()

    def get_recommendations(
        self, user_phone: str, count: int = 3, category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered activity recommendations for a user.

        Args:
            user_phone: User's phone number
            count: Number of recommendations to return (default: 3)
            category_filter: Optional category to filter by

        Returns:
            List of recommendation dictionaries with:
                - activity: Activity instance
                - reasoning: AI-generated explanation for recommendation
                - score: Confidence score (0-100)

        Raises:
            ValueError: If count is invalid
        """
        if count < 1 or count > 10:
            raise ValueError("Count must be between 1 and 10")

        try:
            # Load user preferences (if any)
            user_prefs = self._load_user_preferences(user_phone)

            # Get user's past confirmed bookings
            past_bookings = self._get_past_bookings(user_phone)

            # Query available activities
            activities = self._query_activities(category_filter)

            if not activities:
                logger.warning("No activities available for recommendations")
                return []

            # Build AI prompt for recommendations
            prompt = self._build_recommendation_prompt(
                user_prefs, past_bookings, activities, count
            )

            # Call AI to generate recommendations
            ai_response = self._call_ai_for_recommendations(prompt)

            # Parse AI response into structured recommendations
            recommendations = self._parse_recommendations(ai_response, activities)

            return recommendations[:count]

        except AIError as e:
            logger.error(f"AI error generating recommendations: {e}")
            # Fallback to simple popularity-based recommendations
            return self._fallback_recommendations(activities, count)
        except Exception as e:
            logger.error(f"Unexpected error generating recommendations: {e}")
            return []

    def _load_user_preferences(self, user_phone: str) -> Optional[UserPreference]:
        """Load user preferences from database."""
        try:
            return UserPreference.objects.get(user_phone=user_phone)
        except UserPreference.DoesNotExist:
            return None

    def _get_past_bookings(self, user_phone: str) -> QuerySet[Booking]:
        """Get user's past confirmed bookings."""
        return Booking.objects.select_related("activity").filter(
            user_phone=user_phone, status__in=["confirmed", "completed"]
        )

    def _query_activities(
        self, category_filter: Optional[str] = None
    ) -> QuerySet[Activity]:
        """Query available activities, optionally filtered by category."""
        queryset = Activity.objects.filter(is_active=True)

        if category_filter:
            queryset = queryset.filter(category=category_filter)

        return queryset.order_by("-created_at")

    def _build_recommendation_prompt(
        self,
        user_prefs: Optional[UserPreference],
        past_bookings: QuerySet[Booking],
        activities: QuerySet[Activity],
        count: int,
    ) -> List[Dict[str, str]]:
        """
        Build the AI prompt for generating recommendations.

        Uses hybrid approach: structured format with clear delimiters
        and natural language reasoning for best parsing reliability.
        """
        # System message: Define AI's role
        system_msg = (
            "You are an expert resort activity recommender. Your goal is to suggest "
            "activities that match the guest's preferences and provide compelling reasons "
            "for each recommendation. Be enthusiastic but concise."
        )

        # Build user message with context
        user_msg_parts = []

        # Add user preferences if available
        if user_prefs:
            user_msg_parts.append("**Guest Preferences:**")
            if user_prefs.preferred_categories:
                categories = ", ".join(user_prefs.preferred_categories)
                user_msg_parts.append(f"- Preferred categories: {categories}")
            if user_prefs.preferred_times:
                times = ", ".join(user_prefs.preferred_times)
                user_msg_parts.append(f"- Preferred times: {times}")
            if user_prefs.budget_range:
                budget = user_prefs.budget_range
                if "min" in budget and "max" in budget:
                    user_msg_parts.append(
                        f"- Budget range: ${budget['min']} - ${budget['max']}"
                    )
            if user_prefs.interests:
                user_msg_parts.append(f"- Interests: {user_prefs.interests}")
            user_msg_parts.append("")
        else:
            user_msg_parts.append(
                "**Guest Preferences:** None specified (recommend popular activities)\n"
            )

        # Add past bookings to avoid repetition
        if past_bookings.exists():
            user_msg_parts.append("**Previously Booked Activities:**")
            for booking in past_bookings[:5]:  # Limit to last 5
                user_msg_parts.append(f"- {booking.activity.name}")
            user_msg_parts.append(
                "Note: Try to suggest different experiences unless highly relevant.\n"
            )

        # Add available activities
        user_msg_parts.append("**Available Activities:**")
        for activity in activities:
            duration_hours = activity.duration_minutes / 60
            user_msg_parts.append(
                f"\n- **{activity.name}**\n"
                f"  Category: {activity.get_category_display()}\n"  # type: ignore[attr-defined]
                f"  Price: ${activity.price} {activity.currency}\n"
                f"  Duration: {duration_hours:.1f} hours\n"
                f"  Description: {activity.description[:150]}..."
            )

        # Add instructions
        user_msg_parts.append(
            f"\n**Task:** Recommend exactly {count} activities from the list above. "
            "For each recommendation, use this exact format:\n"
            "\n---\n"
            "ACTIVITY: [exact activity name from list]\n"
            "SCORE: [0-100]\n"
            "REASONING: [2-3 sentences explaining why this is a great match]\n"
            "---\n"
            "\nIMPORTANT: Use the EXACT activity names from the list above."
        )

        user_msg = "\n".join(user_msg_parts)

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

    def _call_ai_for_recommendations(
        self, messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Call the AI adapter with the recommendation prompt.

        Args:
            messages: List of message dictionaries for AI

        Returns:
            AI response dictionary with 'content' and 'metadata'

        Raises:
            AIError: If AI call fails
        """
        try:
            response = self.ai_adapter.send_message(messages)
            return response
        except AIError as e:
            logger.error(f"AI adapter error: {e}")
            raise

    def _parse_recommendations(
        self, ai_response: Dict[str, Any], activities: QuerySet[Activity]
    ) -> List[Dict[str, Any]]:
        """
        Parse AI response into structured recommendations.

        Expects format with --- delimiters:
        ---
        ACTIVITY: Activity Name
        SCORE: 85
        REASONING: Because...
        ---
        """
        recommendations = []
        content = ai_response.get("content", "")

        # Create lookup dict for fast activity matching
        activity_dict = {
            activity.name.strip().lower(): activity for activity in activities
        }

        # Split by delimiter
        sections = content.split("---")

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extract fields using simple parsing
            activity_name = None
            score = 50  # Default score
            reasoning = ""

            lines = section.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()

                if line.upper().startswith("ACTIVITY:"):
                    activity_name = line.split(":", 1)[1].strip()
                elif line.upper().startswith("SCORE:"):
                    try:
                        score = int(line.split(":", 1)[1].strip())
                        # Clamp score between 0-100
                        score = max(0, min(100, score))
                    except (ValueError, IndexError):
                        score = 50
                elif line.upper().startswith("REASONING:"):
                    # Reasoning might span multiple lines
                    reasoning_parts = [line.split(":", 1)[1].strip()]
                    # Collect remaining lines as part of reasoning
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()
                        if next_line and not any(
                            next_line.upper().startswith(prefix)
                            for prefix in ["ACTIVITY:", "SCORE:", "REASONING:"]
                        ):
                            reasoning_parts.append(next_line)
                        else:
                            break
                    reasoning = " ".join(reasoning_parts)
                    break

            # Match activity name to database
            if activity_name:
                # Try exact match first (case-insensitive)
                activity = activity_dict.get(activity_name.strip().lower())

                # If no exact match, try fuzzy matching
                if not activity:
                    for db_name, db_activity in activity_dict.items():
                        name_lower = activity_name.strip().lower()
                        if name_lower in db_name or db_name in name_lower:
                            activity = db_activity
                            logger.info(
                                f"Fuzzy matched '{activity_name}' to "
                                f"'{db_activity.name}'"
                            )
                            break

                if activity:
                    recommendations.append(
                        {
                            "activity": activity,
                            "reasoning": reasoning or "Recommended for you",
                            "score": score,
                        }
                    )
                else:
                    logger.warning(
                        f"Could not match AI recommended activity: {activity_name}"
                    )

        return recommendations

    def update_preferences_from_conversation(
        self, user_phone: str, conversation_messages: List[str]
    ) -> Optional[UserPreference]:
        """
        Extract and update user preferences from conversation messages.

        Args:
            user_phone: User's phone number
            conversation_messages: List of recent conversation messages

        Returns:
            Updated UserPreference instance, or None if no preferences extracted

        Raises:
            AIError: If AI extraction fails
        """
        if not conversation_messages:
            logger.info(f"No conversation messages provided for {user_phone}")
            return None

        try:
            # Build prompt for preference extraction
            prompt = self._build_preference_extraction_prompt(conversation_messages)

            # Call AI to extract preferences
            ai_response = self._call_ai_for_recommendations(prompt)

            # Parse extracted preferences
            extracted_prefs = self._parse_extracted_preferences(ai_response)

            if not extracted_prefs:
                logger.info(
                    f"No preferences extracted from conversation for {user_phone}"
                )
                return None

            # Update or create user preference
            user_pref, created = UserPreference.objects.update_or_create(
                user_phone=user_phone, defaults=extracted_prefs
            )

            action = "Created" if created else "Updated"
            logger.info(f"{action} preferences for {user_phone}: {extracted_prefs}")

            return user_pref

        except AIError as e:
            logger.error(f"AI error extracting preferences: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating preferences: {e}")
            return None

    def _build_preference_extraction_prompt(
        self, conversation_messages: List[str]
    ) -> List[Dict[str, str]]:
        """
        Build AI prompt for extracting preferences from conversation.

        Args:
            conversation_messages: List of conversation messages

        Returns:
            List of message dictionaries for AI
        """
        system_msg = (
            "You are an expert at understanding guest preferences from conversations. "
            "Extract activity preferences, interests, budget constraints, and time preferences. "
            "If no clear preferences are mentioned, indicate that."
        )

        # Format conversation
        conversation_text = "\n".join(
            [f"- {msg}" for msg in conversation_messages[-10:]]  # Last 10 messages
        )

        # Build user message
        user_msg = (
            f"**Conversation:**\n{conversation_text}\n\n"
            "**Task:** Extract guest preferences from the conversation above. "
            "Use this exact format:\n\n"
            "CATEGORIES: [comma-separated list from: watersports, spa, dining, "
            "adventure, wellness]\n"
            "TIMES: [comma-separated list from: morning, afternoon, evening]\n"
            "BUDGET_MIN: [number or 'none']\n"
            "BUDGET_MAX: [number or 'none']\n"
            "INTERESTS: [brief description of interests or 'none']\n\n"
            "IMPORTANT: If a preference is not mentioned, write 'none'. "
            "Only extract explicitly mentioned or clearly implied preferences."
        )

        return [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

    def _parse_extracted_preferences(
        self, ai_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse AI response containing extracted preferences.

        Args:
            ai_response: AI response dictionary

        Returns:
            Dictionary with preference fields for UserPreference model
        """
        content = ai_response.get("content", "")
        preferences: Dict[str, Any] = {}

        lines = content.split("\n")
        for line in lines:
            line = line.strip()

            if line.upper().startswith("CATEGORIES:"):
                value = line.split(":", 1)[1].strip().lower()
                if value and value != "none":
                    # Parse comma-separated categories
                    categories = [cat.strip() for cat in value.split(",")]
                    # Validate categories
                    valid_categories = [
                        "watersports",
                        "spa",
                        "dining",
                        "adventure",
                        "wellness",
                    ]
                    categories = [cat for cat in categories if cat in valid_categories]
                    if categories:
                        preferences["preferred_categories"] = categories

            elif line.upper().startswith("TIMES:"):
                value = line.split(":", 1)[1].strip().lower()
                if value and value != "none":
                    # Parse comma-separated times
                    times = [t.strip() for t in value.split(",")]
                    # Validate times
                    valid_times = ["morning", "afternoon", "evening"]
                    times = [t for t in times if t in valid_times]
                    if times:
                        preferences["preferred_times"] = times

            elif line.upper().startswith("BUDGET_MIN:"):
                value = line.split(":", 1)[1].strip().lower()
                if value and value != "none":
                    try:
                        budget_min = float(value)
                        if "budget_range" not in preferences:
                            preferences["budget_range"] = {}
                        preferences["budget_range"]["min"] = budget_min
                    except ValueError:
                        pass

            elif line.upper().startswith("BUDGET_MAX:"):
                value = line.split(":", 1)[1].strip().lower()
                if value and value != "none":
                    try:
                        budget_max = float(value)
                        if "budget_range" not in preferences:
                            preferences["budget_range"] = {}
                        preferences["budget_range"]["max"] = budget_max
                    except ValueError:
                        pass

            elif line.upper().startswith("INTERESTS:"):
                value = line.split(":", 1)[1].strip()
                if value and value.lower() != "none":
                    preferences["interests"] = value

        return preferences

    def _fallback_recommendations(
        self, activities: QuerySet[Activity], count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate simple fallback recommendations when AI fails.

        Returns most recently created activities as a fallback.
        """
        recommendations = []
        for activity in activities[:count]:
            recommendations.append(
                {
                    "activity": activity,
                    "reasoning": "Popular choice at our resort",
                    "score": 50,  # Neutral score for fallback
                }
            )
        return recommendations
