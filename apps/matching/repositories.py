from typing import Optional

from django.db.models import Count, Prefetch

from apps.startups.models import Startup
from .models import InvestorPreference, MatchScore, SavedMatch, DismissedMatch, InteractionEvent


class MatchingRepository:
    """Data access layer for all matching operations."""

    # ── Preference queries ────────────────────────────────────────

    @staticmethod
    def get_or_create_preference(user):
        pref, _ = InvestorPreference.objects.get_or_create(user=user)
        return pref

    @staticmethod
    def get_user_interaction_events(user, limit=50):
        from .models import InteractionEvent
        return InteractionEvent.objects.filter(
            user=user,
        ).select_related("startup").order_by("-created_at")[:limit]

    @staticmethod
    def get_user_startups(owner):
        from apps.startups.models import Startup
        return Startup.objects.filter(owner=owner, is_visible=True)
    """Data access layer for all matching operations."""

    # ── Investor queries ──────────────────────────────────────────

    @staticmethod
    def get_active_investors():
        """Return all active investors with their preferences and profiles."""
        return InvestorPreference.objects.filter(
            is_active=True,
            user__is_active=True,
            user__role="investor",
        ).select_related(
            "user",
            "user__investor_profile",
        ).only(
            "user__id", "user__first_name", "user__last_name", "user__email",
            "user__role", "user__is_verified",
            "user__investor_profile__investor_type",
            "user__investor_profile__investment_focus",
            "user__investor_profile__preferred_stage",
            "user__investor_profile__ticket_size_min",
            "user__investor_profile__ticket_size_max",
            "user__investor_profile__industries_of_interest",
            "user__investor_profile__portfolio_count",
            "preferred_industries", "preferred_stages",
            "min_ticket_size", "max_ticket_size",
            "preferred_geographies", "risk_appetite",
            "investment_focus",
        )

    @staticmethod
    def get_investor_by_user(user) -> Optional[InvestorPreference]:
        try:
            return InvestorPreference.objects.select_related(
                "user__investor_profile",
            ).get(user=user, is_active=True)
        except InvestorPreference.DoesNotExist:
            return None

    # ── Startup queries ───────────────────────────────────────────

    @staticmethod
    def get_published_startups():
        """Return all visible, active/funded startups with related data."""
        return Startup.objects.filter(
            is_visible=True,
            status__in=["active", "funded"],
        ).select_related(
            "owner", "metrics",
        ).prefetch_related(
            "match_scores", "interaction_events",
        )

    @staticmethod
    def get_startup_by_id(startup_id: int) -> Optional[Startup]:
        try:
            return Startup.objects.select_related(
                "owner", "metrics",
            ).get(pk=startup_id)
        except Startup.DoesNotExist:
            return None

    @staticmethod
    def get_startups_for_investor(investor, exclude_dismissed=True):
        """Published startups with existing match data for an investor."""
        qs = MatchingRepository.get_published_startups().prefetch_related(
            Prefetch(
                "match_scores",
                queryset=MatchScore.objects.filter(investor=investor),
                to_attr="investor_matches",
            ),
        )
        if exclude_dismissed:
            dismissed = MatchScore.objects.filter(
                investor=investor, status=MatchScore.Status.DISMISSED,
            ).values("startup_id")
            qs = qs.exclude(id__in=dismissed)
        return qs

    # ── MatchScore queries ────────────────────────────────────────

    @staticmethod
    def get_or_create_match(investor, startup) -> MatchScore:
        match, _ = MatchScore.objects.get_or_create(
            investor=investor,
            startup=startup,
            defaults={
                "score": 0,
                "score_breakdown": {},
                "status": MatchScore.Status.PENDING,
            },
        )
        return match

    @staticmethod
    def get_match_by_id(match_id: int) -> Optional[MatchScore]:
        try:
            return MatchScore.objects.select_related(
                "investor", "startup",
                "startup__owner", "startup__metrics",
            ).get(pk=match_id)
        except MatchScore.DoesNotExist:
            return None

    @staticmethod
    def get_matches_for_investor(investor, status=None, limit=50):
        qs = MatchScore.objects.filter(investor=investor).select_related(
            "startup", "startup__owner", "startup__metrics",
        ).order_by("-score")
        if status:
            qs = qs.filter(status=status)
        if limit is not None:
            qs = qs[:limit]
        return qs

    @staticmethod
    def get_matches_for_startup(startup, status=None, limit=50):
        qs = MatchScore.objects.filter(startup=startup).select_related(
            "investor", "investor__investor_profile",
        ).order_by("-score")
        if status:
            qs = qs.filter(status=status)
        if limit is not None:
            qs = qs[:limit]
        return qs

    @staticmethod
    def bulk_update_matches(matches, fields):
        MatchScore.objects.bulk_update(matches, fields)

    @staticmethod
    def save_match_record(investor, startup, score, breakdown):
        match, created = MatchScore.objects.update_or_create(
            investor=investor,
            startup=startup,
            defaults={
                "score": score,
                "score_breakdown": breakdown,
                "status": MatchScore.Status.RECOMMENDED,
            },
        )
        return match

    # ── MatchScore mutations ──────────────────────────────────────

    @staticmethod
    def update_match_status(match, status):
        MatchScore.objects.filter(pk=match.pk).update(status=status)

    # ── InteractionEvent queries ──────────────────────────────────

    @staticmethod
    def get_match_for_investor_startup(investor, startup) -> Optional[MatchScore]:
        try:
            return MatchScore.objects.get(investor=investor, startup=startup)
        except MatchScore.DoesNotExist:
            return None

    @staticmethod
    def create_interaction_event(user, startup, event_type, metadata=None):
        return InteractionEvent.objects.create(
            user=user,
            startup=startup,
            event_type=event_type,
            metadata=metadata or {},
        )

    # ── SavedMatch queries ────────────────────────────────────────

    @staticmethod
    def get_saved_matches(user):
        return SavedMatch.objects.filter(user=user).select_related(
            "match", "match__startup", "match__investor",
        ).order_by("-created_at")

    @staticmethod
    def is_match_saved(user, match) -> bool:
        return SavedMatch.objects.filter(user=user, match=match).exists()

    @staticmethod
    def create_saved_match(user, match) -> SavedMatch:
        saved, _ = SavedMatch.objects.get_or_create(user=user, match=match)
        return saved

    @staticmethod
    def delete_saved_match(user, match) -> bool:
        deleted, _ = SavedMatch.objects.filter(user=user, match=match).delete()
        return deleted > 0

    # ── DismissedMatch queries ────────────────────────────────────

    @staticmethod
    def get_dismissed_matches(user):
        return DismissedMatch.objects.filter(user=user).select_related(
            "match", "match__startup", "match__investor",
        ).order_by("-created_at")

    @staticmethod
    def is_match_dismissed(user, match) -> bool:
        return DismissedMatch.objects.filter(user=user, match=match).exists()

    @staticmethod
    def create_dismissed_match(user, match) -> DismissedMatch:
        dismissed, _ = DismissedMatch.objects.get_or_create(user=user, match=match)
        return dismissed

    @staticmethod
    def delete_dismissed_match(user, match) -> bool:
        deleted, _ = DismissedMatch.objects.filter(user=user, match=match).delete()
        return deleted > 0

    # ── Activity queries ──────────────────────────────────────────

    @staticmethod
    def get_startup_activity_count(startup, days=30):
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return InteractionEvent.objects.filter(
            startup=startup,
            created_at__gte=cutoff,
        ).count()

    @staticmethod
    def get_investor_activity_count(investor, days=30):
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return InteractionEvent.objects.filter(
            user=investor,
            created_at__gte=cutoff,
        ).count()

    @staticmethod
    def get_investor_activity_scores(investor_ids, days=30):
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return dict(
            InteractionEvent.objects.filter(
                user_id__in=investor_ids,
                created_at__gte=cutoff,
            ).values("user_id").annotate(
                count=Count("id"),
            ).values_list("user_id", "count")
        )

    @staticmethod
    def get_startup_activity_scores(startup_ids, days=30):
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return dict(
            InteractionEvent.objects.filter(
                startup_id__in=startup_ids,
                created_at__gte=cutoff,
            ).values("startup_id").annotate(
                count=Count("id"),
            ).values_list("startup_id", "count")
        )
