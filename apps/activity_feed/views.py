from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.common.exceptions import ApplicationError

from .serializers import (
    FeedAnalyticsSerializer,
    FeedItemDetailSerializer,
    FeedItemSerializer,
    CommentSerializer,
    ReactSerializer,
)
from .services import ActivityFeedService


class FeedViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cursor = request.query_params.get("cursor")
        activity_type = request.query_params.get("type")
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            limit = 20

        items, has_more = ActivityFeedService.get_feed(
            request.user, cursor=cursor, limit=limit,
            activity_type=activity_type,
        )
        serializer = FeedItemSerializer(
            items, many=True, context={"request": request},
        )
        next_cursor = items[-1].created_at.isoformat() if items else None
        return Response({
            "results": serializer.data,
            "cursor": next_cursor if has_more else None,
            "has_more": has_more,
        })

    @action(detail=False, methods=["get"])
    def trending(self, request):
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            limit = 20

        items = ActivityFeedService.get_trending(request.user, limit=limit)
        serializer = FeedItemSerializer(
            items, many=True, context={"request": request},
        )
        return Response({"results": serializer.data})

    def retrieve(self, request, pk=None):
        item = ActivityFeedService.get_single(pk, request.user)
        serializer = FeedItemDetailSerializer(
            item, context={"request": request},
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def react(self, request, pk=None):
        serializer = ReactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction, created = ActivityFeedService.react(
            pk, request.user, serializer.validated_data["reaction_type"],
        )
        if created:
            return Response(status=status.HTTP_201_CREATED)
        return Response({"detail": "Reaction updated"})

    @action(detail=True, methods=["delete"], url_path="react")
    def unreact(self, request, pk=None):
        reaction_type = request.query_params.get("reaction_type")
        ActivityFeedService.unreact(pk, request.user, reaction_type)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = ActivityFeedService.comment(
            pk, request.user,
            serializer.validated_data["content"],
            serializer.validated_data.get("parent_comment_id"),
        )
        return Response(
            {"id": comment.id, "created_at": comment.created_at.isoformat()},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        comments = ActivityFeedService.get_comments(pk)
        from .serializers import FeedCommentSerializer
        serializer = FeedCommentSerializer(comments, many=True)
        return Response({"results": serializer.data})

    @action(detail=True, methods=["post"])
    def bookmark(self, request, pk=None):
        bookmark, created = ActivityFeedService.bookmark(pk, request.user)
        if created:
            return Response(status=status.HTTP_201_CREATED)
        return Response({"detail": "Already bookmarked"})

    @action(detail=True, methods=["delete"], url_path="bookmark")
    def unbookmark(self, request, pk=None):
        ActivityFeedService.unbookmark(pk, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def bookmarks(self, request):
        cursor = request.query_params.get("cursor")
        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            limit = 20

        bookmarks, has_more = ActivityFeedService.get_bookmarks(
            request.user, cursor=cursor, limit=limit,
        )
        items = [b.feed_item for b in bookmarks]
        serializer = FeedItemSerializer(
            items, many=True, context={"request": request},
        )
        next_cursor = bookmarks[-1].created_at.isoformat() if bookmarks else None
        return Response({
            "results": serializer.data,
            "cursor": next_cursor if has_more else None,
            "has_more": has_more,
        })

    @action(detail=False, methods=["get"])
    def discover(self, request):
        data = ActivityFeedService.discover()
        return Response({
            "trending_startups": [
                {"id": s.id, "name": s.name, "industry": s.industry, "stage": s.stage}
                for s in data.get("trending_startups", [])
            ],
            "recently_funded": [
                {"id": s.id, "name": s.name, "industry": s.industry}
                for s in data.get("recently_funded", [])
            ],
            "active_investors": [
                {"id": u.id, "email": u.email}
                for u in data.get("active_investors", [])
            ],
            "new_founders": [
                {"id": u.id, "email": u.email, "joined": u.date_joined.isoformat()}
                for u in data.get("new_founders", [])
            ],
            "discovered_startups": [
                {"id": s.id, "name": s.name, "industry": s.industry}
                for s in data.get("discovered_startups", [])
            ],
        })

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        analytics = ActivityFeedService.get_analytics()
        serializer = FeedAnalyticsSerializer(analytics)
        return Response(serializer.data)

    @action(detail=True, methods=["delete"])
    def delete_comment(self, request, pk=None):
        comment_id = request.query_params.get("comment_id")
        if not comment_id:
            raise ApplicationError("comment_id required", "MISSING_PARAM", 400)
        ActivityFeedService.delete_comment(int(comment_id), request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
