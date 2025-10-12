"""
WhatsApp message processor for booking intents.

This module handles booking-related conversations in WhatsApp, including:
- Activity browsing and filtering
- Multi-turn booking conversations with state management
- Checking existing bookings
- Cancellation flows
- AI-powered recommendations
"""

import json
import logging
import re
from datetime import timedelta
from typing import Any, Dict, Optional

import redis
from django.db import models
from django.utils import timezone

from .config import Config

logger = logging.getLogger(__name__)


class BookingMessageProcessor:
    """
    Processes WhatsApp messages with booking intents.

    This processor detects booking-related intents and routes them to
    specialized handlers that interact with the booking system.
    Uses Redis for managing multi-turn conversation state.
    """

    # Intent detection patterns (keywords and phrases)
    INTENT_PATTERNS = {
        "browse": [
            r"\b(show|list|browse|see|view|what)\s+(activities|activity)\b",
            r"\bactivities\b",
            r"\bwhat.*available\b",
            r"\bwhat.*can.*do\b",
        ],
        "book": [
            r"\b(book|reserve|schedule|make.*booking|make.*reservation)\b",
            r"\bi.*book\b",
            r"\breserve\b",
        ],
        "check": [
            r"\b(check|view|show|list|see).*bookings?\b",
            r"\bmy.*bookings?\b",
            r"\breservations?\b",
            r"\bwhat.*booked\b",
        ],
        "cancel": [
            r"\bcancel.*booking\b",
            r"\bcancel.*reservation\b",
        ],
        "recommend": [
            r"\brecommend\b",
            r"\bsuggestions?\b",
            r"\bwhat.*should.*do\b",
            r"\bhelp.*choose\b",
        ],
    }

    # Flat list of keywords for fuzzy matching (typo handling)
    INTENT_KEYWORDS = {
        "browse": ["show", "list", "browse", "see", "view", "activities", "activity"],
        "book": ["book", "reserve", "schedule", "booking", "reservation"],
        "check": ["check", "view", "show", "bookings", "reservations", "booked"],
        "cancel": ["cancel", "cancellation"],
        "recommend": ["recommend", "suggestions", "suggest"],
    }

    # Emoji icons for categories
    CATEGORY_ICONS = {
        "watersports": "🏄",
        "spa": "💆",
        "dining": "🍽️",
        "adventure": "🏔️",
        "wellness": "🧘",
    }

    def __init__(
        self, whatsapp_client: Any, redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize the booking message processor.

        Args:
            whatsapp_client: WhatsApp client for sending messages
            redis_client: Redis client for storing conversation state (optional)
        """
        self.whatsapp_client = whatsapp_client
        self.redis_client = redis_client or redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
        )

    def detect_intent(self, message: str) -> Optional[str]:
        """
        Detect the booking intent from a user message.

        Uses regex patterns for exact matching (fast path), then falls back
        to fuzzy string matching if no exact match is found (typo handling).

        Args:
            message: The user's message text

        Returns:
            Intent name (browse, book, check, cancel, recommend) or None
        """
        message_lower = message.lower()

        # Try exact regex matching first (fast path: ~0.1ms)
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    logger.info(
                        f"Regex matched intent '{intent}' from message: {message[:50]}"
                    )
                    return intent

        # Fallback to fuzzy matching for typos (slower but still fast: ~0.5ms)
        fuzzy_intent = self._fuzzy_match_intent(message)
        if fuzzy_intent:
            return fuzzy_intent

        return None

    def _fuzzy_match_intent(
        self, message: str, threshold: float = 0.75
    ) -> Optional[str]:
        """
        Detect intent using fuzzy string matching to handle typos.

        Uses Python's difflib.SequenceMatcher to calculate string similarity,
        allowing the system to match misspellings like "bbok" → "book".

        Args:
            message: User message text
            threshold: Similarity threshold (0.0-1.0, default 0.75 = 75%)

        Returns:
            Intent name or None if no fuzzy match found
        """
        from difflib import SequenceMatcher

        words = message.lower().split()

        # Check each word against intent keywords
        for word in words:
            # Skip very short words (pronouns, articles, etc.)
            if len(word) < 3:
                continue

            # Check against all intent keywords
            for intent, keywords in self.INTENT_KEYWORDS.items():
                for keyword in keywords:
                    # Calculate similarity ratio (0.0 to 1.0)
                    similarity = SequenceMatcher(None, word, keyword).ratio()

                    if similarity >= threshold:
                        logger.info(
                            f"Fuzzy matched '{word}' to '{keyword}' "
                            f"(intent: {intent}, similarity: {similarity:.2%})"
                        )
                        return intent

        return None

    def process(self, user_phone: str, message: str) -> bool:
        """
        Process a booking-related message.

        Detects intent and routes to appropriate handler. Also handles
        continuation of multi-turn conversations.

        Args:
            user_phone: User's phone number
            message: The user's message text

        Returns:
            True if message was handled, False if not a booking intent
        """
        # Check if there's an ongoing conversation state
        state = self._get_conversation_state(user_phone)
        if state and state.get("intent"):
            # Continue ongoing conversation
            logger.info(
                f"Continuing {state['intent']} conversation for {user_phone}, "
                f"step {state.get('step', 0)}"
            )
            return self._continue_conversation(user_phone, message, state)

        # Detect new intent
        intent = self.detect_intent(message)

        if not intent:
            return False

        logger.info(f"Processing new booking intent '{intent}' for {user_phone}")

        try:
            if intent == "browse":
                return self.handle_browse(user_phone, message)
            elif intent == "book":
                return self.handle_booking(user_phone, message)
            elif intent == "check":
                return self.handle_check_booking(user_phone, message)
            elif intent == "cancel":
                return self.handle_cancel_booking(user_phone, message)
            elif intent == "recommend":
                return self.handle_recommendations(user_phone, message)
            else:
                return False

        except Exception as e:
            logger.error(
                f"Error processing booking intent '{intent}' for {user_phone}: {e}",
                exc_info=True,
            )
            self.whatsapp_client.send_message(
                user_phone,
                "Sorry, there was an error processing your request. Please try again.",
            )
            # Clear any stale state
            self._clear_conversation_state(user_phone)
            return True

    def _continue_conversation(
        self, user_phone: str, message: str, state: Dict[str, Any]
    ) -> bool:
        """
        Continue an ongoing multi-turn conversation.

        Args:
            user_phone: User's phone number
            message: The user's message text
            state: Current conversation state

        Returns:
            True if handled successfully
        """
        intent = state["intent"]

        if intent == "book":
            return self._continue_booking_flow(user_phone, message, state)
        elif intent == "cancel":
            return self._continue_cancel_flow(user_phone, message, state)
        else:
            # Unknown conversation type, clear state
            self._clear_conversation_state(user_phone)
            return False

    def handle_browse(self, user_phone: str, message: str) -> bool:
        """
        Handle activity browsing requests.

        Queries activities and formats them for WhatsApp display with
        category filtering if specified in the message.

        Args:
            user_phone: User's phone number
            message: The user's message text

        Returns:
            True if handled successfully
        """
        # Import here to avoid circular imports
        from booking_system.models import Activity

        try:
            # Extract category filter from message
            category_filter = self._extract_category(message)

            # Query activities
            queryset = Activity.objects.filter(is_active=True)
            if category_filter:
                queryset = queryset.filter(category=category_filter)

            activities = list(queryset.order_by("category", "name")[:8])

            if not activities:
                self.whatsapp_client.send_message(
                    user_phone,
                    "No activities available at the moment. Please check back later!",
                )
                return True

            # Format response
            if category_filter:
                response = f"*{category_filter.title()} Activities*\n\n"
            else:
                response = "*Available Activities*\n\n"

            for idx, activity in enumerate(activities, 1):
                icon = self.CATEGORY_ICONS.get(activity.category, "🎯")
                duration_hours = activity.duration_minutes / 60
                duration_str = (
                    f"{int(duration_hours)}h"
                    if duration_hours >= 1
                    else f"{activity.duration_minutes}min"
                )

                response += (
                    f"{idx}. {icon} *{activity.name}*\n"
                    f"   💵 ${activity.price} | ⏱️ {duration_str}\n"
                    f"   📍 {activity.location}\n"
                    f"   _{activity.description[:80]}..._\n\n"
                )

            response += "\nTo book an activity, reply with:\n'Book [activity name]'"

            self.whatsapp_client.send_message(user_phone, response)
            return True

        except Exception as e:
            logger.error(f"Error handling browse for {user_phone}: {e}", exc_info=True)
            self.whatsapp_client.send_message(
                user_phone,
                "Sorry, I couldn't retrieve activities. Please try again later.",
            )
            return True

    def handle_booking(self, user_phone: str, message: str) -> bool:
        """
        Handle booking creation with multi-turn conversation.

        Initiates a booking flow that collects activity, time slot, and
        participant count through multiple messages.

        Args:
            user_phone: User's phone number
            message: The user's message text

        Returns:
            True if handled successfully
        """
        # Import here to avoid circular imports
        from booking_system.models import Activity

        try:
            # Try to extract activity name from message
            activity = self._extract_activity_from_message(message)

            if activity:
                # Start booking flow at step 2 (already have activity)
                state = {
                    "intent": "book",
                    "step": 2,
                    "activity_id": str(activity.id),
                    "time_slot_id": None,
                    "participants": None,
                }
                self._set_conversation_state(user_phone, state)
                return self._show_time_slots(user_phone, activity)
            else:
                # Start booking flow at step 1 (need to choose activity)
                state = {
                    "intent": "book",
                    "step": 1,
                    "activity_id": None,
                    "time_slot_id": None,
                    "participants": None,
                }
                self._set_conversation_state(user_phone, state)

                # Show available activities
                activities = list(
                    Activity.objects.filter(is_active=True).order_by("name")[:8]
                )

                if not activities:
                    self.whatsapp_client.send_message(
                        user_phone,
                        "No activities available for booking. Please check back later!",
                    )
                    self._clear_conversation_state(user_phone)
                    return True

                response = "*Choose an activity to book:*\n\n"
                for idx, act in enumerate(activities, 1):
                    icon = self.CATEGORY_ICONS.get(act.category, "🎯")
                    response += f"{idx}. {icon} {act.name} (${act.price})\n"

                response += "\nReply with the activity number (1-8)."

                self.whatsapp_client.send_message(user_phone, response)
                return True

        except Exception as e:
            logger.error(f"Error starting booking for {user_phone}: {e}", exc_info=True)
            self.whatsapp_client.send_message(
                user_phone,
                "Sorry, I couldn't start the booking. Please try again.",
            )
            self._clear_conversation_state(user_phone)
            return True

    def _continue_booking_flow(
        self, user_phone: str, message: str, state: Dict[str, Any]
    ) -> bool:
        """
        Continue the multi-turn booking conversation.

        Args:
            user_phone: User's phone number
            message: The user's message text
            state: Current conversation state

        Returns:
            True if handled successfully
        """
        from booking_system.models import Activity, TimeSlot
        from booking_system.services import BookingService

        step = state.get("step", 1)

        try:
            if step == 1:
                # User choosing activity
                try:
                    activity_num = int(message.strip())
                    activities = list(
                        Activity.objects.filter(is_active=True).order_by("name")[:8]
                    )
                    if 1 <= activity_num <= len(activities):
                        activity = activities[activity_num - 1]
                        state["activity_id"] = str(activity.id)
                        state["step"] = 2
                        self._set_conversation_state(user_phone, state)
                        return self._show_time_slots(user_phone, activity)
                    else:
                        self.whatsapp_client.send_message(
                            user_phone,
                            f"Please reply with a number between 1 and {len(activities)}.",
                        )
                        return True
                except ValueError:
                    self.whatsapp_client.send_message(
                        user_phone,
                        "Please reply with the activity number (e.g., '1', '2', '3').",
                    )
                    return True

            elif step == 2:
                # User choosing time slot
                try:
                    slot_num = int(message.strip())
                    activity = Activity.objects.get(id=state["activity_id"])
                    time_slots = self._get_available_time_slots(activity)

                    if 1 <= slot_num <= len(time_slots):
                        time_slot = time_slots[slot_num - 1]
                        state["time_slot_id"] = str(time_slot.id)
                        state["step"] = 3
                        self._set_conversation_state(user_phone, state)

                        # Ask for participants
                        max_capacity = time_slot.capacity - time_slot.booked_count
                        response = (
                            f"Great! You've selected:\n"
                            f"*{activity.name}*\n"
                            f"📅 {time_slot.start_time.strftime('%A, %B %d at %I:%M %p')}\n\n"
                            f"How many participants? (Max: {max_capacity})"
                        )
                        self.whatsapp_client.send_message(user_phone, response)
                        return True
                    else:
                        self.whatsapp_client.send_message(
                            user_phone,
                            f"Please reply with a number between 1 and {len(time_slots)}.",
                        )
                        return True
                except ValueError:
                    self.whatsapp_client.send_message(
                        user_phone, "Please reply with the time slot number."
                    )
                    return True

            elif step == 3:
                # User providing participant count
                try:
                    participants = int(message.strip())
                    time_slot = TimeSlot.objects.get(id=state["time_slot_id"])
                    available = time_slot.capacity - time_slot.booked_count

                    if participants < 1:
                        self.whatsapp_client.send_message(
                            user_phone, "Please enter at least 1 participant."
                        )
                        return True
                    elif participants > available:
                        msg = (
                            f"Sorry, only {available} spots available. "
                            "Please enter a lower number."
                        )
                        self.whatsapp_client.send_message(user_phone, msg)
                        return True

                    # Create the booking
                    booking = BookingService.create_booking(
                        user_phone=user_phone,
                        activity_id=state["activity_id"],
                        time_slot_id=state["time_slot_id"],
                        participants=participants,
                        booking_source="whatsapp",
                    )

                    # Clear conversation state
                    self._clear_conversation_state(user_phone)

                    # Send confirmation
                    activity = booking.activity
                    time_slot = booking.time_slot
                    formatted_time = time_slot.start_time.strftime(
                        "%A, %B %d at %I:%M %p"
                    )
                    response = (
                        f"✅ *Booking Created!*\n\n"
                        f"*{activity.name}*\n"
                        f"📅 {formatted_time}\n"
                        f"👥 {participants} participant(s)\n"
                        f"💵 Total: ${booking.total_price}\n"
                        f"📍 {activity.location}\n\n"
                        f"⚠️ *Important*: Please confirm within 30 minutes "
                        f"or your booking will expire.\n\n"
                        f"Booking ID: `{str(booking.id)[:8]}`\n"
                        f"Status: {booking.status.upper()}"
                    )
                    self.whatsapp_client.send_message(user_phone, response)
                    return True

                except ValueError:
                    self.whatsapp_client.send_message(
                        user_phone, "Please reply with a number for participants."
                    )
                    return True

        except Exception as e:
            logger.error(
                f"Error in booking flow step {step} for {user_phone}: {e}",
                exc_info=True,
            )
            self.whatsapp_client.send_message(
                user_phone, "Sorry, something went wrong. Let's start over."
            )
            self._clear_conversation_state(user_phone)
            return True

        return True

    def handle_check_booking(self, user_phone: str, message: str) -> bool:
        """
        Handle checking user's bookings.

        Retrieves and displays user's bookings grouped by status.

        Args:
            user_phone: User's phone number
            message: The user's message text

        Returns:
            True if handled successfully
        """
        from booking_system.services import BookingService

        try:
            # Get all user bookings
            bookings = list(BookingService.get_user_bookings(user_phone))

            if not bookings:
                msg = (
                    "You don't have any bookings yet. "
                    "Browse activities to make your first booking!"
                )
                self.whatsapp_client.send_message(user_phone, msg)
                return True

            # Group by status
            pending = [b for b in bookings if b.status == "pending"]
            confirmed = [b for b in bookings if b.status == "confirmed"]
            past = [b for b in bookings if b.status in ["completed", "cancelled"]]

            response = "*Your Bookings*\n\n"

            # Show pending bookings first (most urgent)
            if pending:
                response += "⏳ *Pending* (Action Required)\n"
                for booking in pending[:3]:
                    time_left = booking.expires_at - timezone.now()
                    minutes_left = int(time_left.total_seconds() / 60)
                    response += (
                        f"\n• {booking.activity.name}\n"
                        f"  📅 {booking.time_slot.start_time.strftime('%b %d, %I:%M %p')}\n"
                        f"  ⏰ Expires in {minutes_left} minutes\n"
                        f"  ID: `{str(booking.id)[:8]}`\n"
                    )
                response += "\n"

            # Show confirmed bookings
            if confirmed:
                response += "✅ *Confirmed*\n"
                for booking in confirmed[:3]:
                    response += (
                        f"\n• {booking.activity.name}\n"
                        f"  📅 {booking.time_slot.start_time.strftime('%b %d, %I:%M %p')}\n"
                        f"  👥 {booking.participants} participant(s)\n"
                        f"  ID: `{str(booking.id)[:8]}`\n"
                    )
                response += "\n"

            # Show past bookings (limited)
            if past:
                response += "📋 *Past*\n"
                for booking in past[:2]:
                    response += (
                        f"\n• {booking.activity.name}\n"
                        f"  📅 {booking.time_slot.start_time.strftime('%b %d, %I:%M %p')}\n"
                        f"  Status: {booking.status.title()}\n"
                    )

            if len(bookings) > 8:
                response += f"\n_...and {len(bookings) - 8} more_"

            self.whatsapp_client.send_message(user_phone, response)
            return True

        except Exception as e:
            logger.error(
                f"Error checking bookings for {user_phone}: {e}", exc_info=True
            )
            self.whatsapp_client.send_message(
                user_phone,
                "Sorry, I couldn't retrieve your bookings. Please try again later.",
            )
            return True

    def handle_cancel_booking(self, user_phone: str, message: str) -> bool:
        """
        Handle booking cancellation requests.

        Initiates a two-step cancellation flow.

        Args:
            user_phone: User's phone number
            message: The user's message text

        Returns:
            True if handled successfully
        """
        from booking_system.services import BookingService

        try:
            # Get user's confirmed bookings
            bookings = list(
                BookingService.get_user_bookings(user_phone, status="confirmed")
            )

            if not bookings:
                self.whatsapp_client.send_message(
                    user_phone, "You don't have any active bookings to cancel."
                )
                return True

            # Start cancellation flow
            state = {
                "intent": "cancel",
                "step": 1,
                "bookings": [str(b.id) for b in bookings[:5]],  # Store IDs
            }
            self._set_conversation_state(user_phone, state)

            # Format bookings list
            response = "*Select a booking to cancel:*\n\n"
            for idx, booking in enumerate(bookings[:5], 1):
                response += (
                    f"{idx}. {booking.activity.name}\n"
                    f"   📅 {booking.time_slot.start_time.strftime('%b %d, %I:%M %p')}\n"
                    f"   👥 {booking.participants} participant(s)\n\n"
                )

            response += "Reply with the booking number (1-5) to cancel."

            self.whatsapp_client.send_message(user_phone, response)
            return True

        except Exception as e:
            logger.error(
                f"Error starting cancellation for {user_phone}: {e}", exc_info=True
            )
            self.whatsapp_client.send_message(
                user_phone,
                "Sorry, I couldn't retrieve your bookings. Please try again.",
            )
            return True

    def _continue_cancel_flow(
        self, user_phone: str, message: str, state: Dict[str, Any]
    ) -> bool:
        """
        Continue the booking cancellation flow.

        Args:
            user_phone: User's phone number
            message: The user's message text
            state: Current conversation state

        Returns:
            True if handled successfully
        """
        from booking_system.services import BookingService

        try:
            booking_num = int(message.strip())
            bookings = state.get("bookings", [])

            if 1 <= booking_num <= len(bookings):
                booking_id = bookings[booking_num - 1]

                try:
                    booking = BookingService.cancel_booking(
                        booking_id=booking_id,
                        user_phone=user_phone,
                        reason="User requested cancellation via WhatsApp",
                    )

                    # Clear conversation state
                    self._clear_conversation_state(user_phone)

                    response = (
                        f"✅ *Booking Cancelled*\n\n"
                        f"Your booking for *{booking.activity.name}* has been cancelled.\n"
                        f"📅 {booking.time_slot.start_time.strftime('%b %d, %I:%M %p')}\n\n"
                        f"Feel free to book another activity anytime!"
                    )
                    self.whatsapp_client.send_message(user_phone, response)
                    return True

                except ValueError as e:
                    # Cancellation failed (deadline passed, etc.)
                    self._clear_conversation_state(user_phone)
                    self.whatsapp_client.send_message(
                        user_phone,
                        f"❌ Unable to cancel booking: {str(e)}",
                    )
                    return True
            else:
                self.whatsapp_client.send_message(
                    user_phone,
                    f"Please reply with a number between 1 and {len(bookings)}.",
                )
                return True

        except ValueError:
            self.whatsapp_client.send_message(
                user_phone, "Please reply with the booking number to cancel."
            )
            return True
        except Exception as e:
            logger.error(f"Error in cancel flow for {user_phone}: {e}", exc_info=True)
            self._clear_conversation_state(user_phone)
            self.whatsapp_client.send_message(
                user_phone, "Sorry, something went wrong. Please try again."
            )
            return True

    def handle_recommendations(self, user_phone: str, message: str) -> bool:
        """
        Handle AI-powered recommendation requests.

        Calls the RecommendationService to get personalized suggestions.

        Args:
            user_phone: User's phone number
            message: The user's message text

        Returns:
            True if handled successfully
        """
        from booking_system.services import RecommendationService

        try:
            # Get AI recommendations
            recommendation_service = RecommendationService()
            recommendations = recommendation_service.get_recommendations(
                user_phone=user_phone, count=3
            )

            if not recommendations:
                self.whatsapp_client.send_message(
                    user_phone,
                    "No recommendations available at the moment. Try browsing our activities!",
                )
                return True

            # Format recommendations
            response = "🎯 *Personalized Recommendations*\n\n"

            for idx, rec in enumerate(recommendations, 1):
                activity = rec["activity"]
                reasoning = rec.get("reasoning", "Great choice for you!")
                icon = self.CATEGORY_ICONS.get(activity.category, "🎯")

                response += (
                    f"{idx}. {icon} *{activity.name}*\n"
                    f"   💵 ${activity.price}\n"
                    f"   💡 {reasoning}\n\n"
                )

            response += "To book an activity, reply with:\n'Book [activity name]'"

            self.whatsapp_client.send_message(user_phone, response)
            return True

        except Exception as e:
            logger.error(
                f"Error getting recommendations for {user_phone}: {e}", exc_info=True
            )
            self.whatsapp_client.send_message(
                user_phone,
                "Sorry, I couldn't generate recommendations. Try browsing activities instead!",
            )
            return True

    # Helper methods

    def _extract_category(self, message: str) -> Optional[str]:
        """Extract category from message if mentioned."""
        message_lower = message.lower()
        categories = ["watersports", "spa", "dining", "adventure", "wellness"]

        for category in categories:
            if category in message_lower:
                return category
        return None

    def _extract_activity_from_message(self, message: str):
        """
        Extract activity from message using fuzzy matching to handle typos.

        Tries exact substring matching first (fast path), then falls back to
        fuzzy matching to handle typos like "scba" → "scuba".

        Args:
            message: User message text

        Returns:
            Activity instance or None
        """
        from difflib import get_close_matches

        from booking_system.models import Activity

        # Remove common intent words
        words = message.lower()
        for word in ["book", "reserve", "schedule", "i", "want", "to", "the", "a"]:
            words = words.replace(word, "")
        words = words.strip()

        if not words:
            return None

        # Get all active activities
        activities = list(Activity.objects.filter(is_active=True))

        # Try exact substring match first (fast path)
        for activity in activities:
            activity_name_lower = activity.name.lower()
            if activity_name_lower in words or words in activity_name_lower:
                logger.info(f"Exact substring match: '{words}' → '{activity.name}'")
                return activity

        # Fallback to fuzzy matching for typos
        # Build map of searchable strings to activities
        activity_map = {act.name.lower(): act for act in activities}

        # Also include individual words from activity names (for partial matches)
        word_map = {}
        for act in activities:
            for word in act.name.lower().split():
                if len(word) >= 4:  # Skip short words like "and", "the", "spa"
                    word_map[word] = act

        # Combine both dictionaries for comprehensive matching
        all_match_targets = {**activity_map, **word_map}

        # Find close matches (60% similarity threshold)
        matches = get_close_matches(words, all_match_targets.keys(), n=1, cutoff=0.6)

        if matches:
            matched_key = matches[0]
            activity = all_match_targets[matched_key]
            logger.info(
                f"Fuzzy matched: '{words}' → '{matched_key}' → '{activity.name}'"
            )
            return activity

        logger.info(f"No activity match found for: '{words}'")
        return None

    def _show_time_slots(self, user_phone: str, activity) -> bool:
        """Show available time slots for an activity."""
        time_slots = self._get_available_time_slots(activity)

        if not time_slots:
            self.whatsapp_client.send_message(
                user_phone,
                f"Sorry, no time slots available for *{activity.name}* in the next 7 days.",
            )
            self._clear_conversation_state(user_phone)
            return True

        response = f"*Available times for {activity.name}*\n\n"
        for idx, slot in enumerate(time_slots, 1):
            available = slot.capacity - slot.booked_count
            response += (
                f"{idx}. {slot.start_time.strftime('%A, %B %d')}\n"
                f"   ⏰ {slot.start_time.strftime('%I:%M %p')}\n"
                f"   👥 {available} spots available\n\n"
            )

        response += "Reply with the time slot number (1-10)."

        self.whatsapp_client.send_message(user_phone, response)
        return True

    def _get_available_time_slots(self, activity):
        """Get available time slots for the next 7 days."""
        from booking_system.models import TimeSlot

        now = timezone.now()
        end_date = now + timedelta(days=7)

        return list(
            TimeSlot.objects.filter(
                activity=activity,
                start_time__gte=now,
                start_time__lte=end_date,
                is_available=True,
            )
            .exclude(booked_count__gte=models.F("capacity"))
            .order_by("start_time")[:10]
        )

    def _get_conversation_state(self, user_phone: str) -> Dict[str, Any]:
        """Get conversation state from Redis."""
        key = f"booking_flow:{user_phone}"
        try:
            data = self.redis_client.get(key)
            if data:
                state: Dict[str, Any] = json.loads(data)
                return state
        except Exception as e:
            logger.error(f"Error getting conversation state: {e}")
        return {}

    def _set_conversation_state(
        self, user_phone: str, state: Dict[str, Any], ttl_seconds: int = 600
    ) -> None:
        """Store conversation state in Redis with 10-minute TTL."""
        key = f"booking_flow:{user_phone}"
        try:
            self.redis_client.setex(key, ttl_seconds, json.dumps(state))
        except Exception as e:
            logger.error(f"Error setting conversation state: {e}")

    def _clear_conversation_state(self, user_phone: str) -> None:
        """Clear conversation state from Redis."""
        key = f"booking_flow:{user_phone}"
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error clearing conversation state: {e}")
