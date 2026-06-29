import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.common.exceptions import ApplicationError

from .models import MatchScore
from .services import MatchingService
from .repositories import MatchingRepository
from .serializers import (
    MatchScoreListSerializer, MatchScoreDetailSerializer,
    SavedMatchSerializer, DismissedMatchSerializer,
    InvestorPreferenceSerializer, InteractionEventSerializer,
)
from .permissions import IsInvestor, IsEntrepreneur

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["Matching - Investor"],
        summary="List recommended startup matches for the current investor",
    ),
    retrieve=extend_schema(
        tags=["Matching - Investor"],
        summary="Get details of a specific match",
    ),
)
class InvestorMatchViewSet(viewsets.ReadOnlyModelViewSet):
    """Investor-facing match endpoints: view recommendations, save, dismiss."""

    permission_classes = [IsAuthenticated, IsInvestor]
    serializer_class = MatchScoreListSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MatchScoreDetailSerializer
        return MatchScoreListSerializer

    def get_queryset(self):
        return MatchScore.objects.filter(investor=self.request.user).select_related(
            "startup", "startup__owner", "startup__metrics",
        ).order_by("-score", "-startup_id")

    def list(self, request, *args, **kwargs):
        limit = request.GET.get("limit", 50)
        try:
            limit = min(int(limit), 100)
        except (ValueError, TypeError):
            limit = 50

        reload = request.GET.get("reload", "").lower() == "true"
        is_async = request.GET.get("async", "").lower() == "true"

        if reload:
            if is_async:
                from .tasks import generate_investor_matches_task
                generate_investor_matches_task.delay(request.user.id, limit=limit)
            else:
                MatchingService.generate_matches_for_investor(request.user, limit=limit)

        matches = self.get_queryset()
        
        # DEBUG START
        pref = MatchingRepository.get_investor_by_user(request.user)
        startups = MatchingRepository.get_startups_for_investor(request.user)
        if request.GET.get('debug'):
            return Response({
                "pref_exists": pref is not None,
                "startups_count": startups.count(),
                "startups": [s.name for s in startups],
                "matches_count": matches.count()
            })
        # DEBUG END

        matches = self.get_queryset()
        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({"status": "success", "data": serializer.data})

        serializer = self.get_serializer(matches, many=True)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(
        tags=["Matching - Investor"],
        summary="Save a match for later reference",
    )
    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        match = self.get_object()
        MatchingService.save_match(request.user, match)
        return Response(
            {"status": "success", "data": {"message": "Match saved"}},
        )

    @extend_schema(
        tags=["Matching - Investor"],
        summary="Dismiss a match (remove from recommendations)",
    )
    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        match = self.get_object()
        MatchingService.dismiss_match(request.user, match)
        return Response(
            {"status": "success", "data": {"message": "Match dismissed"}},
        )

    @extend_schema(
        tags=["Matching - Investor"],
        summary="List saved matches for the current investor",
    )
    @action(detail=False, methods=["get"])
    def saved(self, request):
        saved = MatchingService.get_saved_matches(request.user)
        serializer = SavedMatchSerializer(saved, many=True)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(
        tags=["Matching - Investor"],
        summary="List dismissed matches for the current investor",
    )
    @action(detail=False, methods=["get"], url_path="dismissed")
    def dismissed_list(self, request):
        dismissed = MatchingService.get_dismissed_matches(request.user)
        serializer = DismissedMatchSerializer(dismissed, many=True)
        return Response({"status": "success", "data": serializer.data})


