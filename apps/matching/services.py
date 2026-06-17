import logging

from django.conf import settings
from django.db import transaction, models
from django.db.models import Q, Count, Avg, Prefetch
from django.utils import timezone

from apps.startups.models import Startup
from apps.matching.models import InvestorPreference, MatchScore, InteractionEvent

logger = logging.getLogger(__name__)


class ScoringEngine:
    WEIGHTS = getattr(settings, "MATCHING_WEIGHTS", {
        "industry": 30,
        "stage": 20,
        "funding": 20,
        "geography": 10,
        "traction": 10,
        "preferences": 10,
    })

    @classmethod
    def calculate_match(cls, investor_pref, startup):
        scores = {}
        explanations = []

        industry_score, industry_reason = cls._score_industry(investor_pref, startup)
        scores["industry"] = industry_score
        if industry_reason:
            explanations.append(industry_reason)

        stage_score, stage_reason = cls._score_stage(investor_pref, startup)
        scores["stage"] = stage_score
        if stage_reason:
            explanations.append(stage_reason)

        funding_score, funding_reason = cls._score_funding(investor_pref, startup)
        scores["funding"] = funding_score
        if funding_reason:
            explanations.append(funding_reason)

        geography_score, geography_reason = cls._score_geography(investor_pref, startup)
        scores["geography"] = geography_score
        if geography_reason:
            explanations.append(geography_reason)

        traction_score, traction_reason = cls._score_traction(investor_pref, startup)
        scores["traction"] = traction_score
        if traction_reason:
            explanations.append(traction_reason)

        preferences_score, preferences_reason = cls._score_preferences(investor_pref, startup)
        scores["preferences"] = preferences_score
        if preferences_reason:
            explanations.append(preferences_reason)

        total = sum(
            scores.get(key, 0) * weight / 100
            for key, weight in cls.WEIGHTS.items()
        )

        return round(total, 2), scores, explanations

    @classmethod
    def _score_industry(cls, pref, startup):
        preferred = pref.preferred_industries or []
        if not preferred:
            return 50, "No industry preferences set (neutral score)"
        if startup.industry in preferred:
            return 100, f"Startup industry ({startup.industry}) matches your preference"
        return 0, f"Startup industry ({startup.industry}) not in your preferences"

    @classmethod
    def _score_stage(cls, pref, startup):
        preferred = pref.preferred_stages or []
        if not preferred:
            return 50, "No stage preferences set (neutral score)"
        if startup.stage in preferred:
            return 100, f"Startup stage ({startup.stage}) matches your preference"
        return 0, f"Startup stage ({startup.stage}) not in your preferences"

    @classmethod
    def _score_funding(cls, pref, startup):
        min_ticket = pref.min_ticket_size
        max_ticket = pref.max_ticket_size
        goal = startup.funding_goal

        if goal is None:
            return 50, "Funding goal not disclosed (neutral score)"
        if min_ticket is None and max_ticket is None:
            return 50, "No ticket size preferences set (neutral score)"

        if min_ticket is not None and goal < min_ticket:
            return 30, f"Funding goal (${goal}) below your minimum ticket (${min_ticket})"
        if max_ticket is not None and goal > max_ticket:
            return 30, f"Funding goal (${goal}) exceeds your maximum ticket (${max_ticket})"

        if min_ticket and max_ticket:
            mid = (min_ticket + max_ticket) / 2
            ratio = 1 - abs(float(goal) - float(mid)) / (float(max_ticket) - float(min_ticket)) if max_ticket != min_ticket else 1
            score = 50 + int(ratio * 50)
            return score, f"Funding goal (${goal}) within your range (${min_ticket}-${max_ticket})"

        return 100, "Funding goal aligns with your range"

    @classmethod
    def _score_geography(cls, pref, startup):
        preferred = [g.lower().strip() for g in (pref.preferred_geographies or [])]
        if not preferred:
            return 50, "No geography preferences set (neutral score)"
        if startup.location and any(geo in startup.location.lower() for geo in preferred):
            matching = [g for g in preferred if g in startup.location.lower()]
            return 100, f"Startup location ({startup.location}) matches: {', '.join(matching)}"
        return 0, f"Startup location ({startup.location}) not in your preferred geographies"

    @classmethod
    def _score_traction(cls, pref, startup):
        try:
            metrics = startup.metrics
        except Exception:
            return 50, "No traction data available (neutral score)"

        score = 50
        reasons = []

        if metrics.monthly_revenue and metrics.monthly_revenue > 0:
            if metrics.revenue_growth_pct and metrics.revenue_growth_pct > 20:
                score += 20
                reasons.append(f"Revenue growth of {metrics.revenue_growth_pct}%")
            score += 10
            reasons.append(f"Monthly revenue: ${metrics.monthly_revenue}")

        if metrics.monthly_active_users and metrics.monthly_active_users > 100:
            score += 15
            reasons.append(f"{metrics.monthly_active_users} MAU")

        if metrics.runway_months and metrics.runway_months > 12:
            score += 10
            reasons.append(f"{metrics.runway_months} months runway")

        return min(score, 100), "; ".join(reasons) if reasons else "Basic traction metrics available"

    @classmethod
    def _score_preferences(cls, pref, startup):
        score = 50
        reasons = []

        if pref.investment_focus and startup.description:
            focus_keywords = pref.investment_focus.lower().split()
            desc_lower = startup.description.lower()
            matches = sum(1 for kw in focus_keywords if kw in desc_lower)
            if matches > 0:
                bonus = min(matches * 10, 40)
                score += bonus
                reasons.append(f"{matches} keyword matches in description")

        risk_map = {"conservative": 1, "moderate": 2, "aggressive": 3}
        stage_map = {
            "idea": 1, "pre_seed": 2, "seed": 3,
            "series_a": 4, "series_b": 5, "series_c": 6, "growth": 7,
        }
        pref_risk = risk_map.get(pref.risk_appetite, 2)
        startup_stage = stage_map.get(startup.stage, 3)

        if pref_risk >= 3 and startup_stage <= 2:
            score -= 10
            reasons.append("Risk appetite too low for early-stage startup")
        elif pref_risk <= 1 and startup_stage >= 5:
            score -= 10
            reasons.append("Startup stage too advanced for conservative investor")
        else:
            score += 10
            reasons.append("Risk/stage alignment good")

        return min(score, 100), "; ".join(reasons) if reasons else "No specific preference signals"


