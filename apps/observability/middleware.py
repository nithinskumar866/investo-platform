import logging
import time
import uuid

from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

from .models import RequestMetric

logger = logging.getLogger(__name__)

EXCLUDED_PATHS = {"/health/", "/health/db/", "/health/redis/", "/health/storage/", "/health/celery/",
                  "/api/v1/admin/ops/health/", "/api/v1/admin/ops/metrics/"}


class RequestIDMiddleware(MiddlewareMixin):
    """Attaches a unique request_id to every request."""

    def process_request(self, request):
        request.request_id = request.META.get("HTTP_X_REQUEST_ID") or str(uuid.uuid4())
        request.correlation_id = request.META.get("HTTP_X_CORRELATION_ID") or request.request_id

    def process_response(self, request, response):
        if hasattr(request, "request_id"):
            response["X-Request-ID"] = request.request_id
        if hasattr(request, "correlation_id"):
            response["X-Correlation-ID"] = request.correlation_id
        return response


class MetricsMiddleware(MiddlewareMixin):
    """Records API request metrics."""

    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        if not hasattr(request, "_start_time"):
            return response
        if request.path in EXCLUDED_PATHS:
            return response

        duration_ms = int((time.time() - request._start_time) * 1000)
        try:
            RequestMetric.objects.create(
                method=request.method,
                endpoint=request.path[:500],
                status_code=response.status_code,
                duration_ms=duration_ms,
                user=request.user if request.user.is_authenticated else None,
                request_id=getattr(request, "request_id", ""),
                is_error=response.status_code >= 400,
            )
        except Exception:
            logger.warning("Failed to record request metric", exc_info=True)
        return response
