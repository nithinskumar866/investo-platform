import logging
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.startups.models import Startup
from apps.accounts.models import InvestorProfile
from apps.accounts.repositories import InvestorProfileRepository
from .models import InvestorPreference, MatchScore
from .repositories import MatchingRepository

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Production-grade matching algorithm with weighted factors.

    Scores are out of 100 total percentage points.
    Each factor contributes its weight to the final score.
    Unavailable data gets a neutral (50% of weight) score rather than 0,
    so missing data doesn't unfairly penalize matches.
    """

    WEIGHTS = getattr(settings, "MATCHING_WEIGHTS", {
        "industry": 30,
        "stage": 15,
        "funding": 15,
        "geography": 10,
        "keywords": 10,
        "startup_completeness": 5,
        "investor_completeness": 5,
        "startup_activity": 5,
        "investor_activity": 5,
    })

    @classmethod
    def _get_profile(cls, pref):
        """Get InvestorProfile from pref.user, with None fallback."""
        try:
            return pref.user.investor_profile
        except Exception:
            return None

    @classmethod
    def calculate(
        cls,
        investor_pref: InvestorPreference,
        startup: Startup,
        investor_profile=None,
        startup_activity_score: float = None,
        investor_activity_score: float = None,
    ) -> tuple:
        """
        Calculate match score between an investor preference and a startup.
        Accepts optional pre-computed activity scores to avoid N+1 queries.
        Accepts optional investor_profile to avoid getattr/N+1 on profile access.

        Returns (total_score, score_breakdown_dict).
        """
        profile = investor_profile or cls._get_profile(investor_pref)
        breakdown = {}

        industry_score = cls._industry_match(investor_pref, startup, profile)
        breakdown["industry"] = round(industry_score, 2)

        stage_score = cls._stage_compatibility(investor_pref, startup, profile)
        breakdown["stage"] = round(stage_score, 2)

        funding_score = cls._funding_match(investor_pref, startup, profile)
        breakdown["funding"] = round(funding_score, 2)

        geography_score = cls._geography_match(investor_pref, startup)
        breakdown["geography"] = round(geography_score, 2)

        keywords_score = cls._keyword_match(investor_pref, startup, profile)
        breakdown["keywords"] = round(keywords_score, 2)

        startup_comp = cls._startup_completeness(startup)
        breakdown["startup_completeness"] = round(startup_comp, 2)

        investor_comp = cls._investor_completeness(investor_pref, profile)
        breakdown["investor_completeness"] = round(investor_comp, 2)

        startup_act = startup_activity_score if startup_activity_score is not None else cls._startup_activity_score(startup)
        breakdown["startup_activity"] = round(startup_act, 2)

        investor_act = investor_activity_score if investor_activity_score is not None else cls._investor_activity_score(investor_pref.user)
        breakdown["investor_activity"] = round(investor_act, 2)

        total = sum(
            breakdown.get(key, 0) * weight / 100
            for key, weight in cls.WEIGHTS.items()
        )

        return round(total, 2), breakdown

    @classmethod
    def _industry_match(cls, pref: InvestorPreference, startup: Startup, profile=None) -> float:
        """
        30% weight factor.
        Checks both InvestorPreference.preferred_industries and
        InvestorProfile.preferred_industries against startup.industry.
        Exact match = 100. Partial (related industry) = 50. No match = 0.
        """
        preferred = [i.lower().strip() for i in (pref.preferred_industries or [])]
        startup_industry = startup.industry.lower() if startup.industry else ""

        if not preferred:
            return 50.0

        if startup_industry in preferred:
            return 100.0

        if profile:
            profile_industries = profile.preferred_industries or []
            if isinstance(profile_industries, list):
                if startup_industry in [i.lower() for i in profile_industries]:
                    return 80.0

        related_map = {
            "ai_ml": ["saas", "fintech", "healthtech"],
            "fintech": ["saas", "blockchain"],
            "healthtech": ["biotech", "ai_ml"],
            "edtech": ["saas", "media"],
            "saas": ["fintech", "edtech", "healthtech"],
            "ecommerce": ["marketplace", "food_tech"],
            "marketplace": ["ecommerce", "social"],
            "blockchain": ["fintech", "gaming"],
            "biotech": ["healthtech", "cleantech"],
            "cleantech": ["iot", "real_estate"],
        }
        related = related_map.get(startup_industry, [])
        if any(r in preferred for r in related):
            return 50.0

        return 0.0

    @classmethod
    def _stage_compatibility(cls, pref: InvestorPreference, startup: Startup, profile=None) -> float:
        """
        15% weight factor.
        Checks both preferred_stages and InvestorProfile.preferred_stages.
        Considers adjacent stages as partial matches (e.g., investor wants seed,
        startup is pre-seed = adjacent = 60).
        """
        preferred = [s.lower().strip() for s in (pref.preferred_stages or [])]
        startup_stage = startup.stage.lower() if startup.stage else ""

        if not preferred:
            return 50.0

        if startup_stage in preferred:
            return 100.0

        stage_order = ["idea", "pre_seed", "seed", "series_a", "series_b", "series_c", "growth"]
        try:
            startup_idx = stage_order.index(startup_stage)
        except ValueError:
            return 50.0

        for pref_stage in preferred:
            try:
                pref_idx = stage_order.index(pref_stage)
                diff = abs(startup_idx - pref_idx)
                if diff == 1:
                    return 60.0
                if diff == 2:
                    return 30.0
            except ValueError:
                continue

        if profile:
            profile_stages = profile.preferred_stages or []
            if isinstance(profile_stages, list):
                for ps in profile_stages:
                    try:
                        pref_idx = stage_order.index(ps.lower())
                        diff = abs(startup_idx - pref_idx)
                        if diff == 0:
                            return 90.0
                        if diff == 1:
                            return 50.0
                    except ValueError:
                        continue

        return 0.0

    @classmethod
    def _funding_match(cls, pref: InvestorPreference, startup: Startup, profile=None) -> float:
        """
        15% weight factor.
        Investor ticket size vs startup funding_goal.
        Perfect fit = 100. Outside range = partial based on how far off.
        Uses both InvestorPreference and InvestorProfile ticket fields.
        """
        goal = startup.funding_goal
        min_ticket = pref.min_ticket_size
        max_ticket = pref.max_ticket_size

        if goal is None:
            return 50.0
        if min_ticket is None and max_ticket is None:
            if profile:
                min_ticket = profile.ticket_size_min
                max_ticket = profile.ticket_size_max
            if min_ticket is None and max_ticket is None:
                return 50.0

        min_t = float(min_ticket or 0)
        max_t = float(max_ticket or float("inf"))
        goal_f = float(goal)

        if min_t <= goal_f <= max_t:
            if min_t > 0 and max_t < float("inf"):
                mid = (min_t + max_t) / 2
                ratio = 1 - abs(goal_f - mid) / (max_t - min_t) if max_t != min_t else 1
                return 50.0 + ratio * 50.0
            return 100.0

        if goal_f < min_t:
            ratio = goal_f / min_t
            return max(10.0, ratio * 40.0)
        if goal_f > max_t < float("inf"):
            ratio = max_t / goal_f
            return max(10.0, ratio * 40.0)

        return 50.0

    @classmethod
    def _geography_match(cls, pref: InvestorPreference, startup: Startup) -> float:
        """
        10% weight factor.
        Checks preferred_geographies against startup.location.
        Case-insensitive substring matching for flexibility.
        """
        preferred = [g.lower().strip() for g in (pref.preferred_geographies or [])]
        location = (startup.location or "").lower()

        if not preferred:
            return 50.0
        if not location:
            return 30.0

        if any(geo == location for geo in preferred):
            return 100.0
        if any(geo in location for geo in preferred):
            return 80.0
        if any(location in geo for geo in preferred):
            return 60.0

        return 0.0

    @classmethod
    def _keyword_match(cls, pref: InvestorPreference, startup: Startup, profile=None) -> float:
        """
        10% weight factor.
        Matches investment_focus keywords against startup name, tagline,
        short_description, and description.
        Uses both InvestorPreference and InvestorProfile focus fields.
        """
        focus = (pref.investment_focus or "").lower()
        if profile and profile.investment_focus:
            focus += " " + (profile.investment_focus or "").lower()

        if not focus.strip():
            return 50.0

        keywords = set(focus.split())
        if not keywords:
            return 50.0

        text_fields = " ".join(filter(None, [
            startup.name or "",
            startup.tagline or "",
            startup.short_description or "",
            startup.description or "",
        ])).lower()

        matches = sum(1 for kw in keywords if kw in text_fields and len(kw) > 2)
        if not matches:
            return 0.0

        ratio = matches / len(keywords)
        return min(100.0, ratio * 100.0)

    @classmethod
    def _startup_completeness(cls, startup: Startup) -> float:
        """
        5% weight factor.
        Measures how complete the startup profile is based on filled fields.
        """
        fields = [
            bool(startup.name),
            bool(startup.tagline),
            bool(startup.short_description),
            bool(startup.description),
            bool(startup.detailed_pitch),
            bool(startup.industry),
            bool(startup.stage),
            bool(startup.funding_goal is not None),
            bool(startup.location),
            bool(startup.website),
            bool(startup.logo),
            bool(startup.team_size is not None),
            bool(startup.founded_date),
        ]
        try:
            metrics = startup.metrics
            fields.extend([
                bool(metrics.monthly_revenue is not None),
                bool(metrics.annual_revenue is not None),
                bool(metrics.monthly_active_users is not None),
            ])
        except Exception:
            fields.extend([False, False, False])

        filled = sum(fields)
        total = len(fields)
        return (filled / total) * 100.0

    @classmethod
    def _investor_completeness(cls, pref: InvestorPreference, profile=None) -> float:
        """
        5% weight factor.
        Measures how complete the investor profile + preferences are.
        Uses both InvestorPreference (pref) and InvestorProfile (profile) fields.
        """
        fields = [
            bool(pref.preferred_industries),
            bool(pref.preferred_stages),
            bool(pref.min_ticket_size is not None),
            bool(pref.max_ticket_size is not None),
            bool(pref.preferred_geographies),
            bool(pref.investment_focus),
        ]
        if profile:
            fields.extend([
                bool(profile.investor_type),
                bool(profile.bio),
                bool(profile.tagline),
                bool(profile.investment_focus),
                bool(profile.preferred_industries),
                bool(profile.preferred_stages),
                bool(profile.ticket_size_min is not None),
                bool(profile.ticket_size_max is not None),
                bool(profile.preferred_geographies),
                bool(profile.website_url),
                bool(profile.linkedin_url),
                bool(profile.years_of_experience is not None),
            ])
        else:
            fields.extend([False] * 13)

        filled = sum(fields)
        total = len(fields)
        return (filled / total) * 100.0

    @classmethod
    def _startup_activity_score(cls, startup: Startup) -> float:
        """
        5% weight factor.
        Based on view_count and recent interaction events.
        Higher view_count and recency = higher score.
        """
        view_score = min(50.0, float(startup.view_count or 0) * 5)

        recent_events = MatchingRepository.get_startup_activity_count(startup, days=30)
        event_score = min(50.0, float(recent_events) * 5)

        return view_score + event_score

    @classmethod
    def _investor_activity_score(cls, user) -> float:
        """
        5% weight factor.
        Based on recent interaction events by this investor.
        Active investors get higher scores.
        """
        recent_events = MatchingRepository.get_investor_activity_count(user, days=30)
        return min(100.0, float(recent_events) * 10)


class MatchingService:
    """
    Orchestrates matching operations.
    Delegates data access to MatchingRepository.
    Delegates scoring to ScoringEngine.
    """

    @staticmethod
    def generate_matches_for_investor(investor, limit=50):
        """
        Generate/re-rank matches for an investor against all candidate startups.
        Pre-computes batch activity scores to eliminate N+1 queries.
        Fetches InvestorProfile through repository for scoring completeness.
        """
        pref = MatchingRepository.get_investor_by_user(investor)
        if not pref:
            logger.warning(f"No active preferences for investor {investor.email}")
            return []

        investor_profile = InvestorProfileRepository.get_by_user(investor)
        startups = MatchingRepository.get_startups_for_investor(investor)
        startup_ids = [s.id for s in startups]
        startup_activity_map = MatchingRepository.get_startup_activity_scores(startup_ids)
        investor_activity = MatchingRepository.get_investor_activity_count(investor)

        matches = []

        for startup in startups:
            existing = getattr(startup, "investor_matches", [])
            existing_match = existing[0] if existing else None

            if existing_match and existing_match.status == MatchScore.Status.DISMISSED:
                continue

            startup_act = min(100.0, float(startup_activity_map.get(startup.id, 0)) * 5)
            score, breakdown = ScoringEngine.calculate(
                pref, startup,
                investor_profile=investor_profile,
                startup_activity_score=startup_act,
                investor_activity_score=min(100.0, float(investor_activity) * 10),
            )
            match = MatchingRepository.save_match_record(
                investor=investor,
                startup=startup,
                score=score,
                breakdown=breakdown,
            )
            matches.append(match)

        matches.sort(key=lambda m: m.score, reverse=True)
        top = matches[:limit]

        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=investor,
            notification_type="new_match",
            title="New Matching Recommendations",
            message=f"We found {len(top)} new startup matches for you",
            data={"count": len(top), "limit": limit},
        )
        return top

    @staticmethod
    def generate_matches_for_startup(startup, limit=50):
        """
        Find investors that match a given startup.
        Pre-computes batch activity scores to eliminate N+1 queries.
        Fetches each InvestorProfile through repository for scoring.
        """
        active_investors = MatchingRepository.get_active_investors()
        investor_ids = [p.user_id for p in active_investors]
        investor_activity_map = MatchingRepository.get_investor_activity_scores(investor_ids)
        startup_activity = MatchingRepository.get_startup_activity_count(startup)

        investor_profiles = {
            p.user_id: p
            for p in InvestorProfile.objects.filter(
                user_id__in=investor_ids,
            ).only("id", "user_id", "investor_type", "bio", "tagline",
                   "investment_focus", "preferred_industries", "preferred_stages",
                   "ticket_size_min", "ticket_size_max", "preferred_geographies",
                   "website_url", "linkedin_url", "years_of_experience")
        }

        results = []

        for pref in active_investors:
            investor_act = min(100.0, float(investor_activity_map.get(pref.user_id, 0)) * 10)
            investor_profile = investor_profiles.get(pref.user_id)
            score, breakdown = ScoringEngine.calculate(
                pref, startup,
                investor_profile=investor_profile,
                startup_activity_score=min(100.0, float(startup_activity) * 5),
                investor_activity_score=investor_act,
            )
            if score >= 20:
                match = MatchingRepository.save_match_record(
                    investor=pref.user,
                    startup=startup,
                    score=score,
                    breakdown=breakdown,
                )
                results.append(match)

        results.sort(key=lambda m: m.score, reverse=True)
        top = results[:limit]

        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=startup.owner,
            notification_type="new_match",
            title="New Investor Interest",
            message=f"{len(top)} investors are interested in {startup.name}",
            data={"count": len(top), "startup_id": startup.id},
        )
        return top

    @staticmethod
    def refresh_match_scores(investor=None, startup=None):
        """
        Recalculate scores for existing matches.
        Can be scoped to a single investor or startup.
        Batch operation for periodic score refresh.
        Uses repository for all data access.
        """
        if investor:
            matches = MatchingRepository.get_matches_for_investor(
                investor, limit=None,
            )
            if not matches:
                return
            pref = MatchingRepository.get_investor_by_user(investor)
            if not pref:
                return
            for match in matches:
                score, breakdown = ScoringEngine.calculate(pref, match.startup)
                match.score = score
                match.score_breakdown = breakdown
            MatchingRepository.bulk_update_matches(
                matches, fields=["score", "score_breakdown"],
            )

        elif startup:
            matches = MatchingRepository.get_matches_for_startup(
                startup, limit=None,
            )
            if not matches:
                return
            for match in matches:
                pref = MatchingRepository.get_investor_by_user(match.investor)
                if not pref:
                    continue
                score, breakdown = ScoringEngine.calculate(pref, startup)
                match.score = score
                match.score_breakdown = breakdown
            MatchingRepository.bulk_update_matches(
                matches, fields=["score", "score_breakdown"],
            )

    @staticmethod
    def get_investor_recommendations(investor, limit=50):
        """Get recommended matches for an investor (with scores > 0)."""
        return MatchingRepository.get_matches_for_investor(
            investor, limit=limit,
        )

    @staticmethod
    def get_startup_recommendations(startup, limit=50):
        """Get recommended investors for a startup (with scores > 0)."""
        return MatchingRepository.get_matches_for_startup(
            startup, limit=limit,
        )

    @staticmethod
    def get_saved_matches(user):
        """Get all matches saved by a user."""
        return MatchingRepository.get_saved_matches(user)

    @staticmethod
    def get_dismissed_matches(user):
        """Get all matches dismissed by a user."""
        return MatchingRepository.get_dismissed_matches(user)

    @staticmethod
    @transaction.atomic
    def save_match(user, match) -> MatchScore:
        """Save a match for later reference. Updates match status to SAVED."""
        MatchingRepository.create_saved_match(user, match)
        MatchingRepository.update_match_status(match, MatchScore.Status.SAVED)

        from apps.notifications.services import NotificationService
        if user.role == "investor":
            NotificationService.notify(
                recipient=match.startup.owner,
                notification_type="match_saved",
                title="Investor Saved Your Startup",
                message=f"{user.email} has saved {match.startup.name} to their portfolio",
                actor=user,
                data={"startup_id": match.startup_id, "match_id": match.id},
            )
        else:
            NotificationService.notify(
                recipient=match.investor,
                notification_type="new_match",
                title="Startup Showed Interest",
                message=f"{match.startup.name} is interested in your investment",
                actor=user,
                data={"startup_id": match.startup_id, "match_id": match.id},
            )
        return match

    @staticmethod
    @transaction.atomic
    def unsave_match(user, match) -> MatchScore:
        """Remove a saved match. Reverts status to RECOMMENDED."""
        MatchingRepository.delete_saved_match(user, match)
        MatchingRepository.update_match_status(match, MatchScore.Status.RECOMMENDED)
        return match

    @staticmethod
    @transaction.atomic
    def dismiss_match(user, match) -> MatchScore:
        """Dismiss a match (hide from recommendations)."""
        from django.utils import timezone
        MatchingRepository.create_dismissed_match(user, match)
        MatchingRepository.update_match_status(match, MatchScore.Status.DISMISSED)
        match.is_ignored = True
        match.ignored_at = timezone.now()
        match.save(update_fields=["is_ignored", "ignored_at"])
        return match

    @staticmethod
    @transaction.atomic
    def undismiss_match(user, match) -> MatchScore:
        """Undo a dismiss. Reverts status and flags."""
        MatchingRepository.delete_dismissed_match(user, match)
        MatchingRepository.update_match_status(match, MatchScore.Status.RECOMMENDED)
        match.is_ignored = False
        match.ignored_at = None
        match.save(update_fields=["is_ignored", "ignored_at"])
        return match

    @staticmethod
    def record_interaction(user, startup, event_type, metadata=None):
        """Record a user interaction event and update the associated match."""
        event = MatchingRepository.create_interaction_event(
            user=user,
            startup=startup,
            event_type=event_type,
            metadata=metadata or {},
        )

        if startup:
            match = MatchingRepository.get_match_for_investor_startup(user, startup)
            if not match:
                return event

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
                match.status = MatchScore.Status.CONTACTED
                match.contacted_at = now
            match.save()

        return event

    @staticmethod
    def get_match_analytics():
        """Admin analytics for match system."""
        from django.db.models import Count, Avg
        from .models import SavedMatch
        return {
            "total_matches": MatchScore.objects.count(),
            "avg_score": MatchScore.objects.aggregate(avg=Avg("score"))["avg"],
            "by_status": dict(
                MatchScore.objects.values("status").annotate(
                    count=Count("id"),
                ).values_list("status", "count")
            ),
            "total_saved": SavedMatch.objects.count(),
        }
