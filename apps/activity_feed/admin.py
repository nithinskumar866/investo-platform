from django.contrib import admin

from .models import ActivityFeed, FeedReaction, FeedBookmark, FeedComment


@admin.register(ActivityFeed)
class ActivityFeedAdmin(admin.ModelAdmin):
    list_display = ["actor_email", "activity_type", "title_short", "visibility", "created_at"]
    list_filter = ["activity_type", "visibility", "created_at"]
    search_fields = ["title", "description", "actor__email"]
    raw_id_fields = ["actor", "startup", "investor"]
    readonly_fields = ["created_at"]

    def actor_email(self, obj):
        return obj.actor.email
    actor_email.short_description = "Actor"

    def title_short(self, obj):
        return obj.title[:60] + "..." if len(obj.title) > 60 else obj.title
    title_short.short_description = "Title"


@admin.register(FeedReaction)
class FeedReactionAdmin(admin.ModelAdmin):
    list_display = ["user_email", "feed_item", "reaction_type", "created_at"]
    list_filter = ["reaction_type"]
    search_fields = ["user__email"]
    raw_id_fields = ["user", "feed_item"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"


@admin.register(FeedBookmark)
class FeedBookmarkAdmin(admin.ModelAdmin):
    list_display = ["user_email", "feed_item", "created_at"]
    search_fields = ["user__email"]
    raw_id_fields = ["user", "feed_item"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"


@admin.register(FeedComment)
class FeedCommentAdmin(admin.ModelAdmin):
    list_display = ["user_email", "feed_item", "content_short", "created_at"]
    search_fields = ["content", "user__email"]
    raw_id_fields = ["user", "feed_item", "parent_comment"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User"

    def content_short(self, obj):
        return obj.content[:60] + "..." if len(obj.content) > 60 else obj.content
    content_short.short_description = "Content"
