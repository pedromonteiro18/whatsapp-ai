"""
Specialized subagent configurations for the deep-agent hospitality concierge.

Defines three specialized subagents:
- booking_specialist: Handles complete booking workflows
- activity_guide: Provides recommendations and activity research
- knowledge_assistant: Answers resort information questions
"""

from typing import List

from .prompts import (
    ACTIVITY_GUIDE_PROMPT,
    BOOKING_SPECIALIST_PROMPT,
    KNOWLEDGE_ASSISTANT_PROMPT,
)
from .tools import (
    cancel_booking,
    check_time_slots,
    create_pending_booking,
    get_activity_details,
    get_ai_recommendations,
    get_user_bookings,
    search_activities,
    search_resort_knowledge,
)


def get_subagent_configs() -> List[dict]:
    """
    Get configurations for all specialized subagents.

    Returns:
        List of subagent configuration dictionaries for SubAgentMiddleware
    """
    return [
        # Booking Specialist Subagent
        {
            "name": "booking_specialist",
            "description": (
                "Specialized agent for handling complete booking workflows. "
                "Use this agent when guests want to book, modify, or cancel activities. "
                "It guides them through: searching activities → checking time slots → "
                "confirming details → creating the booking. "
                "Handles multi-step conversations and ensures all requirements are gathered."
            ),
            "system_prompt": BOOKING_SPECIALIST_PROMPT,
            "tools": [
                search_activities,
                get_activity_details,
                check_time_slots,
                create_pending_booking,
                get_user_bookings,
                cancel_booking,
            ],
            # Use the same model as main agent (will inherit from parent)
            # "model": "claude-sonnet-4-5-20250929",
        },
        # Activity Guide Subagent
        {
            "name": "activity_guide",
            "description": (
                "Specialized agent for activity recommendations and research. "
                "Use this agent when guests need help discovering activities, "
                "want personalized suggestions based on their interests, or need "
                "detailed information about multiple activities to make a decision. "
                "It learns preferences and provides thoughtful, personalized recommendations."
            ),
            "system_prompt": ACTIVITY_GUIDE_PROMPT,
            "tools": [
                search_activities,
                get_activity_details,
                get_ai_recommendations,
                get_user_bookings,  # To understand past preferences
            ],
            # Could use a different model optimized for recommendations
            # "model": "gpt-4o",
        },
        # Knowledge Assistant Subagent
        {
            "name": "knowledge_assistant",
            "description": (
                "Specialized agent for resort information and policies. "
                "Use this agent when guests ask about: check-in/check-out times, "
                "WiFi and amenities, dining options, pool hours, spa services, "
                "cancellation policies, or any general resort information. "
                "Provides accurate, helpful answers from the resort knowledge base."
            ),
            "system_prompt": KNOWLEDGE_ASSISTANT_PROMPT,
            "tools": [
                search_resort_knowledge,
            ],
            # Knowledge queries can use a faster/cheaper model
            # "model": "gpt-4o-mini",
        },
    ]


# Export for convenient importing
__all__ = ["get_subagent_configs"]
