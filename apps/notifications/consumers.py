import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.realtime.services import RealtimeService

from .repositories import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time notifications.

    User channel: user_{user_id}
    Events (server → client):
        notification.created     — new notification delivered
        notification.read        — notification marked read
        notification.count_updated — unread count changed
    Events (client → server):
        notification.mark_read   — mark single notification read
        notification.mark_all_read — mark all notifications read
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.user_channel = None

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.user_channel = f"user_{self.user.id}"

        await self.channel_layer.group_add(
            self.user_channel,
            self.channel_name,
        )

        await self.accept()

        unread_count = await self._get_unread_count()
        await self.send_json({
            "type": "notification.count_updated",
            "unread_count": unread_count,
        })

        RealtimeService.track_connection_open()

    async def disconnect(self, close_code):
        if self.user_channel:
            await self.channel_layer.group_discard(
                self.user_channel,
                self.channel_name,
            )
        RealtimeService.track_connection_close()

    async def receive_json(self, content):
        event_type = content.get("type")

        if event_type == "notification.mark_read":
            await self._handle_mark_read(content)
        elif event_type == "notification.mark_all_read":
            await self._handle_mark_all_read()
        else:
            await self.send_json({"type": "error", "message": f"Unknown event: {event_type}"})

    async def _handle_mark_read(self, content):
        notification_id = content.get("notification_id")
        if not notification_id:
            return

        await self._mark_read(notification_id)

        await self.channel_layer.group_send(
            self.user_channel,
            {
                "type": "notification_read",
                "notification_id": notification_id,
            },
        )

    async def _handle_mark_all_read(self):
        await self._mark_all_read()

        await self.channel_layer.group_send(
            self.user_channel,
            {
                "type": "notification_read_all",
            },
        )

    # ── Event Handlers (called by group_send) ────────────────────

    async def notification_created(self, event):
        await self.send_json({
            "type": "notification.created",
            "notification": event.get("notification", {}),
        })
        RealtimeService.track_notification_delivery()

    async def notification_read(self, event):
        unread_count = await self._get_unread_count()
        await self.send_json({
            "type": "notification.read",
            "notification_id": event.get("notification_id"),
            "unread_count": unread_count,
        })

    async def notification_read_all(self, event):
        await self.send_json({
            "type": "notification.read",
            "unread_count": 0,
        })

    async def notification_count_updated(self, event):
        await self.send_json({
            "type": "notification.count_updated",
            "unread_count": event.get("unread_count", 0),
        })

    async def presence_update(self, event):
        await self.send_json({
            "type": "presence.update",
            "user_id": event.get("user_id"),
            "status": event.get("status"),
        })

    # ── Database Helpers ──────────────────────────────────────────

    @database_sync_to_async
    def _get_unread_count(self):
        return NotificationRepository.get_unread_count(self.user)

    @database_sync_to_async
    def _mark_read(self, notification_id):
        try:
            from .models import Notification
            notification = Notification.objects.get(id=notification_id, recipient=self.user)
            NotificationRepository.mark_read(notification)
        except Notification.DoesNotExist:
            pass

    @database_sync_to_async
    def _mark_all_read(self):
        return NotificationRepository.mark_all_read(self.user)
