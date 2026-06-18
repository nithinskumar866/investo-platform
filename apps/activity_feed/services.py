import logging

from apps.common.exceptions import ApplicationError

from .models import ActivityFeed, FeedReaction, FeedComment
from .repositories import ActivityFeedRepository

logger = logging.getLogger(__name__)


class ActivityFeedService:
    """Business logic for feed operations."""

    # ── Feed generation ───────────────────────────────────────────

    @classmethod
    def publish_activity(cls, actor, activity_type, title, description="",
                         startup=None, investor=None,
                         target_object_id=None, target_object_type="",
                         metadata=None):
        """Publish an activity to the feed. Called by other modules."""
        activity = ActivityFeedRepository.create_activity(
            actor=actor,
            activity_type=activity_type,
            title=title,
            description=description,
            startup=startup,
            investor=investor,
            target_object_id=target_object_id,
            target_object_type=target_object_type,
            metadata=metadata,
        )
        cls._broadcast(activity)
        return activity

    # ── Feed retrieval ────────────────────────────────────────────

    @staticmethod
    def get_feed(user, cursor=None, limit=20, activity_type=None):
        return ActivityFeedRepository.get_feed(
            user, cursor=cursor, limit=limit, activity_type=activity_type,
        )

    @staticmethod
    def get_trending(user, limit=20):
        return ActivityFeedRepository.get_trending_feed(limit=limit)

    @staticmethod
    def get_single(feed_id, user):
        item = ActivityFeedRepository.get_single_feed(feed_id)
        if not item:
            raise ApplicationError("Feed item not found", "NOT_FOUND", 404)
        return item

    @staticmethod
    def get_by_startup(startup_id):
        return ActivityFeedRepository.get_feed_by_startup(startup_id)

    # ── Reactions ─────────────────────────────────────────────────

    @staticmethod
    def react(feed_item_id, user, reaction_type="like"):
        feed_item = ActivityFeed.objects.filter(id=feed_item_id).first()
        if not feed_item:
            raise ApplicationError("Feed item not found", "NOT_FOUND", 404)
        reaction, created = ActivityFeedRepository.create_reaction(
            user, feed_item, reaction_type,
        )
        return reaction, created

    @staticmethod
    def unreact(feed_item_id, user, reaction_type=None):
        feed_item = ActivityFeed.objects.filter(id=feed_item_id).first()
        if not feed_item:
            raise ApplicationError("Feed item not found", "NOT_FOUND", 404)
        return ActivityFeedRepository.remove_reaction(user, feed_item, reaction_type)

    # ── Comments ──────────────────────────────────────────────────

    @staticmethod
    def comment(feed_item_id, user, content, parent_comment_id=None):
        feed_item = ActivityFeed.objects.filter(id=feed_item_id).first()
        if not feed_item:
            raise ApplicationError("Feed item not found", "NOT_FOUND", 404)

        parent = None
        if parent_comment_id:
            parent = FeedComment.objects.filter(id=parent_comment_id).first()
            if not parent or parent.feed_item_id != feed_item.id:
                raise ApplicationError("Parent comment not found", "NOT_FOUND", 404)

        comment = ActivityFeedRepository.create_comment(
            user, feed_item, content, parent,
        )
        return comment

    @staticmethod
    def delete_comment(comment_id, user):
        return ActivityFeedRepository.delete_comment(comment_id, user)

    @staticmethod
    def get_comments(feed_item_id):
        feed_item = ActivityFeed.objects.filter(id=feed_item_id).first()
        if not feed_item:
            raise ApplicationError("Feed item not found", "NOT_FOUND", 404)
        return ActivityFeedRepository.get_comments(feed_item)

    # ── Bookmarks ─────────────────────────────────────────────────

    @staticmethod
    def bookmark(feed_item_id, user):
        feed_item = ActivityFeed.objects.filter(id=feed_item_id).first()
        if not feed_item:
            raise ApplicationError("Feed item not found", "NOT_FOUND", 404)
        bookmark, created = ActivityFeedRepository.create_bookmark(user, feed_item)
        return bookmark, created

    @staticmethod
    def unbookmark(feed_item_id, user):
        feed_item = ActivityFeed.objects.filter(id=feed_item_id).first()
        if not feed_item:
            raise ApplicationError("Feed item not found", "NOT_FOUND", 404)
        return ActivityFeedRepository.remove_bookmark(user, feed_item)

    @staticmethod
    def get_bookmarks(user, cursor=None, limit=20):
        return ActivityFeedRepository.get_bookmarks(user, cursor=cursor, limit=limit)

    # ── Discovery ─────────────────────────────────────────────────

    @staticmethod
    def discover() -> dict:
        return {
            "trending_startups": ActivityFeedRepository.get_trending_startups(),
            "recently_funded": ActivityFeedRepository.get_recently_funded(),
            "active_investors": ActivityFeedRepository.get_active_investors(),
            "new_founders": ActivityFeedRepository.get_new_founders(),
            "discovered_startups": ActivityFeedRepository.get_discovered_startups(),
        }

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics():
        return ActivityFeedRepository.get_analytics()

    # ── WebSocket broadcast via Channels ─────────────────────────

    @staticmethod
    def _broadcast(activity):
        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_feed(
            event_type="feed_created",
            payload={
                "activity": {
                    "id": activity.id,
                    "type": activity.activity_type,
                    "title": activity.title,
                    "actor_email": activity.actor.email,
                    "created_at": activity.created_at.isoformat(),
                },
            },
        )



