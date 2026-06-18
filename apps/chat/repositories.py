from django.db import transaction
from django.db.models import Count, Q, Prefetch
from django.utils import timezone

from .models import Conversation, ConversationParticipant, Message, MessageReadStatus


class ChatRepository:
    """Data access layer for chat operations."""

    @staticmethod
    @transaction.atomic
    def create_conversation(created_by, participant_ids):
        """Create a conversation with a list of participants (excluding creator)."""
        conversation = Conversation.objects.create(created_by=created_by)
        participants = [ConversationParticipant(
            conversation=conversation, user=created_by,
        )]
        for pid in participant_ids:
            participants.append(
                ConversationParticipant(conversation=conversation, user_id=pid),
            )
        ConversationParticipant.objects.bulk_create(participants)
        return conversation

    @staticmethod
    def get_conversation(conversation_id):
        return Conversation.objects.filter(id=conversation_id).first()

    @staticmethod
    def get_user_conversations(user):
        return Conversation.objects.filter(
            participants__user=user,
            is_active=True,
        ).select_related(
            "created_by",
        ).prefetch_related(
            Prefetch(
                "participants",
                queryset=ConversationParticipant.objects.select_related("user"),
            ),
            Prefetch(
                "messages",
                queryset=Message.objects.order_by("-created_at").select_related("sender"),
                to_attr="latest_message",
            ),
        ).annotate(
            unread=Count(
                "messages",
                filter=Q(
                    messages__read_by__isnull=True,
                ) & ~Q(messages__sender=user),
            ),
        ).order_by("-updated_at")

    @staticmethod
    def create_message(conversation, sender, message_type, content, attachment=None, metadata=None):
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            message_type=message_type,
            content=content,
            attachment=attachment,
            metadata=metadata or {},
        )
        Conversation.objects.filter(id=conversation.id).update(
            updated_at=timezone.now(),
        )
        return message

    @staticmethod
    def get_messages(conversation, before=None, limit=50):
        qs = Message.objects.filter(
            conversation=conversation,
        ).select_related("sender").order_by("-created_at")
        if before:
            qs = qs.filter(created_at__lt=before)
        return list(qs[:limit])

    @staticmethod
    def mark_message_read(message, user):
        MessageReadStatus.objects.get_or_create(
            message=message,
            user=user,
            defaults={"read_at": timezone.now()},
        )

    @staticmethod
    def mark_conversation_read(conversation, user):
        unread = Message.objects.filter(
            conversation=conversation,
        ).exclude(
            sender=user,
        ).exclude(
            read_by__user=user,
        )
        read_statuses = [
            MessageReadStatus(message=m, user=user, read_at=timezone.now())
            for m in unread
        ]
        MessageReadStatus.objects.bulk_create(
            read_statuses, ignore_conflicts=True,
        )

    @staticmethod
    def unread_count(user):
        return Message.objects.filter(
            ~Q(sender=user),
            conversation__participants__user=user,
            conversation__is_active=True,
        ).exclude(
            read_by__user=user,
        ).count()

    @staticmethod
    def participant_exists(conversation, user) -> bool:
        return ConversationParticipant.objects.filter(
            conversation=conversation,
            user=user,
        ).exists()

    @staticmethod
    def participant_exists_by_ids(conversation_id, user_id) -> bool:
        return ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user_id=user_id,
        ).exists()

    @staticmethod
    def get_participants(conversation):
        return ConversationParticipant.objects.filter(
            conversation=conversation,
        ).select_related("user")

    @staticmethod
    def user_has_match_with(user_a, user_b) -> bool:
        """Check if there's at least one MatchScore linking these two users."""
        from apps.matching.models import MatchScore
        return MatchScore.objects.filter(
            Q(investor=user_a, startup__owner=user_b)
            | Q(investor=user_b, startup__owner=user_a),
        ).exists()
