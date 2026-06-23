from django.contrib import admin

from .models import AuditLog, SupportMessage, SupportTicket


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action_type", "actor", "target_repr", "description", "created_at"]
    list_filter = ["action_type", "created_at"]
    search_fields = ["description", "target_repr", "actor__email"]
    date_hierarchy = "created_at"


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ["subject", "user", "status", "priority", "category", "assigned_to", "updated_at"]
    list_filter = ["status", "priority", "category"]
    search_fields = ["subject", "user__email"]


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ["ticket", "sender", "is_internal", "created_at"]
    list_filter = ["is_internal"]
    search_fields = ["content", "sender__email"]
