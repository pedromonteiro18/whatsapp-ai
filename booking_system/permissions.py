"""Custom permission classes for booking system."""

import logging

from rest_framework import permissions

logger = logging.getLogger(__name__)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a booking to edit it.

    Read permissions are allowed to any authenticated user.
    Write permissions are only allowed to the owner of the booking.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access the booking.

        Args:
            request: DRF request object
            view: DRF view object
            obj: Booking object

        Returns:
            bool: True if permission granted, False otherwise
        """
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            # Check if user owns this booking
            if hasattr(request, "auth") and request.auth:
                user_phone = request.auth
                return obj.user_phone == user_phone
            return False

        # Write permissions are only allowed to the owner
        if hasattr(request, "auth") and request.auth:
            user_phone = request.auth
            is_owner = obj.user_phone == user_phone

            if not is_owner:
                logger.warning(
                    "Permission denied: User %s attempted to modify "
                    "booking owned by %s",
                    user_phone,
                    obj.user_phone,
                )

            return is_owner

        return False


class IsAuthenticated(permissions.BasePermission):
    """
    Custom permission to only allow authenticated users.

    Checks for valid session token in request.auth.
    """

    def has_permission(self, request, view):
        """
        Check if user is authenticated.

        Args:
            request: DRF request object
            view: DRF view object

        Returns:
            bool: True if authenticated, False otherwise
        """
        # Check if request has auth (phone_number)
        if hasattr(request, "auth") and request.auth:
            return True

        logger.warning("Permission denied: User not authenticated")
        return False
