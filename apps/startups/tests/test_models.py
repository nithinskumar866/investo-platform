import pytest
from django.db import IntegrityError

from apps.startups.models import Startup, StartupMetric, StartupDocument, StartupTeamMember


class TestStartupModel:
    def test_create_startup_auto_generates_slug(self, db):
        startup = Startup.objects.create(
            owner=None,
            name="My Awesome Startup",
            industry="saas",
            stage="seed",
        )
        assert startup.slug == "my-awesome-startup"

    def test_slug_unique_on_duplicate_name(self, db):
        s1 = Startup.objects.create(
            owner=None, name="Duplicate Name", industry="saas", stage="seed"
        )
        s2 = Startup.objects.create(
            owner=None, name="Duplicate Name", industry="fintech", stage="idea"
        )
        assert s1.slug == "duplicate-name"
        assert s2.slug == "duplicate-name-1"

    def test_str_returns_name(self, db):
        startup = Startup.objects.create(
            owner=None, name="TestCo", industry="healthtech", stage="seed"
        )
        assert str(startup) == "TestCo"

    def test_default_status_is_draft(self, db):
        startup = Startup.objects.create(
            owner=None, name="DraftCo", industry="edtech", stage="pre_seed"
        )
        assert startup.status == Startup.Status.DRAFT

    def test_default_is_visible_is_true(self, db):
        startup = Startup.objects.create(
            owner=None, name="VisibleCo", industry="saas", stage="seed"
        )
        assert startup.is_visible is True

    def test_default_is_verified_is_false(self, db):
        startup = Startup.objects.create(
            owner=None, name="UnverifiedCo", industry="saas", stage="seed"
        )
        assert startup.is_verified is False

    def test_default_view_count_is_zero(self, db):
        startup = Startup.objects.create(
            owner=None, name="NoViews", industry="saas", stage="seed"
        )
        assert startup.view_count == 0

    def test_default_bookmark_count_is_zero(self, db):
        startup = Startup.objects.create(
            owner=None, name="NoBookmarks", industry="saas", stage="seed"
        )
        assert startup.bookmark_count == 0

    def test_default_gallery_images_is_empty_list(self, db):
        startup = Startup.objects.create(
            owner=None, name="NoGallery", industry="saas", stage="seed"
        )
        assert startup.gallery_images == []

    def test_default_currency_is_usd(self, db):
        startup = Startup.objects.create(
            owner=None, name="USDBased", industry="saas", stage="seed"
        )
        assert startup.currency == "USD"

    def test_default_tagline_and_descriptions_are_blank(self, db):
        startup = Startup.objects.create(
            owner=None, name="PlainCo", industry="saas", stage="seed"
        )
        assert startup.tagline == ""
        assert startup.short_description == ""
        assert startup.description == ""
        assert startup.detailed_pitch == ""
        assert startup.location == ""
        assert startup.website == ""
        assert startup.business_model == ""


class TestStartupTeamMemberModel:
    def test_team_member_ordering(self, db, startup):
        m1 = StartupTeamMember.objects.create(
            startup=startup, name="Alice", role="CTO", order=2, is_founder=False
        )
        m2 = StartupTeamMember.objects.create(
            startup=startup, name="Bob", role="CEO", order=1, is_founder=True
        )
        m3 = StartupTeamMember.objects.create(
            startup=startup, name="Charlie", role="CFO", order=1, is_founder=False
        )
        members = list(startup.team_members.all())
        assert members[0] == m2  # order=1, is_founder=True sorts higher
        assert members[1] == m3  # order=1, is_founder=False
        assert members[2] == m1  # order=2

    def test_team_member_str(self, db, startup):
        member = StartupTeamMember.objects.create(
            startup=startup, name="Diana", role="COO"
        )
        expected = f"Diana - COO ({startup.name})"
        assert str(member) == expected


class TestStartupMetricModel:
    def test_one_to_one_constraint(self, db):
        startup = Startup.objects.create(
            owner=None, name="MetricCo", industry="saas", stage="seed"
        )
        StartupMetric.objects.create(startup=startup)
        with pytest.raises(IntegrityError):
            StartupMetric.objects.create(startup=startup)

    def test_metric_str(self, db, startup):
        metric = StartupMetric.objects.create(startup=startup)
        assert str(metric) == f"Metrics: {startup.name}"

    def test_default_values(self, db, startup):
        metric = StartupMetric.objects.create(startup=startup)
        assert metric.monthly_revenue is None
        assert metric.annual_revenue is None
        assert metric.revenue_growth_pct is None
        assert metric.monthly_active_users is None
        assert metric.total_users is None
        assert metric.gross_margin_pct is None
        assert metric.burn_rate is None
        assert metric.runway_months is None
        assert metric.traction_description == ""
        assert metric.key_achievements == []


class TestStartupDocumentModel:
    def test_str_returns_name(self, db, startup):
        doc = StartupDocument.objects.create(
            startup=startup,
            name="Pitch Deck 2025",
            document_type=StartupDocument.DocumentType.PITCH_DECK,
        )
        assert str(doc) == "Pitch Deck 2025"

    def test_default_document_type_is_other(self, db, startup):
        doc = StartupDocument.objects.create(
            startup=startup, name="Some File"
        )
        assert doc.document_type == StartupDocument.DocumentType.OTHER
