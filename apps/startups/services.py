import logging

from django.db import transaction

from .models import Startup
from .repositories import StartupRepository

logger = logging.getLogger(__name__)


class StartupService:
    @staticmethod
    @transaction.atomic
    def create_startup(owner, data):
        team_data = data.pop("team_members", [])
        social_data = data.pop("social_links", [])
        metrics_data = data.pop("metrics", None)

        startup = StartupRepository.create_startup(
            owner=owner,
            data=data,
            team_data=team_data,
            social_data=social_data,
            metrics_data=metrics_data,
        )

        logger.info(f"Startup created: {startup.name} by {owner.email}")
        from apps.activity_feed.services import ActivityFeedService
        ActivityFeedService.publish_activity(
            actor=owner,
            activity_type="startup_created",
            title=f"{owner.email} created {startup.name}",
            startup=startup,
            target_object_id=startup.id,
            target_object_type="startup",
        )
        return startup

    @staticmethod
    def get_user_startups(user):
        return StartupRepository.get_user_startups(user)

    @staticmethod
    def get_published_startups():
        return StartupRepository.get_published_startups()

    @staticmethod
    @transaction.atomic
    def update_startup(startup, data):
        team_data = data.pop("team_members", None)
        social_data = data.pop("social_links", None)
        metrics_data = data.pop("metrics", None)

        return StartupRepository.update_startup(
            startup=startup,
            data=data,
            team_data=team_data,
            social_data=social_data,
            metrics_data=metrics_data,
        )

    @staticmethod
    def increment_view_count(startup):
        StartupRepository.increment_view_count(startup)

    @staticmethod
    def get_queryset(user):
        return StartupRepository.get_queryset(user)

    @staticmethod
    def get_statistics():
        return {
            "total": StartupRepository.get_total_count(),
            "active": StartupRepository.get_active_count(),
            "funded": StartupRepository.get_funded_count(),
            "by_industry": StartupRepository.get_by_industry(),
            "by_stage": StartupRepository.get_by_stage(),
        }

    @staticmethod
    @transaction.atomic
    def publish_startup(startup):
        if startup.status != "draft":
            raise ValueError("Only draft startups can be published")
        StartupRepository.update_fields(startup, {
            "status": Startup.Status.ACTIVE,
            "is_visible": True,
        })
        logger.info(f"Startup published: {startup.name}")
        from apps.activity_feed.services import ActivityFeedService
        ActivityFeedService.publish_activity(
            actor=startup.owner,
            activity_type="startup_published",
            title=f"{startup.name} is now on the platform",
            startup=startup,
            target_object_id=startup.id,
            target_object_type="startup",
        )
        return startup

    @staticmethod
    @transaction.atomic
    def archive_startup(startup):
        if startup.status == "archived":
            raise ValueError("Startup is already archived")
        StartupRepository.update_fields(startup, {
            "status": "archived",
            "is_visible": False,
        })
        logger.info(f"Startup archived: {startup.name}")
        return startup
