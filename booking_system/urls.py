"""URL routing for booking system API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ActivityViewSet, BookingViewSet

router = DefaultRouter()
router.register(r"activities", ActivityViewSet, basename="activity")
router.register(r"bookings", BookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
]
