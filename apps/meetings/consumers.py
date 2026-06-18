import json
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.realtime.services import RealtimeService

logger = logging.getLogger(__name__)


class MeetingConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time meeting updates.

    User channel: user_{user_id}
    Events (server → client):
        meeting.created    — new meeting scheduled
        meeting.updated    — meeting details changed
        meeting.cancelled  — meeting cancelled
        meeting.confirmed  — meeting confirmed
        meeting.reminder   — meeting reminder
    Events (client → server):
        meeting.ping       — heartbeat
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

        if event_type == "meeting.ping":
            await self.send_json({"type": "meeting.pong"})
        else:
            await self.send_json({"type": "error", "message": f"Unknown event: {event_type}"})

    # ── Event Handlers (called by group_send) ────────────────────

    async def meeting_created(self, event):
        await self.send_json({
            "type": "meeting.created",
            "meeting": event.get("meeting", {}),
        })

    async def meeting_updated(self, event):
        await self.send_json({
            "type": "meeting.updated",
            "meeting": event.get("meeting", {}),
        })

    async def meeting_cancelled(self, event):
        await self.send_json({
            "type": "meeting.cancelled",
            "meeting": event.get("meeting", {}),
            "reason": event.get("reason"),
        })

    async def meeting_confirmed(self, event):
        await self.send_json({
            "type": "meeting.confirmed",
            "meeting": event.get("meeting", {}),
        })

    async def meeting_reminder(self, event):
        await self.send_json({
            "type": "meeting.reminder",
            "meeting": event.get("meeting", {}),
            "minutes_before": event.get("minutes_before"),
        })

    async def presence_update(self, event):
        await self.send_json({
            "type": "presence.update",
            "user_id": event.get("user_id"),
            "status": event.get("status"),
        })
