from django.contrib import admin

from .models import AlertEvent, AlertRule, RequestMetric, SystemError


@admin.register(SystemError)
class SystemErrorAdmin(admin.ModelAdmin):
    list_display = ["source", "severity", "error_type", "endpoint", "user", "request_id", "created_at"]
    list_filter = ["source", "severity", "created_at"]
    search_fields = ["error_type", "message", "endpoint"]
    date_hierarchy = "created_at"


@admin.register(RequestMetric)
class RequestMetricAdmin(admin.ModelAdmin):
    list_display = ["method", "endpoint", "status_code", "duration_ms", "is_error", "created_at"]
    list_filter = ["method", "is_error", "created_at"]
    search_fields = ["endpoint"]


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ["name", "metric", "operator", "threshold", "is_active"]
    list_filter = ["metric", "is_active"]


@admin.register(AlertEvent)
class AlertEventAdmin(admin.ModelAdmin):
    list_display = ["rule", "status", "metric_value", "created_at"]
    list_filter = ["status", "created_at"]
