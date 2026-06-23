from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.common.exceptions import ApplicationError

from .serializers import (
    AvailabilitySerializer,
    CalendarMeetingSerializer,
    CancelSerializer,
    CompleteSerializer,
    CreateMeetingSerializer,
    MeetingAnalyticsSerializer,
    MeetingDetailSerializer,
    MeetingListSerializer,
    MeetingParticipantSerializer,
    MeetingEventSerializer,
    RescheduleSerializer,
    UpdateMeetingSerializer,
)
from .services import MeetingService


class MeetingViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cursor = request.query_params.get("cursor")
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            limit = 20

        meetings, has_more = MeetingService.list_meetings(
            request.user, cursor=cursor, limit=limit,
        )
        serializer = MeetingListSerializer(meetings, many=True)
        next_cursor = meetings[-1].scheduled_start.isoformat() if meetings else None
        return Response({
            "results": serializer.data,
            "cursor": next_cursor if has_more else None,
            "has_more": has_more,
        })

    def create(self, request):
        serializer = CreateMeetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = MeetingService.schedule_meeting(
            request.user, serializer.validated_data,
        )
        result = MeetingDetailSerializer(meeting)
        return Response(result.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        meeting = MeetingService.get_meeting(pk, request.user)
        serializer = MeetingDetailSerializer(meeting)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        serializer = UpdateMeetingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = MeetingService._get_meeting(pk, request.user)

        if meeting.organizer_id != request.user.id:
            raise PermissionDenied("Only the organizer can update meeting details")

        from .repositories import MeetingRepository
        meeting = MeetingRepository.update_meeting(meeting, serializer.validated_data)
        result = MeetingDetailSerializer(meeting)
        return Response(result.data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        meeting = MeetingService.confirm_meeting(pk, request.user)
        serializer = MeetingDetailSerializer(meeting)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        serializer = CancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = MeetingService.cancel_meeting(
            pk, request.user, serializer.validated_data.get("reason"),
        )
        result = MeetingDetailSerializer(meeting)
        return Response(result.data)

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        serializer = RescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = MeetingService.reschedule_meeting(
            pk, request.user, serializer.validated_data,
        )
        result = MeetingDetailSerializer(meeting)
        return Response(result.data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        serializer = CompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = MeetingService.complete_meeting(
            pk, request.user, serializer.validated_data.get("notes"),
        )
        result = MeetingDetailSerializer(meeting)
        return Response(result.data)

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        cursor = request.query_params.get("cursor")
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            limit = 20

        meetings, has_more = MeetingService.list_upcoming(
            request.user, cursor=cursor, limit=limit,
        )
        serializer = MeetingListSerializer(meetings, many=True)
        next_cursor = meetings[-1].scheduled_start.isoformat() if meetings else None
        return Response({
            "results": serializer.data,
            "cursor": next_cursor if has_more else None,
            "has_more": has_more,
        })

    @action(detail=False, methods=["get"])
    def past(self, request):
        cursor = request.query_params.get("cursor")
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            limit = 20

        meetings, has_more = MeetingService.list_past(
            request.user, cursor=cursor, limit=limit,
        )
        serializer = MeetingListSerializer(meetings, many=True)
        next_cursor = meetings[-1].scheduled_start.isoformat() if meetings else None
        return Response({
            "results": serializer.data,
            "cursor": next_cursor if has_more else None,
            "has_more": has_more,
        })

    @action(detail=False, methods=["get"])
    def calendar(self, request):
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if not start or not end:
            raise ApplicationError(
                "start and end query params required (ISO format)",
                "MISSING_PARAMS", 400,
            )
        from django.utils.dateparse import parse_datetime
        start_date = parse_datetime(start)
        end_date = parse_datetime(end)
        if not start_date or not end_date:
            raise ApplicationError(
                "Invalid date format. Use ISO 8601.", "INVALID_DATE", 400,
            )
        meetings = MeetingService.get_calendar(
            request.user, start_date, end_date,
        )
        serializer = CalendarMeetingSerializer(meetings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        analytics = MeetingService.get_analytics(request.user)
        serializer = MeetingAnalyticsSerializer(analytics)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        timeline = MeetingService.get_timeline(pk, request.user)
        serializer = MeetingEventSerializer(timeline, many=True)
        return Response(serializer.data)


class AvailabilityViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        slots = MeetingService.get_availability(request.user)
        serializer = AvailabilitySerializer(slots, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = AvailabilitySerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        slots = MeetingService.update_availability(
            request.user, serializer.validated_data,
        )
        result = AvailabilitySerializer(slots, many=True)
        return Response(result.data, status=status.HTTP_201_CREATED)
