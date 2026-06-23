from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .services import ObservabilityService


# ═══════════════════════════════════════════════════════════════════
#  PUBLIC HEALTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    data = ObservabilityService.health_all()
    overall = all(v.get("status") == "healthy" for v in data.values())
    status_code = status.HTTP_200_OK if overall else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response({"overall": "healthy" if overall else "degraded", "services": data}, status=status_code)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_db(request):
    data = ObservabilityService.health_db()
    sc = status.HTTP_200_OK if data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(data, status=sc)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_redis(request):
    data = ObservabilityService.health_redis()
    sc = status.HTTP_200_OK if data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(data, status=sc)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_storage(request):
    data = ObservabilityService.health_storage()
    sc = status.HTTP_200_OK if data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(data, status=sc)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_celery(request):
    data = ObservabilityService.health_celery()
    sc = status.HTTP_200_OK if data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(data, status=sc)


# ═══════════════════════════════════════════════════════════════════
#  ADMIN OPERATIONS CENTER ENDPOINTS
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def ops_health(request):
    data = ObservabilityService.health_all()
    overall = all(v.get("status") == "healthy" for v in data.values())
    return Response({"overall": "healthy" if overall else "degraded", "services": data})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def ops_metrics(request):
    data = ObservabilityService.metrics()
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def ops_errors(request):
    source = request.query_params.get("source")
    severity = request.query_params.get("severity")
    page = int(request.query_params.get("page", 1))
    errors = ObservabilityService.list_errors(source, severity, page)
    summary = ObservabilityService.error_summary()
    return Response({
        "summary": summary,
        "errors": [
            {
                "id": e.id,
                "source": e.source,
                "severity": e.severity,
                "error_type": e.error_type,
                "message": e.message[:200],
                "user_email": e.user.email if e.user else None,
                "request_id": e.request_id,
                "created_at": e.created_at.isoformat(),
            }
            for e in errors
        ],
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def ops_jobs(request):
    data = ObservabilityService.job_stats()
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def ops_alerts(request):
    status_filter = request.query_params.get("status")
    page = int(request.query_params.get("page", 1))
    alerts = ObservabilityService.list_alerts(status_filter, page)
    summary = ObservabilityService.alert_summary()
    return Response({
        "summary": summary,
        "alerts": [
            {
                "id": a.id,
                "rule_name": a.rule.name,
                "metric": a.rule.metric,
                "metric_value": a.metric_value,
                "threshold": a.rule.threshold,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
    })
