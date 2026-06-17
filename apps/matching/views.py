import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from .models import InvestorPreference, MatchScore, InteractionEvent
from .services import MatchingService
from .serializers import MatchScoreSerializer, InteractionEventSerializer
from apps.common.exceptions import ApplicationError
from apps.startups.models import Startup

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Matching"],
    summary="Get match recommendations for the current investor",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_matches(request):
    if request.user.role != "investor":
        raise ApplicationError("Only investors can view matches", "WRONG_ROLE", 403)

    limit = request.GET.get("limit", 20)
    try:
        limit = min(int(limit), 100)
    except (ValueError, TypeError):
        limit = 20

    matches = MatchingService.get_matches_for_investor(request.user, limit=limit)
    from apps.startups.serializers import StartupListSerializer

    data = []
    for m in matches:
        startup_data = StartupListSerializer(m["startup"]).data
        startup_data["match_score"] = m["score"]
        startup_data["match_details"] = m["details"]
        startup_data["is_viewed"] = m["is_viewed"]
        startup_data["is_bookmarked"] = m["is_bookmarked"]
        startup_data["match_id"] = m["match_id"]
        data.append(startup_data)

    return Response({"status": "success", "data": data})


@extend_schema(
    tags=["Matching"],
    summary="Get recommended startups for the current investor (alias for my-matches)",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommended_startups(request):
    return my_matches(request)


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
        try:
            startup = Startup.objects.get(pk=startup_id, is_visible=True)
        except Startup.DoesNotExist:
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

    events = MatchingService.get_interaction_history(request.user, limit=limit)
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


@extend_schema(
    tags=["Matching"],
    summary="Get detailed match information for a specific startup",
    operation_id="matching_detail_retrieve",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def match_detail(request, startup_id):
    if request.user.role != "investor":
        raise ApplicationError("Only investors can view match details", "WRONG_ROLE", 403)

    try:
        startup = Startup.objects.get(pk=startup_id, is_visible=True)
    except Startup.DoesNotExist:
        raise ApplicationError("Startup not found", "NOT_FOUND", 404)

    try:
        pref = InvestorPreference.objects.get(user=request.user, is_active=True)
    except InvestorPreference.DoesNotExist:
        raise ApplicationError("No active preferences found", "NO_PREFERENCES", 404)

    try:
        match = MatchScore.objects.get(investor=request.user, startup=startup)
        score = float(match.score)
        details = match.details
        is_viewed = match.is_viewed
        is_bookmarked = match.is_bookmarked
        is_contacted = match.is_contacted
        is_ignored = match.is_ignored
    except MatchScore.DoesNotExist:
        from apps.matching.services import ScoringEngine
        score, scores, explanations = ScoringEngine.calculate_match(pref, startup)
        details = {"breakdown": scores, "explanations": explanations}
        is_viewed = False
        is_bookmarked = False
        is_contacted = False
        is_ignored = False

    from apps.startups.serializers import StartupDetailSerializer
    startup_data = StartupDetailSerializer(startup).data

    data = {
        "startup": startup_data,
        "match_score": score,
        "match_details": details,
        "is_viewed": is_viewed,
        "is_bookmarked": is_bookmarked,
        "is_contacted": is_contacted,
        "is_ignored": is_ignored,
    }

    return Response({"status": "success", "data": data})


# --- Investor Preferences ---

@extend_schema(
    tags=["Matching"],
    summary="Get or update investor preferences",
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def investor_preferences(request):
    if request.user.role != "investor":
        raise ApplicationError("Only investors can set preferences", "WRONG_ROLE", 403)

    pref, created = InvestorPreference.objects.get_or_create(user=request.user)

    if request.method == "GET":
        from .serializers import InvestorPreferenceSerializer
        return Response(
            {"status": "success", "data": InvestorPreferenceSerializer(pref).data},
        )

    from .serializers import InvestorPreferenceSerializer
    serializer = InvestorPreferenceSerializer(pref, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        {"status": "success", "data": InvestorPreferenceSerializer(pref).data},
    )