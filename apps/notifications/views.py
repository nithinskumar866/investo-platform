import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import Notification
from .services import NotificationService
from .serializers import NotificationSerializer
from apps.common.exceptions import ApplicationError
from apps.common.permissions import IsOwner

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Notifications"],
    summary="List notifications for the current user",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_list(request):
    unread_only = request.GET.get("unread_only", "false").lower() == "true"
    limit = request.GET.get("limit")
    try:
        limit = min(int(limit), 100) if limit else None
    except (ValueError, TypeError):
        limit = None

    notifications = NotificationService.get_user_notifications(
        request.user, unread_only=unread_only, limit=limit
    )
    serializer = NotificationSerializer(notifications, many=True)
    return Response({"status": "success", "data": serializer.data})


@extend_schema(
    tags=["Notifications"],
    summary="Get unread notification count",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def notification_unread_count(request):
    count = NotificationService.get_unread_count(request.user)
    return Response({"status": "success", "data": {"count": count}})


@extend_schema(
    tags=["Notifications"],
    summary="Mark a notification as read",
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsOwner])
def notification_mark_read(request, pk=None):
    success = NotificationService.mark_as_read(request.user, pk)
    if not success:
        raise ApplicationError("Notification not found", "NOT_FOUND", 404)
    logger.info(f"Notification {pk} marked as read by {request.user.email}")
    return Response({"status": "success", "data": {"message": "Notification marked as read"}})


@extend_schema(
    tags=["Notifications"],
    summary="Mark all notifications as read",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def notification_mark_all_read(request):
    count = NotificationService.mark_all_as_read(request.user)
    logger.info(f"All notifications marked as read for {request.user.email}")
    return Response({"status": "success", "data": {"marked_count": count}})