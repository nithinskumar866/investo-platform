import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.realtime.presence import UserPresence
from apps.realtime.services import RealtimeService

from .models import Conversation, Message, MessageReadStatus
from .repositories import ChatRepository

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time chat.

    Rooms: chat_{conversation_id}
    Events:
        chat.message     — new message
        chat.typing      — typing indicator
        chat.read        — read receipt
        chat.presence    — user online/offline in conversation
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conversation_id = None
        self.room_group_name = None
        self.user = None

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"].get("conversation_id")
        if not self.conversation_id:
            await self.close(code=4004)
            return

        if not await self._user_in_conversation():
            await self.close(code=4003)
            return

        self.room_group_name = f"chat_{self.conversation_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        UserPresence.set_online(self.user.id, channel_name=self.channel_name)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_presence",
                "user_id": self.user.id,
                "user_email": self.user.email,
                "status": "online",
            },
        )

        RealtimeService.track_connection_open()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name") and self.room_group_name:
            if self.user and self.user.is_authenticated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_presence",
                        "user_id": self.user.id,
                        "user_email": self.user.email,
                        "status": "offline",
                    },
                )

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

        if self.user and self.user.is_authenticated:
            UserPresence.set_offline(self.user.id)

        RealtimeService.track_connection_close()

    async def receive_json(self, content):
        if not RealtimeService.check_rate_limit(
            self.user.id, content.get("type", ""), max_per_minute=60,
        ):
            await self.send_json({"type": "error", "message": "Rate limit exceeded"})
            return

        event_type = content.get("type")

        if event_type == "chat.message":
            await self._handle_message(content)
        elif event_type == "chat.typing":
            await self._handle_typing(content)
        elif event_type == "chat.read":
            await self._handle_read(content)
        elif event_type == "chat.presence":
            await self._handle_presence_request(content)
        else:
            await self.send_json({"type": "error", "message": f"Unknown event: {event_type}"})

    async def _handle_message(self, content):
        message_content = content.get("content", "").strip()
        message_type = content.get("message_type", "text")
        if not message_content:
            return

        message = await self._create_message(message_content, message_type)
        if not message:
            return

        RealtimeService.track_message()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": message.id,
                "conversation_id": self.conversation_id,
                "sender_id": self.user.id,
                "sender_email": self.user.email,
                "sender_name": f"{self.user.first_name} {self.user.last_name}".strip() or self.user.email,
                "content": message.content,
                "message_type": message.message_type,
                "created_at": message.created_at.isoformat(),
            },
        )

        from apps.notifications.services import NotificationService
        await database_sync_to_async(self._notify_participants)(message)

    def _notify_participants(self, message):
        conversation = Conversation.objects.get(id=self.conversation_id)
        for participant in conversation.participants.all():
            if participant.id != self.user.id:
                NotificationService.notify(
                    recipient=participant,
                    notification_type="message_received",
                    title="New Message",
                    message=f"{self.user.email}: {message.content[:120]}",
                    actor=self.user,
                    data={
                        "conversation_id": self.conversation_id,
                        "message_id": message.id,
                        "message_type": message.message_type,
                    },
                )

    async def _handle_typing(self, content):
        is_typing = content.get("is_typing", False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_typing",
                "user_id": self.user.id,
                "user_email": self.user.email,
                "is_typing": is_typing,
            },
        )

    async def _handle_read(self, content):
        message_id = content.get("message_id")
        if not message_id:
            return

        await self._mark_read(message_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_read",
                "message_id": message_id,
                "user_id": self.user.id,
                "user_email": self.user.email,
            },
        )

    async def _handle_presence_request(self, content):
        target_user_id = content.get("user_id")
        if not target_user_id:
            return

        presence = UserPresence.get_presence(target_user_id)
        await self.send_json({
            "type": "chat.presence",
            "user_id": target_user_id,
            "online": presence["online"],
        })

    # ── Event Handlers (called by group_send) ────────────────────

    async def chat_message(self, event):
        await self.send_json({
            "type": "chat.message",
            "message_id": event["message_id"],
            "conversation_id": event["conversation_id"],
            "sender_id": event["sender_id"],
            "sender_email": event["sender_email"],
            "sender_name": event["sender_name"],
            "content": event["content"],
            "message_type": event["message_type"],
            "created_at": event["created_at"],
        })

    async def chat_typing(self, event):
        await self.send_json({
            "type": "chat.typing",
            "user_id": event["user_id"],
            "user_email": event["user_email"],
            "is_typing": event["is_typing"],
        })

    async def chat_read(self, event):
        await self.send_json({
            "type": "chat.read",
            "message_id": event["message_id"],
            "user_id": event["user_id"],
            "user_email": event["user_email"],
        })

    async def chat_presence(self, event):
        await self.send_json({
            "type": "chat.presence",
            "user_id": event["user_id"],
            "user_email": event.get("user_email", ""),
            "online": event.get("status") == "online",
        })

    # ── Database Helpers ──────────────────────────────────────────

    @database_sync_to_async
    def _user_in_conversation(self):
        return ChatRepository.participant_exists_by_ids(
            self.conversation_id, self.user.id,
        )

    @database_sync_to_async
    def _create_message(self, content, message_type):
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            message = ChatRepository.create_message(
                conversation=conversation,
                sender=self.user,
                message_type=message_type,
                content=content,
            )
            return message
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def _mark_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id, conversation_id=self.conversation_id)
            MessageReadStatus.objects.get_or_create(message=message, user=self.user)
        except Message.DoesNotExist:
            pass
