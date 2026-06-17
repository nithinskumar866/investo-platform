from django.contrib import admin

from .models import Startup, StartupTeamMember, StartupSocialLink, StartupDocument, StartupFundingRound, StartupMetric


class StartupTeamMemberInline(admin.TabularInline):
    model = StartupTeamMember
    extra = 1


class StartupSocialLinkInline(admin.TabularInline):
    model = StartupSocialLink
    extra = 1


class StartupDocumentInline(admin.TabularInline):
    model = StartupDocument
    extra = 1


class StartupFundingRoundInline(admin.TabularInline):
    model = StartupFundingRound
    extra = 1


@admin.register(Startup)
class StartupAdmin(admin.ModelAdmin):
    list_display = [
        "name", "owner_email", "industry", "stage", "status",
        "is_verified", "is_visible", "view_count", "created_at",
    ]
    list_filter = ["industry", "stage", "status", "is_verified", "is_visible"]
    search_fields = ["name", "description", "owner__email"]
    readonly_fields = ["view_count", "bookmark_count", "created_at", "updated_at"]
    inlines = [
        StartupTeamMemberInline, StartupSocialLinkInline,
        StartupDocumentInline, StartupFundingRoundInline,
    ]

    def owner_email(self, obj):
        return obj.owner.email
    owner_email.short_description = "Owner"
    owner_email.admin_order_field = "owner__email"


@admin.register(StartupMetric)
class StartupMetricAdmin(admin.ModelAdmin):
    list_display = ["startup_name", "monthly_revenue", "annual_revenue", "monthly_active_users"]
    search_fields = ["startup__name"]

    def startup_name(self, obj):
        return obj.startup.name
    startup_name.short_description = "Startup"
    startup_name.admin_order_field = "startup__name"
