"""Custom authentication classes for DRF."""

import logging

from rest_framework import authentication, exceptions

from .auth import get_phone_from_session

logger = logging.getLogger(__name__)


class SessionTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class that validates session tokens from Redis.

    Expects Authorization header: Bearer <session_token>
    Sets request.user_phone with the authenticated phone number.
    """

    def authenticate(self, request):
        """
        Authenticate the request using session token.

        Args:
            request: DRF request object

        Returns:
            Tuple[None, str]: (None, phone_number) if authenticated
            None: If no authentication attempted

        Raises:
            AuthenticationFailed: If authentication fails
        """
        # Get Authorization header
        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            # No authentication attempted
            return None

        # Check Bearer token format
        if not auth_header.startswith("Bearer "):
            raise exceptions.AuthenticationFailed("Invalid authorization header format")

        # Extract token
        session_token = auth_header.replace("Bearer ", "").strip()

        if not session_token:
            raise exceptions.AuthenticationFailed("No session token provided")

        # Get phone number from Redis
        phone_number = get_phone_from_session(session_token)

        if not phone_number:
            raise exceptions.AuthenticationFailed("Invalid or expired session token")

        logger.info("Authenticated request for phone %s", phone_number)

        # Return (user, auth) tuple
        # We don't use Django User model, so return None for user
        # The phone_number is stored in the auth part
        return (None, phone_number)

    def authenticate_header(self, request):
        """
        Return WWW-Authenticate header value for 401 responses.

        Args:
            request: DRF request object

        Returns:
            str: Authentication header value
        """
        return 'Bearer realm="api"'


def get_user_phone(request):
    """
    Helper function to get authenticated user's phone number from request.

    Args:
        request: DRF request object

    Returns:
        str: Phone number if authenticated, None otherwise
    """
    # DRF stores the auth result in request.auth
    if hasattr(request, "auth") and request.auth:
        return request.auth
    return None
