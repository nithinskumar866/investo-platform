import logging

from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.http import JsonResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["System"],
    summary="Health check endpoint",
    description="Returns service health status including database and cache connectivity.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
    }

    all_healthy = all(checks.values())
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JsonResponse(
        {
            "status": "healthy" if all_healthy else "degraded",
            "version": getattr(settings, "APP_VERSION", "2.0.0"),
            "checks": {name: "pass" if ok else "fail" for name, ok in checks.items()},
        },
        status=status_code,
    )


def _check_database():
    try:
        connection.ensure_connection()
        return True
    except Exception as e:
        logger.error(f"Health check: database check failed: {e}")
        return False


def _check_cache():
    try:
        cache.set("__health", "ok", timeout=5)
        result = cache.get("__health")
        cache.delete("__health")
        return result == "ok"
    except Exception as e:
        logger.error(f"Health check: cache check failed: {e}")
        return False
