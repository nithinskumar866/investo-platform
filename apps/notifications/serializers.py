from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "message",
            "notification_type",
            "is_read",
            "related_object_id",
            "related_object_type",
            "action_url",
            "created_at",
            "read_at",
        ]
        read_only_fields = fields