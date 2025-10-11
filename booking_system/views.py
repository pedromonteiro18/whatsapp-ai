"""API viewsets for booking system."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Activity, Booking, TimeSlot
from .serializers import (
    ActivitySerializer,
    BookingCreateSerializer,
    BookingSerializer,
    TimeSlotSerializer,
)
from .services import BookingService


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
    filterset_fields = ["category"]
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
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
        else:
            start_date = timezone.now()

        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
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
    """

    serializer_class = BookingSerializer
    filterset_fields = ["status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter bookings by user_phone from request."""
        user_phone = self.request.query_params.get("user_phone")
        if not user_phone:
            return Booking.objects.none()

        return Booking.objects.filter(user_phone=user_phone).select_related(
            "activity", "time_slot"
        )

    def get_serializer_class(self):
        """Use BookingCreateSerializer for create action."""
        if self.action == "create":
            return BookingCreateSerializer
        return BookingSerializer

    def create(self, request, *args, **kwargs):
        """Create a new booking."""
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

        Requires user_phone in request data for authorization.
        """
        booking = self.get_object()
        user_phone = request.data.get("user_phone")

        if not user_phone:
            return Response(
                {"error": "user_phone is required"},
                status=status.HTTP_400_BAD_REQUEST,
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

        Requires user_phone in request data for authorization.
        Optional reason in request data.
        """
        booking = self.get_object()
        user_phone = request.data.get("user_phone")
        reason = request.data.get("reason", "")

        if not user_phone:
            return Response(
                {"error": "user_phone is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cancelled_booking = BookingService.cancel_booking(
                str(booking.id), user_phone, reason
            )
            serializer = self.get_serializer(cancelled_booking)
            return Response(serializer.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
