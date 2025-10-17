"""API viewsets for booking system."""

import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .authentication import SessionTokenAuthentication
from .filters import ActivityFilter
from .models import Activity, Booking, TimeSlot
from .permissions import IsAuthenticated, IsOwnerOrReadOnly
from .serializers import (
    ActivitySerializer,
    BookingCreateSerializer,
    BookingSerializer,
    RecommendationSerializer,
    TimeSlotSerializer,
)
from .services import BookingService, RecommendationService

logger = logging.getLogger(__name__)


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Activity model.

    Provides list and retrieve actions with filtering, search, and ordering.
    """

    queryset = Activity.objects.filter(is_active=True).prefetch_related("images")
    serializer_class = ActivitySerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ActivityFilter
    search_fields = ["name", "description", "location"]
    ordering_fields = ["price", "created_at", "name"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):  # pylint: disable=unused-argument
        """
        Get available time slots for an activity.

        Query params:
        - start_date: ISO date string (default: today)
        - end_date: ISO date string (default: 14 days from start_date)
        - participants: Number of participants (default: 1)
        """
        activity = self.get_object()

        # Get query parameters
        from datetime import datetime, timedelta

        from django.utils import timezone

        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        participants = int(request.query_params.get("participants", 1))

        # Parse dates
        if start_date_str:
            # Parse date string and make timezone-aware
            naive_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
            start_date = timezone.make_aware(naive_date) if timezone.is_naive(naive_date) else naive_date
        else:
            start_date = timezone.now()

        if end_date_str:
            # Parse date string and make timezone-aware
            naive_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
            end_date = timezone.make_aware(naive_date) if timezone.is_naive(naive_date) else naive_date
            # Set end date to end of day to include all slots on that date
            end_date = end_date.replace(hour=23, minute=59, second=59)
        else:
            end_date = start_date + timedelta(days=14)

        # Query time slots
        time_slots = TimeSlot.objects.filter(
            activity=activity,
            start_time__gte=start_date,
            start_time__lte=end_date,
            is_available=True,
        ).order_by("start_time")

        # Filter by availability
        available_slots = []
        for slot in time_slots:
            is_available, _ = BookingService.check_availability(
                str(slot.id), participants
            )
            if is_available:
                available_slots.append(slot)

        serializer = TimeSlotSerializer(available_slots, many=True)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Booking model.

    Provides CRUD operations and custom actions for confirm/cancel.
    Requires authentication via session token.
    """

    serializer_class = BookingSerializer
    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filterset_fields = ["status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter bookings by authenticated user's phone number."""
        # Get phone number from authenticated request
        if hasattr(self.request, "auth") and self.request.auth:
            user_phone = self.request.auth
            return Booking.objects.filter(user_phone=user_phone).select_related(
                "activity", "time_slot"
            )

        return Booking.objects.none()

    def get_serializer_class(self):
        """Use BookingCreateSerializer for create action."""
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        """Create a new booking for authenticated user."""
        # Add user_phone to request for serializer context
        if hasattr(request, "auth") and request.auth:
            request.user_phone = (
                request.auth
            )  # pyright: ignore[reportAttributeAccessIssue]

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            booking = serializer.save()
            response_serializer = BookingSerializer(booking)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):  # pylint: disable=unused-argument
        """
        Confirm a pending booking.

        Uses authenticated user's phone number for authorization.
        """
        booking = self.get_object()

        # Get phone number from authenticated request
        if hasattr(request, "auth") and request.auth:
            user_phone = request.auth
        else:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            confirmed_booking = BookingService.confirm_booking(
                str(booking.id), user_phone
            )
            serializer = self.get_serializer(confirmed_booking)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):  # pylint: disable=unused-argument
        """
        Cancel a booking.

        Uses authenticated user's phone number for authorization.
        Optional reason in request data.
        """
        booking = self.get_object()
        reason = request.data.get("reason", "")

        # Get phone number from authenticated request
        if hasattr(request, "auth") and request.auth:
            user_phone = request.auth
        else:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            cancelled_booking = BookingService.cancel_booking(
                str(booking.id), user_phone, reason
            )
            serializer = self.get_serializer(cancelled_booking)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RecommendationViewSet(viewsets.ViewSet):
    """
    ViewSet for AI-powered activity recommendations.

    Provides personalized activity suggestions based on user preferences
    and booking history.
    """

    authentication_classes = [SessionTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get personalized activity recommendations for authenticated user.

        Query Parameters:
        - count (int, optional): Number of recommendations (default: 3, max: 10)
        - category (str, optional): Filter by specific category

        Returns:
            List of recommended activities with AI-generated reasoning
        """
        # Get authenticated user's phone
        user_phone = getattr(request, "user_phone", None)
        if not user_phone:
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Get query parameters
        try:
            count = int(request.query_params.get("count", 3))
            if count < 1 or count > 10:
                return Response(
                    {"error": "Count must be between 1 and 10"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"error": "Invalid count parameter"}, status=status.HTTP_400_BAD_REQUEST
            )

        category_filter = request.query_params.get("category", None)

        # Validate category if provided
        valid_categories = ["watersports", "spa", "dining", "adventure", "wellness"]
        if category_filter and category_filter not in valid_categories:
            return Response(
                {
                    "error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get recommendations from service
            recommendation_service = RecommendationService()
            recommendations = recommendation_service.get_recommendations(
                user_phone, count=count, category_filter=category_filter
            )

            # Serialize and return
            serializer = RecommendationSerializer(recommendations, many=True)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error generating recommendations for {user_phone}: {e}")
            return Response(
                {"error": "Failed to generate recommendations"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
