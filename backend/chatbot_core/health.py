"""
Health check endpoint for WhatsApp AI Chatbot.

Provides a simple health check endpoint that verifies connectivity
to critical services (database, Redis) for Docker health checks
and monitoring systems.
"""

import logging
from typing import Any, Dict

import redis
from django.db import connection
from django.http import JsonResponse
from django.views import View

from .config import Config

logger = logging.getLogger(__name__)


class HealthCheckView(View):
    """
    Health check endpoint for monitoring and Docker health checks.

    Verifies connectivity to:
    - Database (PostgreSQL)
    - Redis cache

    Returns:
        200 OK: All services are healthy
        503 Service Unavailable: One or more services are down
    """

    def get(self, request: Any) -> JsonResponse:
        """
        Perform health checks on all critical services.

        Args:
            request: HTTP request object

        Returns:
            JsonResponse with health status and details
        """
        health_status: Dict[str, Any] = {
            "status": "healthy",
            "services": {},
        }

        # Check database connectivity
        db_healthy = self._check_database()
        health_status["services"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
        }

        # Check Redis connectivity
        redis_healthy = self._check_redis()
        health_status["services"]["redis"] = {
            "status": "healthy" if redis_healthy else "unhealthy",
        }

        # Determine overall health status
        all_healthy = db_healthy and redis_healthy
        health_status["status"] = "healthy" if all_healthy else "unhealthy"

        # Return appropriate status code
        status_code = 200 if all_healthy else 503

        return JsonResponse(health_status, status=status_code)

    def _check_database(self) -> bool:
        """
        Check database connectivity by executing a simple query.

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            # Execute simple query to verify database connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def _check_redis(self) -> bool:
        """
        Check Redis connectivity by executing a ping command.

        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            # Ping Redis to verify connectivity
            redis_client.ping()
            redis_client.close()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
