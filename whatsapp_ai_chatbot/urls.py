"""
URL configuration for whatsapp_ai_chatbot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from chatbot_core.health import HealthCheckView
from whatsapp.views import WhatsAppWebhookView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health check endpoint
    path("health/", HealthCheckView.as_view(), name="health-check"),
    # WhatsApp webhook endpoint
    path(
        "api/whatsapp/webhook/", WhatsAppWebhookView.as_view(), name="whatsapp-webhook"
    ),
    # Booking system API endpoints
    path("api/v1/", include("booking_system.urls")),
]
