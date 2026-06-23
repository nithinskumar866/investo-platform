from rest_framework import serializers

from .models import AuditLog, SupportMessage, SupportTicket


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "actor", "actor_email", "actor_name",
            "action_type", "target_type", "target_id", "target_repr",
            "description", "metadata", "ip_address", "created_at",
        ]

    @staticmethod
    def get_actor_name(obj):
        if not obj.actor:
            return ""
        return f"{obj.actor.first_name} {obj.actor.last_name}".strip() or obj.actor.email


class SupportTicketListSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True, default="")
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = [
            "id", "user", "user_email", "user_name",
            "subject", "category", "priority", "status",
            "assigned_to", "assigned_to_email",
            "message_count", "created_at", "updated_at",
        ]

    @staticmethod
    def get_user_name(obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

    @staticmethod
    def get_message_count(obj):
        return obj.messages.count()


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    assigned_to_email = serializers.EmailField(source="assigned_to.email", read_only=True, default="")

    class Meta:
        model = SupportTicket
        fields = [
            "id", "user", "user_email", "user_name",
            "subject", "description", "category", "priority",
            "status", "assigned_to", "assigned_to_email",
            "metadata", "created_at", "updated_at",
        ]

    @staticmethod
    def get_user_name(obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class SupportMessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source="sender.email", read_only=True)
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = SupportMessage
        fields = [
            "id", "ticket", "sender", "sender_email", "sender_name",
            "content", "is_internal", "attachments", "created_at",
        ]
        read_only_fields = ["id", "sender", "created_at"]

    @staticmethod
    def get_sender_name(obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email


class SupportTicketCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    category = serializers.ChoiceField(
        choices=SupportTicket.Category.choices, default="other",
    )
    priority = serializers.ChoiceField(
        choices=SupportTicket.Priority.choices, default="medium",
    )


class SupportTicketUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=SupportTicket.Status.choices, required=False)
    priority = serializers.ChoiceField(choices=SupportTicket.Priority.choices, required=False)
    category = serializers.ChoiceField(choices=SupportTicket.Category.choices, required=False)
    assigned_to = serializers.IntegerField(required=False, allow_null=True)


class SupportMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
    is_internal = serializers.BooleanField(default=False)
    attachments = serializers.JSONField(default=list, required=False)


class UserActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject", "archive", "flag"])
    reason = serializers.CharField(required=False, allow_blank=True)


class UserSearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False, default="")
    role = serializers.ChoiceField(
        choices=["entrepreneur", "investor", "mentor", "talent", "admin"],
        required=False,
    )
    status = serializers.ChoiceField(
        choices=["active", "suspended", "all"], required=False,
    )
    page = serializers.IntegerField(default=1)


class StartupFilterSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["draft", "active", "funded", "closed"], required=False,
    )
    verified = serializers.BooleanField(required=False, allow_null=True)
    page = serializers.IntegerField(default=1)


class AuditLogFilterSerializer(serializers.Serializer):
    action_type = serializers.CharField(required=False)
    actor_id = serializers.IntegerField(required=False)
    target_type = serializers.CharField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    page = serializers.IntegerField(default=1)
