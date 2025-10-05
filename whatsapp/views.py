"""
WhatsApp webhook views for receiving and processing incoming messages.

This module provides API endpoints for Twilio WhatsApp webhook integration.
"""

import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from whatsapp.utils import verify_webhook_signature

logger = logging.getLogger(__name__)


class WhatsAppWebhookView(APIView):
    """
    API view for handling WhatsApp webhook requests from Twilio.

    Supports:
    - GET: Webhook verification (Twilio requirement)
    - POST: Incoming message processing
    """

    # Disable CSRF for webhook endpoint (Twilio can't provide CSRF token)
    # Security is handled via signature verification
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        """
        Handle webhook verification requests from Twilio.

        Twilio sends a GET request to verify the webhook URL is accessible.

        Returns:
            Response: 200 OK with any query parameters echoed back
        """
        logger.info("Webhook verification request received")

        # Echo back any query parameters (Twilio verification pattern)
        return Response(
            {"status": "ok", "params": dict(request.query_params)},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """
        Handle incoming WhatsApp messages from Twilio.

        Validates the webhook signature, extracts message data, and queues
        the message for asynchronous processing via Celery.

        Returns:
            Response: 200 OK immediately to prevent Twilio timeout
        """
        logger.info("Incoming WhatsApp webhook request")

        try:
            # Get the full URL for signature verification
            url = request.build_absolute_uri()

            # Get the signature from headers
            signature = request.headers.get("X-Twilio-Signature", "")

            # Get POST data as dictionary
            post_data = dict(request.POST.items())

            # Verify webhook signature
            if not verify_webhook_signature(url, post_data, signature):
                logger.warning(
                    "Webhook signature verification failed for request from %s",
                    request.META.get("REMOTE_ADDR"),
                )
                return Response(
                    {"error": "Invalid signature"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Extract message data from Twilio payload
            sender = request.POST.get("From", "")
            message_body = request.POST.get("Body", "")
            message_sid = request.POST.get("MessageSid", "")

            # Validate required fields
            if not sender or not message_body:
                logger.warning(
                    "Missing required fields in webhook payload. From: %s, Body: %s",
                    sender,
                    message_body,
                )
                return Response(
                    {"error": "Missing required fields"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            logger.info(
                "Received message from %s (SID: %s): %s",
                sender,
                message_sid,
                message_body[:50],  # Log first 50 chars
            )

            # Queue message for processing via Celery
            # Import here to avoid circular imports
            from chatbot_core.tasks import process_whatsapp_message

            # Queue the task asynchronously
            process_whatsapp_message.delay(sender, message_body, message_sid)

            logger.info("Message queued for processing: %s", message_sid)

            # Return 200 OK immediately to prevent Twilio timeout
            return Response(
                {"status": "queued", "message_sid": message_sid},
                status=status.HTTP_200_OK,
            )

        except Exception as e:  # noqa: BLE001
            # Log error but still return 200 to prevent Twilio retries
            logger.error("Error processing webhook: %s", e, exc_info=True)

            # Return 200 OK to prevent Twilio from retrying
            # (we don't want to process the same message multiple times)
            return Response(
                {"status": "error", "message": "Internal error"},
                status=status.HTTP_200_OK,
            )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook_function_view(request):
    """
    Function-based view alternative for WhatsApp webhook.

    This is a simpler alternative to the class-based view above.
    Can be used if DRF is not preferred for this endpoint.

    Args:
        request: Django HttpRequest object

    Returns:
        HttpResponse: 200 OK response
    """
    if request.method == "GET":
        # Webhook verification
        logger.info("Webhook verification request received")
        return HttpResponse("OK", status=200)

    elif request.method == "POST":
        # Process incoming message
        logger.info("Incoming WhatsApp webhook request")

        try:
            # Get the full URL for signature verification
            url = request.build_absolute_uri()

            # Get the signature from headers
            signature = request.META.get("HTTP_X_TWILIO_SIGNATURE", "")

            # Get POST data as dictionary
            post_data = dict(request.POST.items())

            # Verify webhook signature
            if not verify_webhook_signature(url, post_data, signature):
                logger.warning(
                    "Webhook signature verification failed for request from %s",
                    request.META.get("REMOTE_ADDR"),
                )
                return HttpResponse("Forbidden", status=403)

            # Extract message data
            sender = request.POST.get("From", "")
            message_body = request.POST.get("Body", "")
            message_sid = request.POST.get("MessageSid", "")

            # Validate required fields
            if not sender or not message_body:
                logger.warning(
                    "Missing required fields in webhook payload. From: %s, Body: %s",
                    sender,
                    message_body,
                )
                return HttpResponse("Bad Request", status=400)

            logger.info(
                "Received message from %s (SID: %s): %s",
                sender,
                message_sid,
                message_body[:50],
            )

            # Queue message for processing
            from chatbot_core.tasks import process_whatsapp_message

            process_whatsapp_message.delay(sender, message_body, message_sid)

            logger.info("Message queued for processing: %s", message_sid)

            return HttpResponse("OK", status=200)

        except Exception as e:  # noqa: BLE001
            logger.error("Error processing webhook: %s", e, exc_info=True)
            return HttpResponse("OK", status=200)

    return HttpResponse("Method Not Allowed", status=405)
