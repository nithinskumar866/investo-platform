import json
import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.realtime.services import RealtimeService

logger = logging.getLogger(__name__)


class InvestmentConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time investment pipeline updates.

    User channel: user_{user_id}
    Events (server → client):
        investment.stage_changed   — deal moved to a new stage
        investment.closed          — deal marked as invested
        investment.term_sheet_sent — term sheet sent by investor
    Events (client → server):
        investment.ping            — heartbeat
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

        if event_type == "investment.ping":
            await self.send_json({"type": "investment.pong"})
        else:
            await self.send_json({"type": "error", "message": f"Unknown event: {event_type}"})

    # ── Event Handlers (called by group_send) ────────────────────

    async def investment_stage_changed(self, event):
        await self.send_json({
            "type": "investment.stage_changed",
            "opportunity_id": event.get("opportunity_id"),
            "old_status": event.get("old_status"),
            "new_status": event.get("new_status"),
            "updated_by": event.get("updated_by"),
            "timestamp": event.get("timestamp"),
        })

    async def investment_closed(self, event):
        await self.send_json({
            "type": "investment.closed",
            "opportunity_id": event.get("opportunity_id"),
            "startup_name": event.get("startup_name"),
            "investor_name": event.get("investor_name"),
            "amount": event.get("amount"),
            "timestamp": event.get("timestamp"),
        })

    async def investment_term_sheet_sent(self, event):
        await self.send_json({
            "type": "investment.term_sheet_sent",
            "opportunity_id": event.get("opportunity_id"),
            "investor_name": event.get("investor_name"),
            "amount_offered": event.get("amount_offered"),
            "equity_offered": event.get("equity_offered"),
            "timestamp": event.get("timestamp"),
        })

    async def presence_update(self, event):
        await self.send_json({
            "type": "presence.update",
            "user_id": event.get("user_id"),
            "status": event.get("status"),
        })
