from rest_framework import serializers

from .models import Conversation, Message, MessageReadStatus


class ParticipantSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    avatar = serializers.SerializerMethodField()
    role = serializers.CharField()

    def get_avatar(self, obj):
        try:
            return obj.user.avatar.url if obj.user.avatar else None
        except Exception:
            return None


class MessageSerializer(serializers.ModelSerializer):
    sender = ParticipantSerializer(source="sender.participant_set.first", read_only=True)
    read_by = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "message_type",
            "content",
            "attachment",
            "metadata",
            "edited_at",
            "created_at",
            "read_by",
        ]
        read_only_fields = ["id", "sender", "created_at", "edited_at"]

    def get_read_by(self, obj):
        return [
            {"user_id": r.user_id, "read_at": r.read_at}
            for r in obj.read_by.all()
        ]


class MessageCreateSerializer(serializers.Serializer):
    message_type = serializers.ChoiceField(
        choices=["text", "file", "image"],
        default="text",
    )
    content = serializers.CharField(required=False, allow_blank=True, default="")
    attachment = serializers.FileField(required=False, allow_null=True)
    metadata = serializers.JSONField(required=False, default=dict)

    def validate(self, attrs):
        if not attrs.get("content") and not attrs.get("attachment"):
            raise serializers.ValidationError(
                "Either content or attachment is required",
            )
        return attrs


class ConversationListSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()
    unread = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "other_participant",
            "latest_message",
            "unread",
            "updated_at",
            "created_at",
        ]

    def get_other_participant(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        participants = obj.participants.all()
        other = next(
            (p for p in participants if p.user_id != request.user.id),
            None,
        )
        if not other:
            return None
        return {
            "id": other.user.id,
            "first_name": other.user.first_name,
            "last_name": other.user.last_name,
            "avatar": other.user.avatar.url if other.user.avatar else None,
            "role": other.user.role,
        }

    def get_latest_message(self, obj):
        msgs = getattr(obj, "latest_message", None)
        if msgs:
            msg = msgs[0]
            return {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "message_type": msg.message_type,
                "content": msg.content[:100] if msg.content else "",
                "created_at": msg.created_at,
            }
        return None


class ConversationDetailSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "created_by",
            "participants",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_participants(self, obj):
        return [
            {
                "id": p.user.id,
                "first_name": p.user.first_name,
                "last_name": p.user.last_name,
                "avatar": p.user.avatar.url if p.user.avatar else None,
                "role": p.user.role,
            }
            for p in obj.participants.all()
        ]

    def get_created_by(self, obj):
        return {
            "id": obj.created_by.id,
            "first_name": obj.created_by.first_name,
            "last_name": obj.created_by.last_name,
        }


class CreateConversationSerializer(serializers.Serializer):
    participant_id = serializers.IntegerField()


class UnreadCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()
