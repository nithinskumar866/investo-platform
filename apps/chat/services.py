import logging

from django.db import transaction

from apps.common.exceptions import ApplicationError

from .repositories import ChatRepository

logger = logging.getLogger(__name__)


class ChatService:
    """Business logic for chat operations."""

    @staticmethod
    def _validate_participant_roles(current_user, other_user):
        """Ensure investor-founder communication only."""
        roles = {current_user.role, other_user.role}
        if "investor" not in roles or "entrepreneur" not in roles:
            raise ApplicationError(
                "Conversations are only allowed between investors and founders",
                "INVALID_PARTICIPANTS", 400,
            )

    @staticmethod
    def _validate_matched(current_user, other_user):
        """Ensure both users have a match score between them."""
        if not ChatRepository.user_has_match_with(current_user, other_user):
            raise ApplicationError(
                "You can only message matched investors or founders",
                "NOT_MATCHED", 403,
            )

    @staticmethod
    def start_conversation(current_user, other_user_id):
        """
        Start a conversation between matched investor and entrepreneur.
        Only matched users can start conversations.
        Returns existing conversation if one already exists.
        """
        if current_user.id == other_user_id:
            raise ApplicationError(
                "You cannot start a conversation with yourself",
                "SELF_CONVERSATION", 400,
            )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            other_user = User.objects.get(id=other_user_id, is_active=True)
        except User.DoesNotExist:
            raise ApplicationError("User not found", "NOT_FOUND", 404)

        ChatService._validate_participant_roles(current_user, other_user)
        ChatService._validate_matched(current_user, other_user)

        existing = ChatRepository.get_user_conversations(current_user)
        for conv in existing:
            participants = list(conv.participants.all())
            p_ids = [p.user_id for p in participants]
            if other_user.id in p_ids:
                return conv

        conversation = ChatRepository.create_conversation(
            created_by=current_user,
            participant_ids=[other_user.id],
        )

        from .models import Message
        system_msg = ChatRepository.create_message(
            conversation=conversation,
            sender=current_user,
            message_type=Message.MessageType.SYSTEM,
            content=f"Conversation started between {current_user.first_name} and {other_user.first_name}",
        )

        logger.info(
            f"Conversation {conversation.id} started between "
            f"{current_user.email} and {other_user.email}",
        )
        return conversation

    @staticmethod
    def send_message(current_user, conversation_id, message_type, content, attachment=None, metadata=None):
        """Send a message in an existing conversation."""
        conversation = ChatRepository.get_conversation(conversation_id)
        if not conversation:
            raise ApplicationError("Conversation not found", "NOT_FOUND", 404)

        if not conversation.is_active:
            raise ApplicationError("Conversation is closed", "CONVERSATION_CLOSED", 400)

        if not ChatRepository.participant_exists(conversation, current_user):
            raise ApplicationError("Not a participant", "FORBIDDEN", 403)

        message = ChatRepository.create_message(
            conversation=conversation,
            sender=current_user,
            message_type=message_type,
            content=content,
            attachment=attachment,
            metadata=metadata,
        )

        from apps.notifications.services import NotificationService
        for participant in conversation.participants.all():
            if participant.user.id != current_user.id:
                NotificationService.notify(
                    recipient=participant.user,
                    notification_type="message_received",
                    title="New Message",
                    message=f"{current_user.email}: {content[:120]}{'...' if len(content) > 120 else ''}",
                    actor=current_user,
                    data={
                        "conversation_id": conversation.id,
                        "message_id": message.id,
                        "message_type": message_type,
                    },
                )
        return message

    @staticmethod
    def list_conversations(current_user):
        """List all conversations for the current user with unread counts."""
        return ChatRepository.get_user_conversations(current_user)

    @staticmethod
    def get_conversation(current_user, conversation_id):
        """Get a single conversation if the user is a participant."""
        conversation = ChatRepository.get_conversation(conversation_id)
        if not conversation:
            raise ApplicationError("Conversation not found", "NOT_FOUND", 404)
        if not ChatRepository.participant_exists(conversation, current_user):
            raise ApplicationError("Not a participant", "FORBIDDEN", 403)
        return conversation

    @staticmethod
    def get_conversation_messages(current_user, conversation_id, before=None, limit=50):
        """Get paginated messages for a conversation."""
        conversation = ChatService.get_conversation(current_user, conversation_id)
        return ChatRepository.get_messages(conversation, before=before, limit=limit)

    @staticmethod
    def mark_read(current_user, conversation_id):
        """Mark all messages in a conversation as read for the current user."""
        conversation = ChatService.get_conversation(current_user, conversation_id)
        ChatRepository.mark_conversation_read(conversation, current_user)
        return True

    @staticmethod
    def unread_count(current_user):
        """Get total unread message count for the current user."""
        return ChatRepository.unread_count(current_user)

    @staticmethod
    def conversation_permissions(current_user, conversation) -> bool:
        """Check if the user has permission to access a conversation."""
        return ChatRepository.participant_exists(conversation, current_user)
