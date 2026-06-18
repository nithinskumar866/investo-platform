from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "recipient_email", "notification_type", "is_read", "created_at"]
    list_filter = ["notification_type", "is_read", "created_at"]
    search_fields = ["title", "message", "recipient__email"]
    readonly_fields = ["created_at", "read_at"]
    raw_id_fields = ["recipient", "actor"]

    def recipient_email(self, obj):
        return obj.recipient.email
    recipient_email.short_description = "Recipient"
    recipient_email.admin_order_field = "recipient__email"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user_email", "in_app_enabled", "email_enabled", "push_enabled"]
    list_filter = ["in_app_enabled", "email_enabled", "push_enabled"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"
