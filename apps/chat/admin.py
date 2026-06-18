from django.contrib import admin

from .models import Conversation, ConversationParticipant, Message, MessageReadStatus


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ["id", "created_by_email", "is_active", "created_at", "updated_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["created_by__email"]

    def created_by_email(self, obj):
        return obj.created_by.email
    created_by_email.short_description = "Created By"
    created_by_email.admin_order_field = "created_by__email"


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ["conversation_id", "user_email", "joined_at"]
    search_fields = ["user__email"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation_id", "sender_email", "message_type", "truncated_content", "created_at"]
    list_filter = ["message_type", "created_at"]
    search_fields = ["sender__email", "content"]

    def sender_email(self, obj):
        return obj.sender.email
    sender_email.short_description = "Sender"
    sender_email.admin_order_field = "sender__email"

    def truncated_content(self, obj):
        return obj.content[:80] if obj.content else ""
    truncated_content.short_description = "Content"


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    list_display = ["message_id", "user_email", "read_at"]
    search_fields = ["user__email"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"
