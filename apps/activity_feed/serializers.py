from rest_framework import serializers

from .models import ActivityFeed, FeedReaction, FeedBookmark, FeedComment


class ActorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    role = serializers.CharField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        first = getattr(obj, "first_name", "")
        last = getattr(obj, "last_name", "")
        return f"{first} {last}".strip() or obj.email


class FeedReactionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = FeedReaction
        fields = ["id", "user", "user_email", "reaction_type", "created_at"]
        read_only_fields = ["user", "created_at"]


class FeedCommentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = FeedComment
        fields = [
            "id", "user", "user_email", "user_name",
            "content", "parent_comment", "replies",
            "created_at", "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]

    def get_user_name(self, obj):
        first = getattr(obj.user, "first_name", "")
        last = getattr(obj.user, "last_name", "")
        return f"{first} {last}".strip() or obj.user.email

    def get_replies(self, obj):
        if hasattr(obj, "_replies"):
            return FeedCommentSerializer(obj._replies, many=True).data
        replies = FeedComment.objects.filter(parent_comment=obj).select_related("user")
        return FeedCommentSerializer(replies, many=True).data


class FeedBookmarkSerializer(serializers.ModelSerializer):
    feed_item_id = serializers.IntegerField(source="feed_item.id", read_only=True)

    class Meta:
        model = FeedBookmark
        fields = ["id", "feed_item", "feed_item_id", "created_at"]
        read_only_fields = ["user", "created_at"]


class FeedItemSerializer(serializers.ModelSerializer):
    actor_data = serializers.SerializerMethodField()
    startup_name = serializers.CharField(
        source="startup.name", read_only=True, default=None,
    )
    investor_email = serializers.EmailField(
        source="investor.email", read_only=True, default=None,
    )
    reaction_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    bookmark_count = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    user_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = ActivityFeed
        fields = [
            "id", "activity_type", "title", "description",
            "actor", "actor_data",
            "startup", "startup_name",
            "investor", "investor_email",
            "target_object_id", "target_object_type",
            "metadata",
            "reaction_count", "comment_count", "bookmark_count",
            "user_reaction", "user_bookmarked",
            "visibility", "created_at",
        ]
        read_only_fields = fields

    def get_reaction_count(self, obj):
        if hasattr(obj, "_reaction_count"):
            return obj._reaction_count
        return obj.reactions.count()

    def get_comment_count(self, obj):
        if hasattr(obj, "_comment_count"):
            return obj._comment_count
        return obj.comments.count()

    def get_bookmark_count(self, obj):
        if hasattr(obj, "_bookmark_count"):
            return obj._bookmark_count
        return obj.bookmarks.count()

    def get_actor_data(self, obj):
        return ActorSerializer(obj.actor).data

    def get_user_reaction(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            reaction = FeedReaction.objects.filter(
                user=request.user, feed_item=obj,
            ).first()
            if reaction:
                return FeedReactionSerializer(reaction).data
        return None

    def get_user_bookmarked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return FeedBookmark.objects.filter(
                user=request.user, feed_item=obj,
            ).exists()
        return False


class FeedItemDetailSerializer(FeedItemSerializer):
    comments = serializers.SerializerMethodField()
    reactions = serializers.SerializerMethodField()

    class Meta(FeedItemSerializer.Meta):
        fields = FeedItemSerializer.Meta.fields + ["comments", "reactions"]

    def get_comments(self, obj):
        comments = FeedComment.objects.filter(
            feed_item=obj, parent_comment__isnull=True,
        ).select_related("user")
        return FeedCommentSerializer(comments, many=True).data

    def get_reactions(self, obj):
        reactions = FeedReaction.objects.filter(
            feed_item=obj,
        ).select_related("user")
        return FeedReactionSerializer(reactions, many=True).data


class ReactSerializer(serializers.Serializer):
    reaction_type = serializers.ChoiceField(
        choices=["like", "celebrate", "support", "insightful", "curious"],
        default="like",
    )


class CommentSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=2000)
    parent_comment_id = serializers.IntegerField(required=False, allow_null=True)


class FeedAnalyticsSerializer(serializers.Serializer):
    total_activities = serializers.IntegerField()
    total_reactions = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    total_bookmarks = serializers.IntegerField()
    engagement_rate = serializers.FloatField()
    by_type = serializers.ListField()
    last_7_days = serializers.IntegerField()
