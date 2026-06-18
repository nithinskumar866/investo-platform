from django.contrib import admin

from .models import InvestmentOpportunity, InvestmentActivity


@admin.register(InvestmentOpportunity)
class InvestmentOpportunityAdmin(admin.ModelAdmin):
    list_display = [
        "id", "investor_email", "startup_name", "amount_requested",
        "amount_offered", "status", "created_at",
    ]
    search_fields = ["investor__email", "startup__name", "notes"]
    list_filter = ["status", "created_at"]

    def investor_email(self, obj):
        return obj.investor.email
    investor_email.short_description = "Investor"
    investor_email.admin_order_field = "investor__email"

    def startup_name(self, obj):
        return obj.startup.name
    startup_name.short_description = "Startup"
    startup_name.admin_order_field = "startup__name"


@admin.register(InvestmentActivity)
class InvestmentActivityAdmin(admin.ModelAdmin):
    list_display = ["id", "opportunity_id", "actor_email", "action", "timestamp"]
    search_fields = ["actor__email", "action"]
    list_filter = ["action", "timestamp"]
    readonly_fields = ["timestamp"]

    def actor_email(self, obj):
        return obj.actor.email if obj.actor else "system"
    actor_email.short_description = "Actor"
