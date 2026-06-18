from django.db import transaction
from django.db.models import Count, Q, OuterRef, Subquery, Exists
from django.utils import timezone

from .models import ActivityFeed, FeedReaction, FeedBookmark, FeedComment


class ActivityFeedRepository:
    """Data access layer for feed operations."""

    # ── Create ────────────────────────────────────────────────────

    @staticmethod
    def create_activity(actor, activity_type, title, description="",
                        startup=None, investor=None,
                        target_object_id=None, target_object_type="",
                        metadata=None, visibility=ActivityFeed.Visibility.PUBLIC):
        return ActivityFeed.objects.create(
            actor=actor,
            activity_type=activity_type,
            startup=startup,
            investor=investor,
            target_object_id=target_object_id,
            target_object_type=target_object_type,
            title=title,
            description=description,
            metadata=metadata or {},
            visibility=visibility,
        )

    @staticmethod
    def bulk_create_activities(activities_data):
        objs = [
            ActivityFeed(
                actor=ad["actor"],
                activity_type=ad["activity_type"],
                startup=ad.get("startup"),
                investor=ad.get("investor"),
                target_object_id=ad.get("target_object_id"),
                target_object_type=ad.get("target_object_type", ""),
                title=ad["title"],
                description=ad.get("description", ""),
                metadata=ad.get("metadata", {}),
                visibility=ad.get("visibility", ActivityFeed.Visibility.PUBLIC),
            )
            for ad in activities_data
        ]
        return ActivityFeed.objects.bulk_create(objs)

    # ── Read ──────────────────────────────────────────────────────

    @staticmethod
    def get_feed(user, cursor=None, limit=20, activity_type=None):
        qs = ActivityFeed.objects.filter(
            visibility=ActivityFeed.Visibility.PUBLIC,
        ).select_related(
            "actor", "startup", "investor",
        ).annotate(
            reaction_count=Count("reactions", distinct=True),
            comment_count=Count("comments", distinct=True),
            bookmark_count=Count("bookmarks", distinct=True),
        ).order_by("-created_at")

        if activity_type:
            qs = qs.filter(activity_type=activity_type)

        if cursor:
            qs = qs.filter(created_at__lt=cursor)

        results = list(qs[:limit])
        has_more = qs[limit:].exists() if len(results) == limit else False
        return results, has_more

    @staticmethod
    def get_feed_by_ids(feed_ids):
        return ActivityFeed.objects.filter(
            id__in=feed_ids,
        ).select_related(
            "actor", "startup", "investor",
        ).annotate(
            reaction_count=Count("reactions", distinct=True),
            comment_count=Count("comments", distinct=True),
            bookmark_count=Count("bookmarks", distinct=True),
        )

    @staticmethod
    def get_trending_feed(days=3, limit=20):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return ActivityFeed.objects.filter(
            created_at__gte=cutoff,
            visibility=ActivityFeed.Visibility.PUBLIC,
        ).select_related(
            "actor", "startup", "investor",
        ).annotate(
            reaction_count=Count("reactions", distinct=True),
            comment_count=Count("comments", distinct=True),
            bookmark_count=Count("bookmarks", distinct=True),
            engagement_score=(
                Count("reactions") * 2 + Count("comments") * 3 + Count("bookmarks") * 1
            ),
        ).order_by("-engagement_score", "-created_at")[:limit]

    @staticmethod
    def get_single_feed(feed_id):
        return ActivityFeed.objects.filter(
            id=feed_id,
        ).select_related(
            "actor", "startup", "investor",
        ).annotate(
            reaction_count=Count("reactions", distinct=True),
            comment_count=Count("comments", distinct=True),
            bookmark_count=Count("bookmarks", distinct=True),
        ).first()

    @staticmethod
    def get_feed_by_startup(startup_id, limit=20):
        return ActivityFeed.objects.filter(
            startup_id=startup_id,
            visibility=ActivityFeed.Visibility.PUBLIC,
        ).select_related("actor").order_by("-created_at")[:limit]

    # ── Reactions ─────────────────────────────────────────────────

    @staticmethod
    def create_reaction(user, feed_item, reaction_type="like"):
        reaction, created = FeedReaction.objects.get_or_create(
            user=user,
            feed_item=feed_item,
            reaction_type=reaction_type,
        )
        return reaction, created

    @staticmethod
    def remove_reaction(user, feed_item, reaction_type=None):
        qs = FeedReaction.objects.filter(user=user, feed_item=feed_item)
        if reaction_type:
            qs = qs.filter(reaction_type=reaction_type)
        deleted, _ = qs.delete()
        return deleted > 0

    @staticmethod
    def get_reactions(feed_item):
        return FeedReaction.objects.filter(
            feed_item=feed_item,
        ).select_related("user")

    @staticmethod
    def user_reaction(user, feed_item):
        return FeedReaction.objects.filter(
            user=user, feed_item=feed_item,
        ).first()

    # ── Bookmarks ─────────────────────────────────────────────────

    @staticmethod
    def create_bookmark(user, feed_item):
        bookmark, created = FeedBookmark.objects.get_or_create(
            user=user, feed_item=feed_item,
        )
        return bookmark, created

    @staticmethod
    def remove_bookmark(user, feed_item):
        deleted, _ = FeedBookmark.objects.filter(
            user=user, feed_item=feed_item,
        ).delete()
        return deleted > 0

    @staticmethod
    def get_bookmarks(user, cursor=None, limit=20):
        qs = FeedBookmark.objects.filter(
            user=user,
        ).select_related(
            "feed_item", "feed_item__actor",
            "feed_item__startup", "feed_item__investor",
        ).order_by("-created_at")

        if cursor:
            qs = qs.filter(created_at__lt=cursor)

        results = list(qs[:limit])
        has_more = qs[limit:].exists() if len(results) == limit else False
        return results, has_more

    # ── Comments ──────────────────────────────────────────────────

    @staticmethod
    def create_comment(user, feed_item, content, parent_comment=None):
        return FeedComment.objects.create(
            user=user,
            feed_item=feed_item,
            content=content,
            parent_comment=parent_comment,
        )

    @staticmethod
    def delete_comment(comment_id, user):
        deleted, _ = FeedComment.objects.filter(
            id=comment_id, user=user,
        ).delete()
        return deleted > 0

    @staticmethod
    def get_comments(feed_item):
        return FeedComment.objects.filter(
            feed_item=feed_item,
        ).select_related("user", "parent_comment").order_by("created_at")

    # ── Discovery ─────────────────────────────────────────────────

    @staticmethod
    def get_discovered_startups(limit=20):
        from apps.startups.models import Startup
        return Startup.objects.filter(
            is_visible=True,
        ).select_related(
            "owner", "metrics",
        ).annotate(
            feed_mentions=Count("feed_activities"),
        ).order_by("-feed_mentions", "-created_at")[:limit]

    @staticmethod
    def get_trending_startups(limit=10):
        from apps.startups.models import Startup
        cutoff = timezone.now() - timezone.timedelta(days=14)
        return Startup.objects.filter(
            is_visible=True,
            created_at__gte=cutoff,
        ).annotate(
            feed_count=Count("feed_activities"),
        ).order_by("-feed_count")[:limit]

    @staticmethod
    def get_recently_funded(limit=10):
        from apps.startups.models import Startup
        return Startup.objects.filter(
            status="funded",
        ).select_related("owner").order_by("-updated_at")[:limit]

    @staticmethod
    def get_active_investors(limit=10):
        cutoff = timezone.now() - timezone.timedelta(days=30)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(
            role="investor",
            feed_activities__created_at__gte=cutoff,
        ).annotate(
            activity_count=Count("feed_activities"),
        ).order_by("-activity_count").distinct()[:limit]

    @staticmethod
    def get_new_founders(limit=10):
        cutoff = timezone.now() - timezone.timedelta(days=30)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(
            role="entrepreneur",
            date_joined__gte=cutoff,
        ).order_by("-date_joined")[:limit]

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics():
        total = ActivityFeed.objects.count()
        reaction_total = FeedReaction.objects.count()
        comment_total = FeedComment.objects.count()
        bookmark_total = FeedBookmark.objects.count()

        by_type = list(
            ActivityFeed.objects.values("activity_type").annotate(
                count=Count("id"),
                reactions=Count("reactions"),
                comments=Count("comments"),
            ).order_by("-count")
        )

        return {
            "total_activities": total,
            "total_reactions": reaction_total,
            "total_comments": comment_total,
            "total_bookmarks": bookmark_total,
            "engagement_rate": round(
                (reaction_total + comment_total + bookmark_total) / total * 100, 1,
            ) if total else 0.0,
            "by_type": by_type,
            "last_7_days": ActivityFeed.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7),
            ).count(),
        }
