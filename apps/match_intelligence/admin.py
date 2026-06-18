from django.contrib import admin

from .models import MatchInsight, MatchFeedback


@admin.register(MatchInsight)
class MatchInsightAdmin(admin.ModelAdmin):
    list_display = ["match", "summary_preview", "generated_at"]
    search_fields = ["match__startup__name", "summary"]
    raw_id_fields = ["match"]
    readonly_fields = ["generated_at"]

    def summary_preview(self, obj):
        return obj.summary[:80] + "..." if len(obj.summary) > 80 else obj.summary
    summary_preview.short_description = "Summary"


@admin.register(MatchFeedback)
class MatchFeedbackAdmin(admin.ModelAdmin):
    list_display = ["user_email", "match", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["user__email", "match__startup__name"]
    raw_id_fields = ["user", "match"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
