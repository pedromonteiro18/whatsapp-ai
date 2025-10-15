"""Authentication API views for booking system."""

import logging

from decouple import config
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.whatsapp.client import WhatsAppClient

from .auth import (
    check_rate_limit,
    delete_otp,
    delete_session,
    generate_otp,
    generate_session_token,
    get_phone_from_session,
    store_otp,
    store_session,
    verify_otp,
)
from .serializers import RequestOTPSerializer, VerifyOTPSerializer

logger = logging.getLogger(__name__)


class RequestOTPView(APIView):
    """
    API endpoint to request OTP for phone number verification.

    POST /api/v1/auth/request-otp/
    {
        "phone_number": "+12345678900"
    }
    """

    authentication_classes = []  # No authentication required
    permission_classes = []  # No permissions required

    def post(self, request):
        """Request OTP for phone number."""
        serializer = RequestOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone_number = serializer.validated_data["phone_number"]

        # Check rate limit
        is_allowed, remaining = check_rate_limit(phone_number)

        if not is_allowed:
            return Response(
                {
                    "error": "Rate limit exceeded. Please try again later.",
                    "detail": "Maximum 3 OTP requests per 10 minutes.",
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Generate OTP
        otp = generate_otp()

        # Store OTP in Redis
        if not store_otp(phone_number, otp):
            logger.error("Failed to store OTP for phone %s", phone_number)
            return Response(
                {"error": "Failed to generate OTP. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Send OTP via WhatsApp (or skip in development mode)
        skip_otp_sending = config("SKIP_OTP_SENDING", default=False, cast=bool)

        if skip_otp_sending:
            # Development mode: Log OTP instead of sending
            logger.warning(
                "⚠️  DEVELOPMENT MODE: Skipping WhatsApp OTP sending\n"
                "📱 Phone: %s\n"
                "🔑 OTP: %s\n"
                "⏱️  Valid for 5 minutes",
                phone_number,
                otp,
            )
        else:
            # Production mode: Send via WhatsApp
            try:
                whatsapp_client = WhatsAppClient()
                message = (
                    f"Your verification code is: {otp}\n\n"
                    f"This code will expire in 5 minutes.\n"
                    f"Do not share this code with anyone."
                )
                whatsapp_client.send_message(phone_number, message)
                logger.info("OTP sent successfully to phone %s", phone_number)
            except Exception as e:  # pylint: disable=broad-except
                logger.error("Failed to send OTP via WhatsApp: %s", e)
                return Response(
                    {"error": "Failed to send OTP. Please try again."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "message": "OTP sent successfully",
                "phone_number": phone_number,
                "remaining_requests": remaining,
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """
    API endpoint to verify OTP and create session.

    POST /api/v1/auth/verify-otp/
    {
        "phone_number": "+12345678900",
        "otp": "123456"
    }
    """

    authentication_classes = []  # No authentication required
    permission_classes = []  # No permissions required

    def post(self, request):
        """Verify OTP and create session."""
        serializer = VerifyOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]

        # Verify OTP
        if not verify_otp(phone_number, otp):
            return Response(
                {"error": "Invalid or expired OTP"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Delete OTP after successful verification
        delete_otp(phone_number)

        # Generate session token
        session_token = generate_session_token()

        # Store session in Redis
        if not store_session(session_token, phone_number):
            logger.error("Failed to store session for phone %s", phone_number)
            return Response(
                {"error": "Failed to create session. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        logger.info("Session created successfully for phone %s", phone_number)

        return Response(
            {
                "message": "OTP verified successfully",
                "session_token": session_token,
                "phone_number": phone_number,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    API endpoint to logout and delete session.

    POST /api/v1/auth/logout/
    Headers:
        Authorization: Bearer <session_token>
    """

    def post(self, request):
        """Logout and delete session."""
        # Get session token from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return Response(
                {"error": "Invalid authorization header"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session_token = auth_header.replace("Bearer ", "")

        # Delete session
        delete_session(session_token)

        logger.info("User logged out successfully")

        return Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    API endpoint to get current user information.

    GET /api/v1/auth/me/
    Headers:
        Authorization: Bearer <session_token>
    """

    def get(self, request):
        """Get current user information."""
        # Get session token from Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return Response(
                {"error": "Invalid authorization header"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session_token = auth_header.replace("Bearer ", "")

        # Get phone number from session
        phone_number = get_phone_from_session(session_token)

        if not phone_number:
            return Response(
                {"error": "Invalid or expired session"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "phone_number": phone_number,
                "authenticated": True,
            },
            status=status.HTTP_200_OK,
        )
