import logging

from django.db import models as db_models
from django.db import transaction
from django.db.models import Count, Q

from .models import Startup, StartupTeamMember, StartupSocialLink, StartupMetric

logger = logging.getLogger(__name__)


class StartupService:
    @staticmethod
    @transaction.atomic
    def create_startup(owner, data):
        team_data = data.pop("team_members", [])
        social_data = data.pop("social_links", [])
        metrics_data = data.pop("metrics", None)

        startup = Startup.objects.create(owner=owner, **data)

        for member_data in team_data:
            StartupTeamMember.objects.create(startup=startup, **member_data)
        for link_data in social_data:
            StartupSocialLink.objects.create(startup=startup, **link_data)
        if metrics_data:
            StartupMetric.objects.create(startup=startup, **metrics_data)

        logger.info(f"Startup created: {startup.name} by {owner.email}")
        return startup

    @staticmethod
    @transaction.atomic
    def update_startup(startup, data):
        team_data = data.pop("team_members", None)
        social_data = data.pop("social_links", None)
        metrics_data = data.pop("metrics", None)

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
    def increment_view_count(startup):
        Startup.objects.filter(pk=startup.pk).update(view_count=db_models.F("view_count") + 1)

    @staticmethod
    def get_queryset(user):
        if user.role == "admin":
            return Startup.objects.all()
        if user.role == "entrepreneur":
            return Startup.objects.filter(
                Q(owner=user) | Q(is_visible=True, status__in=["active", "funded"]),
            )
        return Startup.objects.filter(is_visible=True, status__in=["active", "funded"])

    @staticmethod
    def get_statistics():
        return {
            "total": Startup.objects.count(),
            "active": Startup.objects.filter(status="active").count(),
            "funded": Startup.objects.filter(status="funded").count(),
            "by_industry": dict(
                Startup.objects.values("industry").annotate(count=Count("id")).values_list("industry", "count")
            ),
            "by_stage": dict(
                Startup.objects.values("stage").annotate(count=Count("id")).values_list("stage", "count")
            ),
        }
