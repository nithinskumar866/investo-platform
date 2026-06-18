from django.db.models import Q, Count, Value, IntegerField, Case, When
from django.db.models.functions import Length
from django.utils import timezone

from .models import SavedSearch, SearchHistory, SearchClickEvent


class SearchRepository:
    """Data access layer for search operations."""

    # ── Startup Search ────────────────────────────────────────────

    @staticmethod
    def search_startups(query="", filters=None, sort="-relevance", limit=20):
        from apps.startups.models import Startup
        qs = Startup.objects.filter(is_visible=True).select_related("owner", "metrics")

        if query:
            qs = qs.filter(
                Q(name__icontains=query)
                | Q(tagline__icontains=query)
                | Q(short_description__icontains=query)
                | Q(description__icontains=query)
                | Q(detailed_pitch__icontains=query)
                | Q(location__icontains=query)
                | Q(owner__email__icontains=query)
            )

        f = filters or {}
        if f.get("industry"):
            qs = qs.filter(industry__in=f["industry"])
        if f.get("stage"):
            qs = qs.filter(stage__in=f["stage"])
        if f.get("status"):
            qs = qs.filter(status__in=f["status"])
        if f.get("location"):
            qs = qs.filter(location__icontains=f["location"])
        if f.get("funding_goal_min"):
            qs = qs.filter(funding_goal__gte=f["funding_goal_min"])
        if f.get("funding_goal_max"):
            qs = qs.filter(funding_goal__lte=f["funding_goal_max"])
        if f.get("valuation_min"):
            qs = qs.filter(valuation__gte=f["valuation_min"])
        if f.get("valuation_max"):
            qs = qs.filter(valuation__lte=f["valuation_max"])
        if f.get("team_size_min"):
            qs = qs.filter(team_size__gte=f["team_size_min"])
        if f.get("team_size_max"):
            qs = qs.filter(team_size__lte=f["team_size_max"])
        if f.get("founded_year_min"):
            qs = qs.filter(founded_date__year__gte=f["founded_year_min"])
        if f.get("founded_year_max"):
            qs = qs.filter(founded_date__year__lte=f["founded_year_max"])
        if f.get("verified_only"):
            qs = qs.filter(is_verified=True)
        if f.get("business_model"):
            qs = qs.filter(business_model__in=f["business_model"])

        qs = SearchRepository._annotate_relevance(qs, query)
        qs = SearchRepository._apply_sorting(qs, sort)
        return qs[:limit]

    @staticmethod
    def _annotate_relevance(qs, query):
        if not query:
            return qs.annotate(
                relevance=Count("feed_activities", distinct=True)
                + Case(
                    When(is_verified=True, then=Value(50)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            )
        return qs.annotate(
            relevance=(
                Case(
                    When(name__icontains=query, then=Value(100)),
                    When(tagline__icontains=query, then=Value(80)),
                    When(short_description__icontains=query, then=Value(60)),
                    default=Value(30),
                    output_field=IntegerField(),
                )
                + Count("feed_activities", distinct=True)
                + Case(
                    When(is_verified=True, then=Value(50)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
        )

    @staticmethod
    def _apply_sorting(qs, sort):
        if sort == "-created_at":
            return qs.order_by("-created_at")
        if sort == "created_at":
            return qs.order_by("created_at")
        if sort == "-view_count":
            return qs.order_by("-view_count")
        if sort == "-team_size":
            return qs.order_by("-team_size")
        if sort == "-funding_goal":
            return qs.order_by("-funding_goal")
        if sort == "funding_goal":
            return qs.order_by("funding_goal")
        return qs.order_by("-relevance", "-created_at")

    # ── Investor Search ───────────────────────────────────────────

    @staticmethod
    def search_investors(query="", filters=None, sort="-relevance", limit=20):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        qs = User.objects.filter(
            role="investor", is_active=True,
        ).select_related("investor_preferences", "investor_profile")

        if query:
            qs = qs.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(investor_profile__bio__icontains=query)
                | Q(investor_profile__tagline__icontains=query)
                | Q(investor_preferences__investment_focus__icontains=query)
            )

        f = filters or {}
        if f.get("investor_type"):
            qs = qs.filter(investor_profile__investor_type__in=f["investor_type"])
        if f.get("ticket_size_min"):
            qs = qs.filter(
                investor_preferences__max_ticket_size__gte=f["ticket_size_min"],
            )
        if f.get("ticket_size_max"):
            qs = qs.filter(
                investor_preferences__min_ticket_size__lte=f["ticket_size_max"],
            )
        if f.get("preferred_industries"):
            from django.db.models import JSONField
            filter_q = Q()
            for ind in f["preferred_industries"]:
                filter_q |= Q(investor_preferences__preferred_industries__contains=ind)
                filter_q |= Q(investor_profile__preferred_industries__contains=ind)
            qs = qs.filter(filter_q)
        if f.get("preferred_stages"):
            filter_q = Q()
            for st in f["preferred_stages"]:
                filter_q |= Q(investor_preferences__preferred_stages__contains=st)
            qs = qs.filter(filter_q)
        if f.get("preferred_geographies"):
            filter_q = Q()
            for geo in f["preferred_geographies"]:
                filter_q |= Q(investor_preferences__preferred_geographies__contains=geo)
            qs = qs.filter(filter_q)
        if f.get("lead_investor") is True:
            qs = qs.filter(investor_profile__lead_investor=True)
        if f.get("follow_on_investor") is True:
            qs = qs.filter(investor_profile__follow_on_investor=True)
        if f.get("years_experience_min"):
            qs = qs.filter(
                investor_profile__years_of_experience__gte=f["years_experience_min"],
            )
        if f.get("investments_completed_min"):
            qs = qs.filter(
                investor_profile__investments_completed__gte=f["investments_completed_min"],
            )

        qs = SearchRepository._annotate_investor_relevance(qs, query)
        qs = SearchRepository._apply_investor_sorting(qs, sort)
        return qs[:limit]

    @staticmethod
    def _annotate_investor_relevance(qs, query):
        if not query:
            return qs.annotate(
                relevance=Value(50, output_field=IntegerField()),
            )
        return qs.annotate(
            relevance=(
                Case(
                    When(email__icontains=query, then=Value(100)),
                    When(
                        Q(first_name__icontains=query)
                        | Q(last_name__icontains=query),
                        then=Value(80),
                    ),
                    default=Value(40),
                    output_field=IntegerField(),
                )
            ),
        )

    @staticmethod
    def _apply_investor_sorting(qs, sort):
        if sort == "-created_at":
            return qs.order_by("-date_joined")
        if sort == "-investments_completed":
            return qs.order_by("-investor_profile__investments_completed")
        if sort == "-years_experience":
            return qs.order_by("-investor_profile__years_of_experience")
        return qs.order_by("-relevance", "-date_joined")

    # ── Founder Search ────────────────────────────────────────────

    @staticmethod
    def search_founders(query="", filters=None, sort="-relevance", limit=20):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        qs = User.objects.filter(
            role="entrepreneur", is_active=True,
            entrepreneur_profile__is_public=True,
        ).select_related("entrepreneur_profile")

        if query:
            qs = qs.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(entrepreneur_profile__company_name__icontains=query)
                | Q(entrepreneur_profile__tagline__icontains=query)
                | Q(entrepreneur_profile__company_description__icontains=query)
                | Q(entrepreneur_profile__achievements__icontains=query)
                | Q(entrepreneur_profile__city__icontains=query)
            )

        f = filters or {}
        if f.get("industry"):
            qs = qs.filter(entrepreneur_profile__industry__in=f["industry"])
        if f.get("funding_stage"):
            qs = qs.filter(
                entrepreneur_profile__funding_stage__in=f["funding_stage"],
            )
        if f.get("city"):
            qs = qs.filter(entrepreneur_profile__city__icontains=f["city"])
        if f.get("country"):
            qs = qs.filter(entrepreneur_profile__country__icontains=f["country"])

        qs = SearchRepository._annotate_founder_relevance(qs, query)
        qs = SearchRepository._apply_founder_sorting(qs, sort)
        return qs[:limit]

    @staticmethod
    def _annotate_founder_relevance(qs, query):
        if not query:
            return qs.annotate(relevance=Value(50, output_field=IntegerField()))
        return qs.annotate(
            relevance=(
                Case(
                    When(email__icontains=query, then=Value(100)),
                    When(
                        Q(first_name__icontains=query)
                        | Q(last_name__icontains=query),
                        then=Value(80),
                    ),
                    When(
                        entrepreneur_profile__company_name__icontains=query,
                        then=Value(70),
                    ),
                    default=Value(30),
                    output_field=IntegerField(),
                )
            ),
        )

    @staticmethod
    def _apply_founder_sorting(qs, sort):
        if sort == "-created_at":
            return qs.order_by("-date_joined")
        if sort == "-company_name":
            return qs.order_by("entrepreneur_profile__company_name")
        return qs.order_by("-relevance", "-date_joined")

    # ── Opportunity Search ────────────────────────────────────────

    @staticmethod
    def search_opportunities(query="", filters=None, sort="-created_at", limit=20):
        from apps.investments.models import InvestmentOpportunity
        qs = InvestmentOpportunity.objects.select_related(
            "startup", "investor",
        )

        if query:
            qs = qs.filter(
                Q(startup__name__icontains=query)
                | Q(startup__tagline__icontains=query)
                | Q(investor__email__icontains=query)
                | Q(notes__icontains=query)
            )

        f = filters or {}
        if f.get("status"):
            qs = qs.filter(status__in=f["status"])
        if f.get("investor_id"):
            qs = qs.filter(investor_id=f["investor_id"])
        if f.get("startup_id"):
            qs = qs.filter(startup_id=f["startup_id"])
        if f.get("amount_min"):
            qs = qs.filter(amount_requested__gte=f["amount_min"])
        if f.get("amount_max"):
            qs = qs.filter(amount_requested__lte=f["amount_max"])

        qs = qs.annotate(relevance=Value(50, output_field=IntegerField()))
        return qs.order_by(sort, "-created_at")[:limit]

    # ── Autocomplete ──────────────────────────────────────────────

    @staticmethod
    def autocomplete(query, domain="startups", limit=10):
        if domain == "startups":
            from apps.startups.models import Startup
            results = Startup.objects.filter(
                is_visible=True,
                name__icontains=query,
            ).values("id", "name", "industry", "stage", "location")[:limit]
            return [
                {
                    "id": r["id"],
                    "label": r["name"],
                    "subtitle": f"{r['industry']} · {r['stage']}" + (f" · {r['location']}" if r['location'] else ""),
                    "type": "startup",
                }
                for r in results
            ]

        if domain == "investors":
            from django.contrib.auth import get_user_model
            User = get_user_model()
            results = User.objects.filter(
                role="investor",
            ).filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query),
            ).values("id", "email", "first_name", "last_name")[:limit]
            return [
                {
                    "id": r["id"],
                    "label": f"{r['first_name']} {r['last_name']}".strip() or r["email"],
                    "subtitle": r["email"],
                    "type": "investor",
                }
                for r in results
            ]

        return []

    # ── Recommendations ───────────────────────────────────────────

    @staticmethod
    def recommend_startups(user, limit=20):
        from apps.startups.models import Startup
        return Startup.objects.filter(
            is_visible=True,
            status__in=["active", "funded"],
        ).select_related("owner").annotate(
            relevance=Count("feed_activities", distinct=True)
            + Case(
                When(is_verified=True, then=Value(50)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        ).order_by("-relevance", "-created_at")[:limit]

    @staticmethod
    def recommend_investors(user, limit=20):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(
            role="investor", is_active=True,
        ).select_related("investor_profile", "investor_preferences")[:limit]

    @staticmethod
    def trending_startups(limit=10):
        from apps.startups.models import Startup
        cutoff = timezone.now() - timezone.timedelta(days=7)
        return Startup.objects.filter(
            is_visible=True, created_at__gte=cutoff,
        ).annotate(
            score=Count("feed_activities") + Count("match_scores") * 2,
        ).order_by("-score")[:limit]

    @staticmethod
    def recently_funded(limit=10):
        from apps.startups.models import Startup
        return Startup.objects.filter(
            status="funded",
        ).select_related("owner").order_by("-updated_at")[:limit]

    # ── Saved / History / Clicks ──────────────────────────────────

    @staticmethod
    def save_search(user, name, search_type, filters):
        return SavedSearch.objects.create(
            user=user, name=name,
            search_type=search_type, filters=filters,
        )

    @staticmethod
    def get_saved_searches(user, search_type=None):
        qs = SavedSearch.objects.filter(user=user)
        if search_type:
            qs = qs.filter(search_type=search_type)
        return qs.order_by("-updated_at")

    @staticmethod
    def delete_saved_search(search_id, user):
        deleted, _ = SavedSearch.objects.filter(id=search_id, user=user).delete()
        return deleted > 0

    @staticmethod
    def record_history(user, query, search_type, filters=None, results_count=0):
        return SearchHistory.objects.create(
            user=user, query=query,
            search_type=search_type,
            filters=filters or {},
            results_count=results_count,
        )

    @staticmethod
    def get_search_history(user, limit=20):
        return SearchHistory.objects.filter(user=user)[:limit]

    @staticmethod
    def record_click(user, result_type, result_id, query=""):
        return SearchClickEvent.objects.create(
            user=user, result_type=result_type,
            result_id=result_id, query=query,
        )

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics():
        total_searches = SearchHistory.objects.count()
        total_clicks = SearchClickEvent.objects.count()
        ctr = round(total_clicks / total_searches * 100, 1) if total_searches else 0.0

        top_queries = list(
            SearchHistory.objects.values("query").annotate(
                count=Count("id"),
            ).order_by("-count")[:20]
        )

        by_type = list(
            SearchHistory.objects.values("search_type").annotate(
                count=Count("id"),
            ).order_by("-count")
        )

        return {
            "total_searches": total_searches,
            "total_clicks": total_clicks,
            "ctr": ctr,
            "top_queries": top_queries,
            "by_type": by_type,
            "last_7_days": SearchHistory.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7),
            ).count(),
        }
