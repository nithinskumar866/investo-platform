from django.conf import settings
from django.db import models


class SystemError(models.Model):
    class Severity(models.TextChoices):
        DEBUG = "debug", "Debug"
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        CRITICAL = "critical", "Critical"

    class Source(models.TextChoices):
        API = "api", "API"
        CELERY = "celery", "Celery Task"
        WEBSOCKET = "websocket", "WebSocket"
        PAYMENT = "payment", "Payment"
        STORAGE = "storage", "Storage"
        DATABASE = "database", "Database"
        INTERNAL = "internal", "Internal"

    source = models.CharField(max_length=20, choices=Source.choices, default=Source.API, db_index=True)
    severity = models.CharField(max_length=15, choices=Severity.choices, default=Severity.ERROR, db_index=True)
    error_type = models.CharField(max_length=255, blank=True, default="")
    message = models.TextField(blank=True, default="")
    traceback = models.TextField(blank=True, default="")
    endpoint = models.CharField(max_length=500, blank=True, default="")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_errors",
    )
    request_id = models.CharField(max_length=100, blank=True, default="", db_index=True)
    correlation_id = models.CharField(max_length=100, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "obs_system_error"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "severity"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"[{self.source}] {self.error_type}: {self.message[:100]}"


class RequestMetric(models.Model):
    method = models.CharField(max_length=10, blank=True, default="")
    endpoint = models.CharField(max_length=500, blank=True, default="", db_index=True)
    status_code = models.PositiveIntegerField(db_index=True)
    duration_ms = models.PositiveIntegerField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    request_id = models.CharField(max_length=100, blank=True, default="")
    is_error = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "obs_request_metric"
        indexes = [
            models.Index(fields=["endpoint", "-created_at"]),
            models.Index(fields=["is_error", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.method} {self.endpoint} {self.status_code} {self.duration_ms}ms"


class AlertRule(models.Model):
    class Metric(models.TextChoices):
        ERROR_RATE = "error_rate", "Error Rate"
        QUEUE_BACKLOG = "queue_backlog", "Queue Backlog"
        RESPONSE_TIME = "response_time", "Response Time"
        DB_CONNECTIONS = "db_connections", "Database Connections"
        WS_CONNECTIONS = "ws_connections", "WebSocket Connections"
        CACHE_HIT_RATE = "cache_hit_rate", "Cache Hit Rate"
        STORAGE_AVAILABILITY = "storage_availability", "Storage Availability"
        FAILED_LOGINS = "failed_logins", "Failed Logins"

    class Operator(models.TextChoices):
        GT = "gt", "Greater Than"
        LT = "lt", "Less Than"
        GTE = "gte", "Greater Than or Equal"
        LTE = "lte", "Less Than or Equal"
        EQ = "eq", "Equals"

    name = models.CharField(max_length=255)
    metric = models.CharField(max_length=30, choices=Metric.choices, db_index=True)
    operator = models.CharField(max_length=5, choices=Operator.choices)
    threshold = models.FloatField()
    window_minutes = models.PositiveIntegerField(default=5)
    cooldown_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    notify_slack = models.BooleanField(default=False)
    notify_email = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "obs_alert_rule"

    def __str__(self):
        return f"{self.name} ({self.metric} {self.operator} {self.threshold})"


class AlertEvent(models.Model):
    class Status(models.TextChoices):
        TRIGGERED = "triggered", "Triggered"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        RESOLVED = "resolved", "Resolved"

    rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,
        related_name="events",
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.TRIGGERED, db_index=True)
    metric_value = models.FloatField()
    message = models.TextField(blank=True, default="")
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "obs_alert_event"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rule.name} - {self.metric_value} at {self.created_at}"
