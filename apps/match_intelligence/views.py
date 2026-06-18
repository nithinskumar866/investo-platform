from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.common.exceptions import ApplicationError

from .serializers import (
    InsightAnalyticsSerializer,
    MatchInsightSerializer,
    PatternAnalyticsSerializer,
    SubmitFeedbackSerializer,
)
from .services import MatchIntelligenceService


class MatchIntelligenceViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        insight = MatchIntelligenceService.get_explanation(pk, request.user)
        serializer = MatchInsightSerializer(insight)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="regenerate")
    def regenerate(self, request, pk=None):
        insight = MatchIntelligenceService.regenerate_explanation(
            pk, request.user,
        )
        serializer = MatchInsightSerializer(insight)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def strengths(self, request, pk=None):
        strengths = MatchIntelligenceService.get_strengths(pk, request.user)
        return Response({"strengths": strengths})

    @action(detail=True, methods=["get"])
    def risks(self, request, pk=None):
        risks = MatchIntelligenceService.get_risks(pk, request.user)
        return Response({"risks": risks})

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        recs = MatchIntelligenceService.get_recommendations(pk, request.user)
        return Response({"recommendations": recs})

    @action(detail=False, methods=["post"])
    def feedback(self, request):
        serializer = SubmitFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fb = MatchIntelligenceService.collect_feedback(
            request.user,
            serializer.validated_data["match_id"],
            serializer.validated_data["rating"],
            serializer.validated_data.get("feedback", ""),
        )
        return Response(
            {
                "id": fb.id,
                "rating": fb.rating,
                "created": fb.created_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        analytics = MatchIntelligenceService.get_analytics()
        serializer = InsightAnalyticsSerializer(analytics)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def patterns(self, request):
        patterns = MatchIntelligenceService.get_pattern_analytics()
        serializer = PatternAnalyticsSerializer(patterns)
        return Response(serializer.data)
