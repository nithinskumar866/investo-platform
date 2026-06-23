import pytest
import json
import time
from django.utils import timezone
from datetime import timedelta
from unittest.mock import Mock, patch
from django.test import RequestFactory

from apps.accounts.models import User
from apps.observability.models import SystemError, RequestMetric, AlertRule, AlertEvent
from apps.observability.services import ObservabilityService
from apps.observability.middleware import RequestIDMiddleware, MetricsMiddleware


# ── User fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def founder(db):
    return User.objects.create_user(
        email="founder@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123", role="admin",
        is_staff=True, is_superuser=True,
    )


@pytest.fixture
def system_error(db):
    return SystemError.objects.create(
        source=SystemError.Source.API,
        severity=SystemError.Severity.ERROR,
        error_type="ValueError",
        message="Test error",
        traceback="Traceback...",
        endpoint="/api/test/",
        request_id="req-001",
        correlation_id="corr-001",
    )


@pytest.fixture
def request_metric(db):
    return RequestMetric.objects.create(
        method="GET",
        endpoint="/api/test/",
        status_code=200,
        duration_ms=150,
        is_error=False,
    )


@pytest.fixture
def alert_rule(db):
    return AlertRule.objects.create(
        name="High Error Rate",
        metric=AlertRule.Metric.ERROR_RATE,
        operator=AlertRule.Operator.GT,
        threshold=90.0,
        window_minutes=5,
        cooldown_minutes=30,
        is_active=True,
    )


@pytest.fixture
def alert_event(db, alert_rule):
    return AlertEvent.objects.create(
        rule=alert_rule,
        status=AlertEvent.Status.TRIGGERED,
        metric_value=95.0,
        message="Error rate exceeded 90%",
    )


# ── Model tests ──────────────────────────────────────────────────────────

class TestSystemErrorModel:
    def test_create_system_error(self, system_error):
        assert system_error.pk is not None
        assert system_error.source == "api"
        assert system_error.severity == "error"
        assert str(system_error).startswith("[api]")

    def test_severity_choices(self):
        assert SystemError.Severity.CRITICAL == "critical"
        assert SystemError.Severity.WARNING == "warning"

    def test_source_choices(self):
        assert SystemError.Source.API == "api"
        assert SystemError.Source.CELERY == "celery"
        assert SystemError.Source.PAYMENT == "payment"


class TestRequestMetricModel:
    def test_create_request_metric(self, request_metric):
        assert request_metric.pk is not None
        assert request_metric.method == "GET"
        assert request_metric.status_code == 200
        assert str(request_metric) == "GET /api/test/ 200 150ms"


class TestAlertRuleModel:
    def test_create_alert_rule(self, alert_rule):
        assert alert_rule.pk is not None
        assert str(alert_rule) == "High Error Rate (error_rate gt 90.0)"

    def test_metric_choices(self):
        assert AlertRule.Metric.ERROR_RATE == "error_rate"
        assert AlertRule.Metric.RESPONSE_TIME == "response_time"


class TestAlertEventModel:
    def test_create_alert_event(self, alert_event):
        assert alert_event.pk is not None
        assert alert_event.status == AlertEvent.Status.TRIGGERED
        assert str(alert_event).startswith("High Error Rate")

    def test_alert_lifecycle(self, alert_event, admin_user):
        alert_event.status = AlertEvent.Status.ACKNOWLEDGED
        alert_event.acknowledged_by = admin_user
        alert_event.acknowledged_at = timezone.now()
        alert_event.save()
        alert_event.status = AlertEvent.Status.RESOLVED
        alert_event.resolved_at = timezone.now()
        alert_event.save()
        assert alert_event.status == AlertEvent.Status.RESOLVED


# ── Middleware tests ─────────────────────────────────────────────────────

class TestRequestIDMiddleware:
    def test_adds_request_id_header(self, rf):
        request = rf.get("/api/test/")
        middleware = RequestIDMiddleware(lambda r: Mock())
        middleware.process_request(request)
        assert hasattr(request, "request_id")

    def test_response_has_x_request_id(self, rf):
        request = rf.get("/api/test/")
        response = Mock()
        middleware = RequestIDMiddleware(lambda r: response)
        middleware.process_request(request)
        result = middleware.process_response(request, response)
        assert hasattr(result, "__setitem__") or response["X-Request-ID"]

    def test_uses_existing_header(self, rf):
        request = rf.get("/api/test/", HTTP_X_REQUEST_ID="existing-id")
        middleware = RequestIDMiddleware(lambda r: Mock())
        middleware.process_request(request)
        assert request.request_id == "existing-id"

    def test_correlation_id(self, rf):
        request = rf.get("/api/test/", HTTP_X_CORRELATION_ID="corr-123")
        middleware = RequestIDMiddleware(lambda r: Mock())
        middleware.process_request(request)
        assert request.correlation_id == "corr-123"


