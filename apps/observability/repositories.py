from datetime import timedelta

from django.db.models import Avg, Count, Max, Q, Sum
from django.utils import timezone

from .models import AlertEvent, AlertRule, RequestMetric, SystemError


class ErrorRepository:
    """Data access for system error tracking."""

    @staticmethod
    def log_error(source, severity, error_type, message="", traceback="",
                  endpoint="", user=None, request_id="", correlation_id="",
                  metadata=None):
        return SystemError.objects.create(
            source=source,
            severity=severity,
            error_type=error_type[:255],
            message=message,
            traceback=traceback,
            endpoint=endpoint[:500],
            user=user,
            request_id=request_id,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )

    @staticmethod
    def search_errors(source=None, severity=None, page=1, page_size=50):
        q = {}
        if source:
            q["source"] = source
        if severity:
            q["severity"] = severity
        offset = (page - 1) * page_size
        return SystemError.objects.filter(**q).order_by("-created_at")[offset:offset + page_size]

    @staticmethod
    def get_error(error_id):
        return SystemError.objects.filter(id=error_id).first()

    @staticmethod
    def recent_errors(hours=24):
        cutoff = timezone.now() - timedelta(hours=hours)
        return SystemError.objects.filter(created_at__gte=cutoff).order_by("-created_at")[:100]

    @staticmethod
    def error_summary(hours=24):
        cutoff = timezone.now() - timedelta(hours=hours)
        base = SystemError.objects.filter(created_at__gte=cutoff)
        return {
            "total": base.count(),
            "by_source": list(base.values("source").annotate(count=Count("id")).order_by("-count")),
            "by_severity": list(base.values("severity").annotate(count=Count("id")).order_by("-count")),
        }


class MetricsRepository:
    """Data access for system metrics."""

    @staticmethod
    def api_summary(hours=24):
        cutoff = timezone.now() - timedelta(hours=hours)
        base = RequestMetric.objects.filter(created_at__gte=cutoff)
        total = base.count()
        if total == 0:
            return {"total_requests": 0, "avg_duration_ms": 0, "error_rate": 0,
                    "status_codes": {}, "top_endpoints": []}

        return {
            "total_requests": total,
            "avg_duration_ms": round(base.aggregate(avg=Avg("duration_ms"))["avg"] or 0, 2),
            "max_duration_ms": base.aggregate(m=Max("duration_ms"))["m"] or 0,
            "error_rate": round((base.filter(is_error=True).count() / total) * 100, 2),
            "status_codes": {
                str(k): v for k, v in
                base.values("status_code").annotate(count=Count("id")).order_by("status_code")
                .values_list("status_code", "count")
            },
            "top_endpoints": list(
                base.values("endpoint")
                .annotate(count=Count("id"), avg_duration=Avg("duration_ms"))
                .order_by("-count")[:10]
            ),
        }

    @staticmethod
    def realtime_metrics():
        now = timezone.now()
        five_min_ago = now - timedelta(minutes=5)
        base = RequestMetric.objects.filter(created_at__gte=five_min_ago)
        total = base.count()
        errors = base.filter(is_error=True).count()

        return {
            "requests_5min": total,
            "errors_5min": errors,
            "avg_duration_5min": round(base.aggregate(avg=Avg("duration_ms"))["avg"] or 0, 2),
            "error_rate_5min": round((errors / total * 100), 2) if total else 0,
        }

    @staticmethod
    def system_metrics():
        from django.contrib.auth import get_user_model
        User = get_user_model()

        now = timezone.now()
        day_ago = now - timedelta(days=1)
        hour_ago = now - timedelta(hours=1)

        return {
            "active_users_24h": User.objects.filter(last_login__gte=day_ago).count(),
            "active_users_1h": User.objects.filter(last_login__gte=hour_ago).count(),
            "total_users": User.objects.filter(is_active=True).count(),
            "recent_errors_1h": SystemError.objects.filter(created_at__gte=hour_ago).count(),
            "ws_connections": 0,
        }

    @staticmethod
    def queue_depth():
        try:
            from config.celery import app as celery_app
            inspect = celery_app.control.inspect()
            active = inspect.active() or {}
            reserved = inspect.reserved() or {}
            scheduled = inspect.scheduled() or {}
            total_active = sum(len(v) for v in active.values()) if active else 0
            total_reserved = sum(len(v) for v in reserved.values()) if reserved else 0
            total_scheduled = sum(len(v) for v in scheduled.values()) if scheduled else 0
            return {
                "active": total_active,
                "reserved": total_reserved,
                "scheduled": total_scheduled,
                "total": total_active + total_reserved + total_scheduled,
            }
        except Exception:
            return {"active": 0, "reserved": 0, "scheduled": 0, "total": 0, "error": "Cannot reach broker"}


class AlertRepository:
    """Data access for alert rules and events."""

    @staticmethod
    def get_active_rules():
        return AlertRule.objects.filter(is_active=True)

    @staticmethod
    def trigger_alert(rule, metric_value, message=""):
        cooldown = rule.cooldown_minutes
        cutoff = timezone.now() - timedelta(minutes=cooldown)
        recent = AlertEvent.objects.filter(rule=rule, created_at__gte=cutoff).exists()
        if recent:
            return None

        return AlertEvent.objects.create(
            rule=rule,
            status=AlertEvent.Status.TRIGGERED,
            metric_value=metric_value,
            message=message,
        )

    @staticmethod
    def acknowledge_alert(alert_id, user):
        alert = AlertEvent.objects.filter(id=alert_id).first()
        if not alert:
            return None
        alert.status = AlertEvent.Status.ACKNOWLEDGED
        alert.acknowledged_by = user
        alert.acknowledged_at = timezone.now()
        alert.save()
        return alert

    @staticmethod
    def resolve_alert(alert_id):
        alert = AlertEvent.objects.filter(id=alert_id).first()
        if not alert:
            return None
        alert.status = AlertEvent.Status.RESOLVED
        alert.resolved_at = timezone.now()
        alert.save()
        return alert

    @staticmethod
    def list_alerts(status=None, page=1, page_size=50):
        q = {}
        if status:
            q["status"] = status
        offset = (page - 1) * page_size
        return AlertEvent.objects.filter(**q).select_related("rule").order_by("-created_at")[offset:offset + page_size]

    @staticmethod
    def alert_summary(hours=24):
        cutoff = timezone.now() - timedelta(hours=hours)
        return AlertEvent.objects.filter(created_at__gte=cutoff).aggregate(
            total=Count("id"),
            triggered=Count("id", filter=Q(status="triggered")),
            resolved=Count("id", filter=Q(status="resolved")),
        )



