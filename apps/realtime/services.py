import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .presence import PresenceRepository

logger = logging.getLogger(__name__)


class RealtimeService:
    """Abstraction layer for Channels-based real-time communication."""

    # ── Event Publishing ──────────────────────────────────────────

    @staticmethod
    def publish_event(group_name, event_type, payload):
        """Publish an event to a Channels group."""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                group_name,
                {"type": event_type, **payload},
            )
        except Exception:
            logger.exception(f"Failed to publish event {event_type} to {group_name}")

    @staticmethod
    def broadcast_to_user(user_id, event_type, payload):
        """Send an event to a user's personal channel.

        User channel pattern: user_{user_id}
        """
        RealtimeService.publish_event(
            f"user_{user_id}", event_type, payload,
        )

    @staticmethod
    def broadcast_to_group(group_name, event_type, payload):
        """Send an event to a named group."""
        RealtimeService.publish_event(group_name, event_type, payload)

    @staticmethod
    def broadcast_to_conversation(conversation_id, event_type, payload):
        """Send an event to a chat conversation room.

        Room channel pattern: chat_{conversation_id}
        """
        RealtimeService.publish_event(
            f"chat_{conversation_id}", event_type, payload,
        )

    @staticmethod
    def broadcast_to_feed(event_type, payload):
        """Broadcast an event to the global feed.

        Feed channel: feed
        """
        RealtimeService.publish_event("feed", event_type, payload)

    @staticmethod
    def broadcast_to_notifications(user_id, event_type, payload):
        """Send a notification event to a specific user."""
        RealtimeService.broadcast_to_user(
            user_id, event_type, payload,
        )

    # ── Presence Management ───────────────────────────────────────

    @staticmethod
    def user_online(user_id, channel_name=None):
        PresenceRepository.set_online(user_id, channel_name)
        RealtimeService.broadcast_to_user(
            user_id,
            "presence_update",
            {"type": "presence_update", "user_id": user_id, "status": "online"},
        )

    @staticmethod
    def user_offline(user_id):
        PresenceRepository.set_offline(user_id)
        RealtimeService.broadcast_to_user(
            user_id,
            "presence_update",
            {"type": "presence_update", "user_id": user_id, "status": "offline"},
        )

    @staticmethod
    def get_presence(user_id):
        return PresenceRepository.get_presence(user_id)

    @staticmethod
    def get_online_users():
        return PresenceRepository.get_online_users()

    # ── Rate Limiting ─────────────────────────────────────────────

    _rate_counters = {}

    @classmethod
    def check_rate_limit(cls, user_id, event_type, max_per_minute=60):
        import time
        now = time.time()
        key = (user_id, event_type)
        window = cls._rate_counters.get(key, [])
        window = [t for t in window if now - t < 60]
        if len(window) >= max_per_minute:
            return False
        window.append(now)
        cls._rate_counters[key] = window
        return True

    # ── Analytics ─────────────────────────────────────────────────

    _connection_stats = {"active_connections": 0, "messages_per_minute": 0,
                         "notification_delivery_count": 0,
                         "connection_durations": []}

    @classmethod
    def track_connection_open(cls):
        cls._connection_stats["active_connections"] += 1

    @classmethod
    def track_connection_close(cls, duration=None):
        cls._connection_stats["active_connections"] -= 1
        if duration is not None:
            cls._connection_stats["connection_durations"].append(duration)

    @classmethod
    def track_message(cls):
        cls._connection_stats["messages_per_minute"] += 1

    @classmethod
    def track_notification_delivery(cls):
        cls._connection_stats["notification_delivery_count"] += 1

    @classmethod
    def get_analytics(cls):
        return dict(cls._connection_stats)
