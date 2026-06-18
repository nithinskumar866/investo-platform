from typing import Optional
from decimal import Decimal

from django.db import models
from django.db.models import Count
from django.db.models import Q

from .models import Startup, StartupTeamMember, StartupSocialLink, StartupMetric


class StartupRepository:
    """Data access layer for Startup model — encapsulates all query patterns."""

    @staticmethod
    def get_base_queryset():
        return Startup.objects.select_related(
            "owner", "metrics"
        ).prefetch_related(
            "team_members", "social_links", "documents", "funding_rounds",
        )

    @staticmethod
    def get_by_id(startup_id: int) -> Optional[Startup]:
        try:
            return StartupRepository.get_base_queryset().get(pk=startup_id)
        except Startup.DoesNotExist:
            return None

    @staticmethod
    def get_by_slug(slug: str) -> Optional[Startup]:
        try:
            return StartupRepository.get_base_queryset().get(slug=slug)
        except Startup.DoesNotExist:
            return None

    @staticmethod
    def create_startup(owner, data, team_data=None, social_data=None, metrics_data=None):
        startup = Startup.objects.create(owner=owner, **data)
        for member_data in (team_data or []):
            StartupTeamMember.objects.create(startup=startup, **member_data)
        for link_data in (social_data or []):
            StartupSocialLink.objects.create(startup=startup, **link_data)
        if metrics_data:
            StartupMetric.objects.create(startup=startup, **metrics_data)
        return startup

    @staticmethod
    def update_startup(startup, data, team_data=None, social_data=None, metrics_data=None):
        for attr, value in data.items():
            setattr(startup, attr, value)
        startup.save()

        if team_data is not None:
            startup.team_members.all().delete()
            for m in team_data:
                StartupTeamMember.objects.create(startup=startup, **m)
        if social_data is not None:
            startup.social_links.all().delete()
            for s in social_data:
                StartupSocialLink.objects.create(startup=startup, **s)
        if metrics_data is not None:
            StartupMetric.objects.update_or_create(startup=startup, defaults=metrics_data)

        return startup

    @staticmethod
    def update_fields(startup: Startup, fields: dict) -> Startup:
        for attr, value in fields.items():
            setattr(startup, attr, value)
        startup.save(update_fields=list(fields.keys()))
        return startup

    @staticmethod
    def get_user_startups(user) -> models.QuerySet:
        return Startup.objects.filter(owner=user).select_related(
            "owner", "metrics"
        ).prefetch_related(
            "team_members", "social_links", "documents", "funding_rounds"
        ).order_by("-created_at")

    @staticmethod
    def get_published_startups() -> models.QuerySet:
        return Startup.objects.filter(
            is_visible=True, status__in=["active", "funded"]
        ).select_related("owner", "metrics").prefetch_related(
            "team_members", "social_links", "documents"
        ).order_by("-created_at")

    @staticmethod
    def search_startups(query: str) -> models.QuerySet:
        return StartupRepository.get_published_startups().filter(
            Q(name__icontains=query)
            | Q(tagline__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(detailed_pitch__icontains=query)
        )

    @staticmethod
    def filter_startups(
        industry: Optional[str] = None,
        stage: Optional[str] = None,
        location: Optional[str] = None,
        funding_min: Optional[Decimal] = None,
        funding_max: Optional[Decimal] = None,
        team_size_min: Optional[int] = None,
        team_size_max: Optional[int] = None,
        is_verified: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> models.QuerySet:
        qs = StartupRepository.get_published_startups()
        if industry:
            qs = qs.filter(industry=industry)
        if stage:
            qs = qs.filter(stage=stage)
        if location:
            qs = qs.filter(location__icontains=location)
        if funding_min is not None:
            qs = qs.filter(funding_goal__gte=funding_min)
        if funding_max is not None:
            qs = qs.filter(funding_goal__lte=funding_max)
        if team_size_min is not None:
            qs = qs.filter(team_size__gte=team_size_min)
        if team_size_max is not None:
            qs = qs.filter(team_size__lte=team_size_max)
        if is_verified is not None:
            qs = qs.filter(is_verified=is_verified)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-created_at")

    @staticmethod
    def increment_view_count(startup: Startup) -> None:
        Startup.objects.filter(pk=startup.pk).update(
            view_count=models.F("view_count") + 1
        )

    @staticmethod
    def get_queryset(user) -> models.QuerySet:
        if user.role == "admin":
            return Startup.objects.all()
        if user.role == "entrepreneur":
            return Startup.objects.filter(
                Q(owner=user) | Q(is_visible=True, status__in=["active", "funded"]),
            )
        return Startup.objects.filter(is_visible=True, status__in=["active", "funded"])

    @staticmethod
    def get_total_count() -> int:
        return Startup.objects.count()

    @staticmethod
    def get_active_count() -> int:
        return Startup.objects.filter(status=Startup.Status.ACTIVE).count()

    @staticmethod
    def get_funded_count() -> int:
        return Startup.objects.filter(status=Startup.Status.FUNDED).count()

    @staticmethod
    def get_by_industry() -> dict:
        return dict(
            Startup.objects.values("industry")
            .annotate(count=Count("id"))
            .values_list("industry", "count")
        )

    @staticmethod
    def get_by_stage() -> dict:
        return dict(
            Startup.objects.values("stage")
            .annotate(count=Count("id"))
            .values_list("stage", "count")
        )
