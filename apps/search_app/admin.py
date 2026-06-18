from django.contrib import admin

from .models import SavedSearch, SearchHistory, SearchClickEvent


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ["name", "user_email", "search_type", "updated_at"]
    list_filter = ["search_type"]
    search_fields = ["name", "user__email"]
    raw_id_fields = ["user"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ["user_email", "query", "search_type", "results_count", "created_at"]
    list_filter = ["search_type", "created_at"]
    search_fields = ["query", "user__email"]
    raw_id_fields = ["user"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"


@admin.register(SearchClickEvent)
class SearchClickEventAdmin(admin.ModelAdmin):
    list_display = ["user_email", "result_type", "result_id", "query", "created_at"]
    search_fields = ["user__email", "query"]
    raw_id_fields = ["user"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"
