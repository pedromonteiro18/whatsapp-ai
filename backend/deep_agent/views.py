"""
Views for deep-agent testing and parallel webhook processing.

Provides endpoints for:
- Testing the deep-agent with direct API calls
- Parallel WhatsApp webhook processing (proof-of-concept)
"""

import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from .agent import process_message as process_with_deep_agent

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def test_deep_agent(request: Request) -> Response:
    """
    Test endpoint for the deep-agent (no WhatsApp client required).

    POST /api/deep-agent/test/
    Body: {
        "user_phone": "+1234567890",
        "message": "I want to book kayaking"
    }

    Returns:
        {
            "success": true,
            "response": "agent response text",
            "metadata": {...}
        }
    """
    try:
        # Extract parameters
        user_phone = request.data.get("user_phone")
        message = request.data.get("message")

        # Validate inputs
        if not user_phone or not message:
            return Response(
                {
                    "success": False,
                    "error": "Both 'user_phone' and 'message' are required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Test request from {user_phone}: {message[:50]}...")

        # Process with deep-agent
        result = process_with_deep_agent(user_phone, message)

        # Return result
        if result["success"]:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"Error in test_deep_agent: {e}", exc_info=True)
        return Response(
            {"success": False, "error": str(e), "response": "", "metadata": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_deep_agent_webhook(request):
    """
    Parallel WhatsApp webhook endpoint using deep-agent processing.

    This is an alternative to the existing webhook that uses deep-agent
    instead of the traditional MessageProcessor.

    POST /api/whatsapp/deep-agent/webhook/

    Expected Twilio webhook payload:
        - From: whatsapp:+1234567890
        - Body: message content

    For production use, this should:
    1. Validate Twilio signature
    2. Queue to Celery for async processing
    3. Return 200 immediately

    For PoC, we process synchronously for simplicity.
    """
    try:
        # Extract WhatsApp message details from Twilio webhook
        user_phone = request.POST.get("From", "")
        message_content = request.POST.get("Body", "")

        # Remove 'whatsapp:' prefix if present
        if user_phone.startswith("whatsapp:"):
            user_phone = user_phone.replace("whatsapp:", "")

        # Validate inputs
        if not user_phone or not message_content:
            logger.warning("Missing required fields in webhook request")
            return JsonResponse(
                {"status": "error", "message": "Missing required fields"},
                status=400,
            )

        logger.info(
            f"Deep-agent webhook received from {user_phone}: {message_content[:50]}..."
        )

        # For PoC: Process synchronously
        # For production: Queue to Celery task and return 200 immediately
        result = process_with_deep_agent(user_phone, message_content)

        if result["success"]:
            # Send response via WhatsApp (would need WhatsAppClient integration)
            # For now, just log it
            logger.info(
                f"Deep-agent response for {user_phone}: {result['response'][:100]}..."
            )

            # TODO: Integrate with WhatsAppClient to send the response
            # from backend.whatsapp.client import WhatsAppClient
            # whatsapp_client = WhatsAppClient()
            # whatsapp_client.send_message(f"whatsapp:{user_phone}", result["response"])

            return JsonResponse(
                {"status": "success", "message": "Message processed"}, status=200
            )
        else:
            logger.error(
                f"Deep-agent processing failed for {user_phone}: {result['error']}"
            )

            # Send error message to user
            # For now, just return error response
            return JsonResponse(
                {"status": "error", "message": result["error"]}, status=500
            )

    except Exception as e:
        logger.error(f"Error in whatsapp_deep_agent_webhook: {e}", exc_info=True)
        return JsonResponse(
            {"status": "error", "message": "Internal server error"}, status=500
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def deep_agent_health(request: Request) -> Response:
    """
    Health check endpoint for deep-agent.

    GET /api/deep-agent/health/

    Returns:
        {
            "status": "healthy",
            "agent_initialized": true,
            "model": "openai/gpt-4",
            "tools_count": 8,
            "subagents_count": 3
        }
    """
    try:
        from .agent import get_agent
        from .subagents import get_subagent_configs

        agent = get_agent()
        subagent_configs = get_subagent_configs()

        return Response(
            {
                "status": "healthy",
                "agent_initialized": agent is not None,
                "model": agent.model if agent else None,
                "tools_count": len(agent.agent.tools) if agent and agent.agent else 0,  # type: ignore
                "subagents_count": len(subagent_configs),
                "subagent_names": [cfg["name"] for cfg in subagent_configs],
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return Response(
            {
                "status": "unhealthy",
                "error": str(e),
                "agent_initialized": False,
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
