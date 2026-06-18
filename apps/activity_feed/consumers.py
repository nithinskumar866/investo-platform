import json
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.realtime.services import RealtimeService

logger = logging.getLogger(__name__)


class FeedConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time activity feed.

    Group: feed
    Events (server → client):
        feed.created    — new activity published
        feed.reaction   — reaction added to an activity
        feed.comment    — comment added to an activity
    Events (client → server):
        feed.ping       — heartbeat
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add("feed", self.channel_name)
        await self.accept()
        RealtimeService.track_connection_open()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("feed", self.channel_name)
        RealtimeService.track_connection_close()

    async def receive_json(self, content):
        event_type = content.get("type")

        if event_type == "feed.ping":
            await self.send_json({"type": "feed.pong"})
        else:
            await self.send_json({"type": "error", "message": f"Unknown event: {event_type}"})

    # ── Event Handlers (called by group_send) ────────────────────

    async def feed_created(self, event):
        await self.send_json({
            "type": "feed.created",
            "activity": event.get("activity", {}),
        })

    async def feed_reaction(self, event):
        await self.send_json({
            "type": "feed.reaction",
            "activity_id": event.get("activity_id"),
            "user_id": event.get("user_id"),
            "reaction_type": event.get("reaction_type"),
            "created": event.get("created", True),
        })

    async def feed_comment(self, event):
        await self.send_json({
            "type": "feed.comment",
            "activity_id": event.get("activity_id"),
            "comment": event.get("comment", {}),
        })

    async def presence_update(self, event):
        await self.send_json({
            "type": "presence.update",
            "user_id": event.get("user_id"),
            "status": event.get("status"),
        })
