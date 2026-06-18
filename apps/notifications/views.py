from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.common.exceptions import ApplicationError

from .permissions import IsNotificationOwner
from .serializers import (
    NotificationAnalyticsSerializer,
    NotificationCursorPaginatedResponse,
    NotificationListSerializer,
    NotificationPreferenceSerializer,
    UnreadCountSerializer,
)
from .services import NotificationService


class NotificationViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cursor = request.query_params.get("cursor")
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            limit = 20

        notifications, has_more = NotificationService.get_notifications(
            request.user, cursor=cursor, limit=limit,
        )
        serializer = NotificationListSerializer(notifications, many=True)

        next_cursor = None
        if notifications:
            next_cursor = notifications[-1].created_at.isoformat()

        return Response({
            "results": serializer.data,
            "cursor": next_cursor if has_more else None,
            "has_more": has_more,
        })

    @action(detail=False, methods=["get"])
    def unread(self, request):
        cursor = request.query_params.get("cursor")
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            limit = 20

        notifications, has_more = NotificationService.get_unread(
            request.user, cursor=cursor, limit=limit,
        )
        serializer = NotificationListSerializer(notifications, many=True)

        next_cursor = None
        if notifications:
            next_cursor = notifications[-1].created_at.isoformat()

        return Response({
            "results": serializer.data,
            "cursor": next_cursor if has_more else None,
            "has_more": has_more,
        })

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = NotificationService.get_unread_count(request.user)
        return Response(UnreadCountSerializer({"count": count}).data)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = NotificationService.mark_read(pk, request.user)
        if not notification:
            raise ApplicationError(
                "Notification not found", "NOT_FOUND", 404,
            )
        serializer = NotificationListSerializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        count = NotificationService.mark_all_read(request.user)
        return Response({"marked_count": count})

    def destroy(self, request, pk=None):
        deleted = NotificationService.delete_notification(pk, request.user)
        if not deleted:
            raise ApplicationError(
                "Notification not found", "NOT_FOUND", 404,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get", "patch"])
    def preferences(self, request):
        if request.method == "GET":
            prefs = NotificationService.get_preferences(request.user)
            serializer = NotificationPreferenceSerializer(prefs)
            return Response(serializer.data)

        serializer = NotificationPreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prefs = NotificationService.update_preferences(
            request.user, serializer.validated_data,
        )
        result = NotificationPreferenceSerializer(prefs)
        return Response(result.data)

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        analytics = NotificationService.get_analytics(request.user)
        serializer = NotificationAnalyticsSerializer(analytics)
        return Response(serializer.data)
