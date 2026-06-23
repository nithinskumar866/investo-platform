from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.exceptions import ApplicationError

from .serializers import DateRangeSerializer, StartupQuerySerializer
from .services import AnalyticsService


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def founder_dashboard(request):
    serializer = StartupQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    startup_id = serializer.validated_data.get("startup_id")
    startups = request.user.startups.all()
    if not startups.exists():
        raise ApplicationError("No startups found for this user", "NOT_FOUND", 404)
    if startup_id is None:
        startup_id = startups.first().id

    data = AnalyticsService.founder_dashboard(
        request.user, startup_id,
        start_date=serializer.validated_data.get("start_date"),
        end_date=serializer.validated_data.get("end_date"),
    )
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def investor_dashboard(request):
    serializer = DateRangeSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    data = AnalyticsService.investor_dashboard(
        request.user,
        start_date=serializer.validated_data.get("start_date"),
        end_date=serializer.validated_data.get("end_date"),
    )
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def founder_funnel(request):
    startup_id = request.query_params.get("startup_id")
    startups = request.user.startups.all()
    if not startups.exists():
        raise ApplicationError("No startups found", "NOT_FOUND", 404)
    sid = int(startup_id) if startup_id else startups.first().id

    data = AnalyticsService.founder_funnel(request.user, sid)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def investor_funnel(request):
    data = AnalyticsService.investor_funnel(request.user)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def founder_charts(request):
    serializer = StartupQuerySerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    startup_id = serializer.validated_data.get("startup_id")
    startups = request.user.startups.all()
    if not startups.exists():
        raise ApplicationError("No startups found", "NOT_FOUND", 404)
    sid = int(startup_id) if startup_id else startups.first().id

    data = AnalyticsService.founder_charts(
        request.user, sid,
        start_date=serializer.validated_data.get("start_date"),
        end_date=serializer.validated_data.get("end_date"),
    )
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def investor_charts(request):
    serializer = DateRangeSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    data = AnalyticsService.investor_charts(
        request.user,
        start_date=serializer.validated_data.get("start_date"),
        end_date=serializer.validated_data.get("end_date"),
    )
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def reports(request):
    serializer = DateRangeSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    data = AnalyticsService.reports(
        start_date=serializer.validated_data.get("start_date"),
        end_date=serializer.validated_data.get("end_date"),
    )
    return Response(data)
