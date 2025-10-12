"""URL routing for booking system API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .auth_views import LogoutView, MeView, RequestOTPView, VerifyOTPView
from .views import ActivityViewSet, BookingViewSet

router = DefaultRouter()
router.register(r"activities", ActivityViewSet, basename="activity")
router.register(r"bookings", BookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
    # Authentication endpoints
    path("auth/request-otp/", RequestOTPView.as_view(), name="request-otp"),
    path("auth/verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
]