@extend_schema_view(
    list=extend_schema(
        tags=["Matching - Entrepreneur"],
        summary="List recommended investors for the current entrepreneur",
    ),
    retrieve=extend_schema(
        tags=["Matching - Entrepreneur"],
        summary="Get details of a specific match",
    ),
)
class EntrepreneurMatchViewSet(viewsets.ReadOnlyModelViewSet):
    """Entrepreneur-facing match endpoints: find investors, save, dismiss."""

    permission_classes = [IsAuthenticated, IsEntrepreneur]
    serializer_class = MatchScoreListSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MatchScoreDetailSerializer
        return MatchScoreListSerializer

    def get_queryset(self):
        return MatchScore.objects.filter(
            startup__owner=self.request.user,
        ).select_related(
            "investor", "investor__investor_profile",
            "startup",
        ).order_by("-score")

    def list(self, request, *args, **kwargs):
        startup_id = request.GET.get("startup_id")
        limit = request.GET.get("limit", 50)
        try:
            limit = min(int(limit), 100)
        except (ValueError, TypeError):
            limit = 50

        reload = request.GET.get("reload", "").lower() == "true"
        is_async = request.GET.get("async", "").lower() == "true"

        if reload:
            startups = MatchingRepository.get_user_startups(request.user)
            if startup_id:
                startups = startups.filter(pk=startup_id)
            if is_async:
                from .tasks import generate_startup_matches_task
                for s in startups:
                    generate_startup_matches_task.delay(s.id, limit=limit)
            else:
                for s in startups:
                    MatchingService.generate_matches_for_startup(s, limit=limit)

        matches = self.get_queryset()
        if startup_id:
            matches = matches.filter(startup_id=startup_id)

        page = self.paginate_queryset(matches)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({"status": "success", "data": serializer.data})

        serializer = self.get_serializer(matches, many=True)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(
        tags=["Matching - Entrepreneur"],
        summary="Save a match for later reference",
    )
    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        match = self.get_object()
        MatchingService.save_match(request.user, match)
        return Response(
            {"status": "success", "data": {"message": "Match saved"}},
        )

    @extend_schema(
        tags=["Matching - Entrepreneur"],
        summary="Dismiss a match (remove from recommendations)",
    )
    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        match = self.get_object()
        MatchingService.dismiss_match(request.user, match)
        return Response(
            {"status": "success", "data": {"message": "Match dismissed"}},
        )

    @extend_schema(
        tags=["Matching - Entrepreneur"],
        summary="List saved matches",
    )
    @action(detail=False, methods=["get"])
    def saved(self, request):
        saved = MatchingService.get_saved_matches(request.user)
        serializer = SavedMatchSerializer(saved, many=True)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(
        tags=["Matching - Entrepreneur"],
        summary="List dismissed matches",
    )
    @action(detail=False, methods=["get"], url_path="dismissed")
    def dismissed_list(self, request):
        dismissed = MatchingService.get_dismissed_matches(request.user)
        serializer = DismissedMatchSerializer(dismissed, many=True)
        return Response({"status": "success", "data": serializer.data})


# ── Legacy function-based views (kept for backward compat) ───────

@extend_schema(
    tags=["Matching"],
    summary="Get match recommendations for the current investor (legacy)",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_matches(request):
    http_request = request._request if hasattr(request, "_request") else request
    if request.user.role == "investor":
        vs = InvestorMatchViewSet.as_view({"get": "list"})
        return vs(http_request)
    if request.user.role == "entrepreneur":
        vs = EntrepreneurMatchViewSet.as_view({"get": "list"})
        return vs(http_request)
    return Response(
        {"status": "error",
         "error": {"code": "WRONG_ROLE", "message": "Only investors and entrepreneurs can view matches"}},
        status=403,
    )


@extend_schema(
    tags=["Matching"],
    summary="Get or update investor preferences",
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def investor_preferences(request):
    if request.user.role != "investor":
        raise ApplicationError("Only investors can set preferences", "WRONG_ROLE", 403)

    pref = MatchingRepository.get_or_create_preference(request.user)

    if request.method == "GET":
        return Response(
            {"status": "success", "data": InvestorPreferenceSerializer(pref).data},
        )

    serializer = InvestorPreferenceSerializer(pref, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {"status": "success", "data": InvestorPreferenceSerializer(pref).data},
    )


@extend_schema(
    tags=["Matching"],
    summary="Record an interaction event (view, bookmark, ignore, contact)",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def interact(request):
    event_type = request.data.get("event_type")
    startup_id = request.data.get("startup_id")

    valid_events = ["viewed", "bookmarked", "ignored", "contacted"]
    if event_type not in valid_events:
        raise ApplicationError(
            f"Invalid event_type. Must be one of: {', '.join(valid_events)}",
            "INVALID_EVENT_TYPE", 400,
        )

    startup = None
    if startup_id:
        startup = MatchingRepository.get_startup_by_id(startup_id)
        if not startup or not startup.is_visible:
            raise ApplicationError("Startup not found", "NOT_FOUND", 404)

    event = MatchingService.record_interaction(
        user=request.user,
        startup=startup,
        event_type=event_type,
        metadata=request.data.get("metadata", {}),
    )

    logger.info(f"Interaction: {request.user.email} {event_type} {startup}")
    return Response(
        {"status": "success", "data": {"id": event.id, "event_type": event.event_type}},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Matching"],
    summary="Get interaction history for the current user",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def interaction_history(request):
    limit = request.GET.get("limit", 50)
    try:
        limit = min(int(limit), 200)
    except (ValueError, TypeError):
        limit = 50

    events = MatchingRepository.get_user_interaction_events(
        request.user, limit=limit,
    )
    serializer = InteractionEventSerializer(events, many=True)
    return Response({"status": "success", "data": serializer.data})


@extend_schema(
    tags=["Matching"],
    summary="Get match analytics (admin only)",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def match_analytics(request):
    if request.user.role != "admin":
        raise ApplicationError("Admin access required", "FORBIDDEN", 403)

    data = MatchingService.get_match_analytics()
    return Response({"status": "success", "data": data})
