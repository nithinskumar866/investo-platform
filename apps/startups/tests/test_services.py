import pytest

from apps.startups.models import Startup
from apps.startups.services import StartupService


class TestGetQueryset:
    def test_admin_sees_all_startups(self, db, admin_user):
        Startup.objects.create(owner=admin_user, name="A", industry="saas", stage="seed", status="active")
        Startup.objects.create(owner=admin_user, name="B", industry="fintech", stage="seed", status="draft")
        qs = StartupService.get_queryset(admin_user)
        assert qs.count() == 2

    def test_entrepreneur_sees_own_and_published(self, db, user):
        Startup.objects.create(owner=user, name="Own", industry="saas", stage="seed", status="draft")
        Startup.objects.create(owner=user, name="OwnActive", industry="saas", stage="seed", status="active", is_visible=True)
        qs = StartupService.get_queryset(user)
        assert qs.count() == 2

    def test_investor_sees_only_published(self, db, user, investor):
        Startup.objects.create(owner=user, name="Visible", industry="saas", stage="seed", status="active", is_visible=True)
        Startup.objects.create(owner=user, name="Hidden", industry="saas", stage="seed", status="draft", is_visible=False)
        qs = StartupService.get_queryset(investor)
        assert qs.count() == 1
        assert qs.first().name == "Visible"

    def test_anonymous_sees_only_published(self, db, user):
        Startup.objects.create(owner=user, name="Pub", industry="saas", stage="seed", status="active", is_visible=True)
        Startup.objects.create(owner=user, name="Draft", industry="saas", stage="seed", status="draft", is_visible=False)
        qs = StartupService.get_queryset(type("FakeUser", (), {"is_anonymous": True, "role": ""})())
        assert qs.count() == 1


class TestPublishStartup:
    def test_publishes_draft_startup(self, db, user):
        startup = Startup.objects.create(owner=user, name="DraftCo", industry="saas", stage="seed", status="draft")
        StartupService.publish_startup(startup)
        startup.refresh_from_db()
        assert startup.status == Startup.Status.ACTIVE
        assert startup.is_visible is True

    def test_raises_error_if_not_draft(self, db, user):
        startup = Startup.objects.create(owner=user, name="ActiveCo", industry="saas", stage="seed", status="active")
        with pytest.raises(ValueError, match="Only draft startups can be published"):
            StartupService.publish_startup(startup)


class TestArchiveStartup:
    def test_archives_active_startup(self, db, user):
        startup = Startup.objects.create(owner=user, name="ActiveCo", industry="saas", stage="seed", status="active")
        StartupService.archive_startup(startup)
        startup.refresh_from_db()
        assert startup.status == "archived"
        assert startup.is_visible is False

    def test_raises_error_if_already_archived(self, db, user):
        startup = Startup.objects.create(owner=user, name="ArchivedCo", industry="saas", stage="seed", status="archived")
        with pytest.raises(ValueError, match="Startup is already archived"):
            StartupService.archive_startup(startup)


class TestIncrementViewCount:
    def test_increments_view_count(self, db, user):
        startup = Startup.objects.create(owner=user, name="ViewedCo", industry="saas", stage="seed")
        assert startup.view_count == 0
        StartupService.increment_view_count(startup)
        startup.refresh_from_db()
        assert startup.view_count == 1

    def test_increments_multiple_times(self, db, user):
        startup = Startup.objects.create(owner=user, name="MultiView", industry="saas", stage="seed")
        for _ in range(5):
            StartupService.increment_view_count(startup)
        startup.refresh_from_db()
        assert startup.view_count == 5


class TestGetStatistics:
    def test_returns_counts_and_breakdowns(self, db, user):
        Startup.objects.create(owner=user, name="A", industry="saas", stage="seed", status="active")
        Startup.objects.create(owner=user, name="B", industry="fintech", stage="seed", status="active")
        Startup.objects.create(owner=user, name="C", industry="saas", stage="seed", status="funded")
        stats = StartupService.get_statistics()
        assert stats["total"] == 3
        assert stats["active"] == 2
        assert stats["funded"] == 1
        assert stats["by_industry"]["saas"] == 2
        assert stats["by_industry"]["fintech"] == 1
        assert stats["by_stage"]["seed"] == 3

    def test_returns_zero_when_empty(self, db):
        stats = StartupService.get_statistics()
        assert stats["total"] == 0
        assert stats["active"] == 0
        assert stats["funded"] == 0
        assert stats["by_industry"] == {}
        assert stats["by_stage"] == {}


class TestGetUserStartups:
    def test_returns_owners_startups(self, db, user, founder):
        s1 = Startup.objects.create(owner=user, name="Mine", industry="saas", stage="seed")
        Startup.objects.create(owner=founder, name="Theirs", industry="saas", stage="seed")
        result = StartupService.get_user_startups(user)
        assert list(result) == [s1]

    def test_returns_empty_if_no_startups(self, db, user):
        result = StartupService.get_user_startups(user)
        assert list(result) == []

    def test_returns_all_when_multiple(self, db, user):
        s1 = Startup.objects.create(owner=user, name="A", industry="saas", stage="seed")
        s2 = Startup.objects.create(owner=user, name="B", industry="fintech", stage="seed")
        result = StartupService.get_user_startups(user)
        assert len(result) == 2
