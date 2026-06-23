from .checks import HealthCheckService
from .models import SystemError
from .repositories import (
    AlertRepository,
    ErrorRepository,
    MetricsRepository,
)


class ObservabilityService:
    """Business logic for observability and monitoring."""

    # ═══════════════════════════════════════════════════════════════
    #  HEALTH
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def health_all():
        return HealthCheckService.check_all()

    @staticmethod
    def health_db():
        return HealthCheckService.check_database()

    @staticmethod
    def health_redis():
        return HealthCheckService.check_redis()

    @staticmethod
    def health_storage():
        return HealthCheckService.check_storage()

    @staticmethod
    def health_celery():
        return HealthCheckService.check_celery()

    # ═══════════════════════════════════════════════════════════════
    #  METRICS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def metrics():
        return {
            "api": MetricsRepository.api_summary(),
            "realtime": MetricsRepository.realtime_metrics(),
            "system": MetricsRepository.system_metrics(),
            "queue": MetricsRepository.queue_depth(),
        }

    # ═══════════════════════════════════════════════════════════════
    #  ERROR TRACKING
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def log_error(source, error_type, message="", traceback="",
                  endpoint="", user=None, request_id="", correlation_id="",
                  severity=SystemError.Severity.ERROR, metadata=None):
        return ErrorRepository.log_error(
            source=source,
            severity=severity,
            error_type=error_type,
            message=message,
            traceback=traceback,
            endpoint=endpoint,
            user=user,
            request_id=request_id,
            correlation_id=correlation_id,
            metadata=metadata,
        )

    @staticmethod
    def list_errors(source=None, severity=None, page=1):
        return ErrorRepository.search_errors(source, severity, page)

    @staticmethod
    def get_error(error_id):
        return ErrorRepository.get_error(error_id)

    @staticmethod
    def error_summary():
        return ErrorRepository.error_summary()

    # ═══════════════════════════════════════════════════════════════
    #  BACKGROUND JOBS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def job_stats():
        from .models import RequestMetric
        from datetime import timedelta
        from django.utils import timezone

        seven_days = timezone.now() - timedelta(days=7)

        celery_errors = SystemError.objects.filter(
            source=SystemError.Source.CELERY,
            created_at__gte=seven_days,
        )

        return {
            "recent_failures_7d": celery_errors.count(),
            "queue": MetricsRepository.queue_depth(),
            "recent_errors": list(
                celery_errors.order_by("-created_at")[:20]
                .values("id", "error_type", "message", "created_at")
            ),
        }

    # ═══════════════════════════════════════════════════════════════
    #  ALERTS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def list_alerts(status=None, page=1):
        return AlertRepository.list_alerts(status, page)

    @staticmethod
    def acknowledge_alert(alert_id, user):
        return AlertRepository.acknowledge_alert(alert_id, user)

    @staticmethod
    def resolve_alert(alert_id):
        return AlertRepository.resolve_alert(alert_id)

    @staticmethod
    def alert_summary():
        return AlertRepository.alert_summary()