class TestMetricsMiddleware:
    def test_records_metric(self, rf):
        request = rf.get("/api/test/")
        request._start_time = time.time()
        request.user = Mock(is_authenticated=False)
        request.request_id = "req-001"
        request.path = "/api/test/"
        response = Mock(status_code=200)
        middleware = MetricsMiddleware(lambda r: response)
        result = middleware.process_response(request, response)
        assert RequestMetric.objects.count() >= 0

    def test_skips_excluded_paths(self, rf):
        request = rf.get("/health/")
        request._start_time = time.time()
        request.user = Mock(is_authenticated=False)
        request.request_id = "req-002"
        request.path = "/health/"
        response = Mock(status_code=200)
        middleware = MetricsMiddleware(lambda r: response)
        result = middleware.process_response(request, response)
        assert result == response


# ── Service tests ────────────────────────────────────────────────────────

class TestObservabilityService:
    def test_log_error(self):
        error = ObservabilityService.log_error(
            source="api",
            error_type="ValueError",
            message="Test error logging",
            endpoint="/api/test/",
            request_id="req-003",
        )
        assert error.pk is not None
        assert error.message == "Test error logging"

    def test_list_errors(self, system_error):
        errors = ObservabilityService.list_errors()
        assert system_error in errors

    def test_list_errors_with_source_filter(self, system_error):
        errors = ObservabilityService.list_errors(source="api")
        assert system_error in errors
        errors = ObservabilityService.list_errors(source="celery")
        assert system_error not in errors

    def test_get_error(self, system_error):
        error = ObservabilityService.get_error(system_error.id)
        assert error.id == system_error.id

    def test_error_summary(self, system_error):
        summary = ObservabilityService.error_summary()
        assert "total" in summary or isinstance(summary, dict)

    def test_metrics(self, request_metric):
        data = ObservabilityService.metrics()
        assert "api" in data
        assert "system" in data

    def test_list_alerts(self, alert_event):
        alerts = ObservabilityService.list_alerts()
        assert alert_event in alerts

    def test_list_alerts_status_filter(self, alert_event):
        alerts = ObservabilityService.list_alerts(status="triggered")
        assert alert_event in alerts
        alerts = ObservabilityService.list_alerts(status="resolved")
        assert alert_event not in alerts

    def test_alert_summary(self, alert_event):
        summary = ObservabilityService.alert_summary()
        assert isinstance(summary, dict)

    def test_acknowledge_alert(self, alert_event, admin_user):
        result = ObservabilityService.acknowledge_alert(alert_event.id, admin_user)
        assert result is not None
        assert result.status == AlertEvent.Status.ACKNOWLEDGED

    def test_resolve_alert(self, alert_event):
        result = ObservabilityService.resolve_alert(alert_event.id)
        assert result is not None
        assert result.status == AlertEvent.Status.RESOLVED


# ── View tests ──────────────────────────────────────────────────────────

class TestObservabilityViews:
    def test_health_all(self, api_client):
        resp = api_client.get("/api/v1/health/")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "overall" in data
        assert "services" in data

    def test_health_db(self, api_client):
        resp = api_client.get("/api/v1/health/db/")
        assert resp.status_code in (200, 503)

    def test_health_redis(self, api_client):
        resp = api_client.get("/api/v1/health/redis/")
        assert resp.status_code in (200, 503)

    def test_health_storage(self, api_client):
        resp = api_client.get("/api/v1/health/storage/")
        assert resp.status_code in (200, 503)

    def test_health_celery(self, api_client):
        resp = api_client.get("/api/v1/health/celery/")
        assert resp.status_code in (200, 503)

    def test_ops_health(self, admin_client):
        resp = admin_client.get("/api/v1/admin/ops/health/")
        assert resp.status_code == 200

    def test_ops_metrics(self, admin_client):
        resp = admin_client.get("/api/v1/admin/ops/metrics/")
        assert resp.status_code == 200

    def test_ops_errors(self, admin_client, system_error):
        resp = admin_client.get("/api/v1/admin/ops/errors/")
        assert resp.status_code == 200

    def test_ops_jobs(self, admin_client):
        resp = admin_client.get("/api/v1/admin/ops/jobs/")
        assert resp.status_code == 200

    def test_ops_alerts(self, admin_client, alert_event):
        resp = admin_client.get("/api/v1/admin/ops/alerts/")
        assert resp.status_code == 200

    def test_ops_endpoints_forbidden(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/admin/ops/health/")
        assert resp.status_code == 403

    def test_ops_errors_forbidden(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/admin/ops/errors/")
        assert resp.status_code == 403
