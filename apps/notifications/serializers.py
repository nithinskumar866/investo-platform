from rest_framework import serializers

from .models import Notification, NotificationPreference


class ActorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    role = serializers.CharField()


class NotificationListSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    actor_info = serializers.SerializerMethodField()
    relative_time = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id", "notification_type", "category", "title", "message",
            "data", "is_read", "actor", "actor_info",
            "relative_time", "created_at", "read_at",
        ]

    def get_category(self, obj):
        return obj.category()

    def get_actor_info(self, obj):
        if not obj.actor_id:
            return None
        return {
            "id": obj.actor_id,
            "email": obj.actor.email,
            "role": getattr(obj.actor, "role", None),
        }

    def get_relative_time(self, obj):
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        if delta.days > 0:
            return f"{delta.days}d ago"
        if delta.seconds >= 3600:
            return f"{delta.seconds // 3600}h ago"
        if delta.seconds >= 60:
            return f"{delta.seconds // 60}m ago"
        return "just now"


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "email_enabled", "push_enabled", "in_app_enabled",
            "matching_notifications", "investment_notifications",
            "chat_notifications", "document_notifications",
            "marketing_notifications",
        ]


class MarkReadSerializer(serializers.Serializer):
    notification_id = serializers.IntegerField(required=False)


class UnreadCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class NotificationAnalyticsSerializer(serializers.Serializer):
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_rate = serializers.FloatField()
    read_count = serializers.IntegerField()
    by_type = serializers.ListField()
    volume_last_7_days = serializers.IntegerField()


class NotificationCursorPaginatedResponse(serializers.Serializer):
    results = NotificationListSerializer(many=True)
    cursor = serializers.DateTimeField(allow_null=True)
    has_more = serializers.BooleanField()