class MatchingService:
    @staticmethod
    def get_matches_for_investor(investor, limit=20):
        try:
            pref = InvestorPreference.objects.get(user=investor, is_active=True)
        except InvestorPreference.DoesNotExist:
            return []

        startups = Startup.objects.filter(
            is_visible=True,
            status__in=["active", "funded"],
        ).select_related("metrics").prefetch_related(
            Prefetch("match_scores", queryset=MatchScore.objects.filter(investor=investor), to_attr="existing_match"),
        )

        matches = []
        for startup in startups:
            existing = startup.existing_match[0] if startup.existing_match else None

            if existing and existing.is_ignored:
                continue
            if existing and existing.is_contacted:
                continue

            if existing:
                score = float(existing.score)
                details = existing.details
            else:
                score, scores, explanations = ScoringEngine.calculate_match(pref, startup)
                details = {"breakdown": scores, "explanations": explanations}

            matches.append({
                "startup": startup,
                "score": score,
                "details": details,
                "is_viewed": existing.is_viewed if existing else False,
                "is_bookmarked": existing.is_bookmarked if existing else False,
                "match_id": existing.id if existing else None,
            })

        matches.sort(key=lambda m: m["score"], reverse=True)
        return matches[:limit]

    @staticmethod
    def get_recommended_investors(startup, limit=20):
        prefs = InvestorPreference.objects.filter(is_active=True).select_related("user")

        results = []
        for pref in prefs:
            score, scores, explanations = ScoringEngine.calculate_match(pref, startup)
            if score >= 30:
                results.append({
                    "investor_id": pref.user_id,
                    "investor_name": (
                        f"{pref.user.first_name} {pref.user.last_name}".strip()
                        or pref.user.email
                    ),
                    "score": score,
                    "details": {"breakdown": scores, "explanations": explanations},
                })

        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:limit]

    @staticmethod
    @transaction.atomic
    def record_interaction(user, startup, event_type, metadata=None):
        event = InteractionEvent.objects.create(
            user=user,
            startup=startup,
            event_type=event_type,
            metadata=metadata or {},
        )

        if startup:
            try:
                match = MatchScore.objects.get(investor=user, startup=startup)
            except MatchScore.DoesNotExist:
                match = MatchScore(investor=user, startup=startup)

            now = timezone.now()

            if event_type == "viewed":
                match.is_viewed = True
                match.viewed_at = now
            elif event_type == "bookmarked":
                match.is_bookmarked = True
                match.bookmarked_at = now
            elif event_type == "ignored":
                match.is_ignored = True
                match.ignored_at = now
            elif event_type == "contacted":
                match.is_contacted = True
                match.contacted_at = now

            if not match.score:
                try:
                    pref = InvestorPreference.objects.get(user=user, is_active=True)
                    score, scores, explanations = ScoringEngine.calculate_match(pref, startup)
                    match.score = score
                    match.details = {"breakdown": scores, "explanations": explanations}
                except InvestorPreference.DoesNotExist:
                    pass

            match.save()

        return event

    @staticmethod
    def get_interaction_history(user, limit=50):
        return InteractionEvent.objects.filter(user=user).select_related("startup").order_by("-created_at")[:limit]

    @staticmethod
    def get_match_analytics():
        return {
            "total_matches": MatchScore.objects.count(),
            "avg_score": MatchScore.objects.aggregate(avg=Avg("score"))["avg__score"],
            "total_views": MatchScore.objects.filter(is_viewed=True).count(),
            "total_bookmarks": MatchScore.objects.filter(is_bookmarked=True).count(),
            "total_contacts": MatchScore.objects.filter(is_contacted=True).count(),
            "by_event_type": dict(
                InteractionEvent.objects.values("event_type").annotate(
                    count=Count("id")
                ).values_list("event_type", "count")
            ),
        }
