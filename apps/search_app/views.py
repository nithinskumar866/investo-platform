from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.common.exceptions import ApplicationError

from .serializers import (
    AutocompleteResultSerializer,
    SaveSearchSerializer,
    SavedSearchSerializer,
    SearchAnalyticsSerializer,
    SearchFounderResultSerializer,
    SearchHistorySerializer,
    SearchInvestorResultSerializer,
    SearchOpportunityResultSerializer,
    SearchStartupResultSerializer,
)
from .services import SearchService

DOMAIN_SERIALIZERS = {
    "startups": SearchStartupResultSerializer,
    "investors": SearchInvestorResultSerializer,
    "founders": SearchFounderResultSerializer,
    "opportunities": SearchOpportunityResultSerializer,
}


class SearchViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_limit(self, request):
        try:
            return min(int(request.query_params.get("limit", 20)), 100)
        except (ValueError, TypeError):
            return 20

    def _search(self, request, domain):
        query = request.query_params.get("q", "")
        sort = request.query_params.get("sort", "-relevance")
        limit = self._get_limit(request)

        filters = {}
        filter_fields = {
            "startups": [
                "industry", "stage", "status", "location",
                "funding_goal_min", "funding_goal_max",
                "valuation_min", "valuation_max",
                "team_size_min", "team_size_max",
                "founded_year_min", "founded_year_max",
                "verified_only", "business_model",
            ],
            "investors": [
                "investor_type", "ticket_size_min", "ticket_size_max",
                "preferred_industries", "preferred_stages",
                "preferred_geographies", "lead_investor",
                "follow_on_investor", "years_experience_min",
                "investments_completed_min",
            ],
            "founders": [
                "industry", "funding_stage", "city", "country",
            ],
            "opportunities": [
                "status", "investor_id", "startup_id",
                "amount_min", "amount_max",
            ],
        }

        for field in filter_fields.get(domain, []):
            val = request.query_params.get(field)
            if val is not None:
                if val.lower() in ("true", "false"):
                    filters[field] = val.lower() == "true"
                elif "," in val:
                    filters[field] = [v.strip() for v in val.split(",")]
                else:
                    try:
                        filters[field] = int(val)
                    except ValueError:
                        try:
                            filters[field] = float(val)
                        except ValueError:
                            filters[field] = val

        results = SearchService.search(domain, request.user, query, filters, sort, limit)
        serializer_class = DOMAIN_SERIALIZERS.get(domain)
        serializer = serializer_class(results, many=True) if serializer_class else None
        return Response({"results": serializer.data if serializer else results})

    @action(detail=False, methods=["get"])
    def startups(self, request):
        return self._search(request, "startups")

    @action(detail=False, methods=["get"])
    def investors(self, request):
        return self._search(request, "investors")

    @action(detail=False, methods=["get"])
    def founders(self, request):
        return self._search(request, "founders")

    @action(detail=False, methods=["get"])
    def opportunities(self, request):
        return self._search(request, "opportunities")

    @action(detail=False, methods=["get"])
    def autocomplete(self, request):
        query = request.query_params.get("q", "")
        domain = request.query_params.get("domain", "startups")
        limit = self._get_limit(request)

        results = SearchService.autocomplete(query, domain, limit)
        serializer = AutocompleteResultSerializer(results, many=True)
        return Response({"results": serializer.data})

    @action(detail=False, methods=["get"])
    def recommended(self, request):
        data = SearchService.recommend(request.user)
        return Response({
            "startups": [
                {"id": s.id, "name": s.name, "industry": s.industry, "stage": s.stage}
                for s in data.get("startups", [])
            ],
            "investors": [
                {
                    "id": u.id, "email": u.email,
                    "type": getattr(getattr(u, "investor_profile", None), "investor_type", None),
                }
                for u in data.get("investors", [])
            ],
            "trending_startups": [
                {"id": s.id, "name": s.name, "industry": s.industry}
                for s in data.get("trending_startups", [])
            ],
            "recently_funded": [
                {"id": s.id, "name": s.name, "industry": s.industry}
                for s in data.get("recently_funded", [])
            ],
        })

    @action(detail=False, methods=["post"])
    def save(self, request):
        serializer = SaveSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = SearchService.save(
            request.user,
            serializer.validated_data["name"],
            serializer.validated_data["search_type"],
            serializer.validated_data.get("filters", {}),
        )
        result = SavedSearchSerializer(saved)
        return Response(result.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def saved(self, request):
        search_type = request.query_params.get("type")
        saved = SearchService.get_saved(request.user, search_type)
        serializer = SavedSearchSerializer(saved, many=True)
        return Response({"results": serializer.data})

    @action(detail=True, methods=["delete"], url_path="saved")
    def delete_saved(self, request, pk=None):
        deleted = SearchService.delete_saved(pk, request.user)
        if not deleted:
            raise ApplicationError("Saved search not found", "NOT_FOUND", 404)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def history(self, request):
        limit = self._get_limit(request)
        history = SearchService.get_history(request.user, limit)
        serializer = SearchHistorySerializer(history, many=True)
        return Response({"results": serializer.data})

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        analytics = SearchService.get_analytics()
        serializer = SearchAnalyticsSerializer(analytics)
        return Response(serializer.data)
