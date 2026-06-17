from django.contrib import admin

from .models import InvestorPreference, MatchScore, InteractionEvent


@admin.register(InvestorPreference)
class InvestorPreferenceAdmin(admin.ModelAdmin):
    list_display = ["user_email", "risk_appetite", "min_ticket_size", "max_ticket_size", "is_active"]
    search_fields = ["user__email"]
    list_filter = ["risk_appetite", "is_active"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"


@admin.register(MatchScore)
class MatchScoreAdmin(admin.ModelAdmin):
    list_display = ["investor_email", "startup_name", "score", "is_viewed", "is_bookmarked", "is_contacted"]
    search_fields = ["investor__email", "startup__name"]
    list_filter = ["is_viewed", "is_bookmarked", "is_contacted", "is_ignored"]

    def investor_email(self, obj):
        return obj.investor.email
    investor_email.short_description = "Investor"
    investor_email.admin_order_field = "investor__email"

    def startup_name(self, obj):
        return obj.startup.name
    startup_name.short_description = "Startup"
    startup_name.admin_order_field = "startup__name"


@admin.register(InteractionEvent)
class InteractionEventAdmin(admin.ModelAdmin):
    list_display = ["user_email", "event_type", "startup_name", "created_at"]
    search_fields = ["user__email", "startup__name"]
    list_filter = ["event_type", "created_at"]
    readonly_fields = ["created_at"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"

    def startup_name(self, obj):
        return obj.startup.name if obj.startup else "-"
    startup_name.short_description = "Startup"
