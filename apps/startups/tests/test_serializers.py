import pytest
from decimal import Decimal

from apps.startups.models import Startup, StartupMetric, StartupTeamMember, StartupSocialLink
from apps.startups.serializers import (
    StartupListSerializer,
    StartupDetailSerializer,
    StartupCreateSerializer,
    StartupDocumentSerializer,
    StartupTeamMemberSerializer,
)


class TestStartupListSerializer:
    def test_includes_expected_fields(self, startup):
        serializer = StartupListSerializer(startup)
        fields = set(serializer.data.keys())
        expected = {
            "id", "name", "slug", "tagline", "industry", "stage",
            "funding_goal", "equity_offered", "location",
            "logo", "team_size", "is_verified", "status",
            "view_count", "bookmark_count", "created_at",
            "owner_name", "match_score",
        }
        assert fields == expected

    def test_owner_name_fallback_to_email(self, db):
        from apps.startups.models import Startup
        startup = Startup.objects.create(
            owner=None, name="NoName", industry="saas", stage="seed"
        )
        startup.owner.first_name = ""
        startup.owner.last_name = ""
        serializer = StartupListSerializer(startup)
        assert "owner_name" in serializer.data

    def test_match_score_is_none(self, startup):
        serializer = StartupListSerializer(startup)
        assert serializer.data["match_score"] is None


class TestStartupCreateSerializer:
    def test_creates_startup_with_owner(self, db, user):
        data = {
            "name": "NewCo",
            "industry": "fintech",
            "stage": "seed",
            "funding_goal": "500000.00",
            "equity_offered": "10.00",
        }
        serializer = StartupCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        startup = serializer.save(owner=user)
        assert startup.name == "NewCo"
        assert startup.owner == user
        assert startup.industry == "fintech"

    def test_requires_name(self, db):
        data = {"industry": "saas", "stage": "seed"}
        serializer = StartupCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "name" in serializer.errors

    def test_requires_industry(self, db):
        data = {"name": "NoIndustry", "stage": "seed"}
        serializer = StartupCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "industry" in serializer.errors

    def test_requires_stage(self, db):
        data = {"name": "NoStage", "industry": "saas"}
        serializer = StartupCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "stage" in serializer.errors

    def test_creates_nested_team_members(self, db, user):
        data = {
            "name": "TeamCo",
            "industry": "saas",
            "stage": "seed",
            "team_members": [
                {"name": "Alice", "role": "CTO"},
                {"name": "Bob", "role": "CEO", "is_founder": True},
            ],
        }
        serializer = StartupCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        startup = serializer.save(owner=user)
        assert startup.team_members.count() == 2

    def test_creates_nested_metrics(self, db, user):
        data = {
            "name": "MetricCo",
            "industry": "saas",
            "stage": "seed",
            "metrics": {"monthly_revenue": "50000.00", "annual_revenue": "600000.00"},
        }
        serializer = StartupCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        startup = serializer.save(owner=user)
        assert startup.metrics is not None
        assert startup.metrics.monthly_revenue == Decimal("50000.00")

    def test_creates_nested_social_links(self, db, user):
        data = {
            "name": "SocialCo",
            "industry": "saas",
            "stage": "seed",
            "social_links": [
                {"platform": "linkedin", "url": "https://linkedin.com/co"},
            ],
        }
        serializer = StartupCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        startup = serializer.save(owner=user)
        assert startup.social_links.count() == 1


class TestStartupDetailSerializer:
    def test_includes_nested_relations(self, startup):
        StartupTeamMember.objects.create(
            startup=startup, name="Alice", role="CTO"
        )
        StartupSocialLink.objects.create(
            startup=startup, platform="linkedin", url="https://linkedin.com/co"
        )
        StartupMetric.objects.create(startup=startup, monthly_revenue=Decimal("10000"))
        serializer = StartupDetailSerializer(startup)
        assert "team_members" in serializer.data
        assert "social_links" in serializer.data
        assert "documents" in serializer.data
        assert "funding_rounds" in serializer.data
        assert "metrics" in serializer.data

    def test_includes_all_detail_fields(self, startup):
        serializer = StartupDetailSerializer(startup)
        fields = set(serializer.data.keys())
        expected = {
            "id", "name", "slug", "tagline", "short_description", "description",
            "detailed_pitch", "industry", "stage", "business_model",
            "funding_goal", "min_funding", "max_funding",
            "equity_offered", "valuation", "currency",
            "location", "website", "logo", "pitch_deck",
            "gallery_images", "founded_date", "team_size",
            "is_verified", "is_visible", "status",
            "view_count", "bookmark_count",
            "created_at", "updated_at",
            "owner_name",
            "team_members", "social_links", "documents",
            "funding_rounds", "metrics",
        }
        assert fields == expected


class TestStartupDocumentSerializer:
    def test_valid_data_passes(self, db, startup):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile(
            "test.pdf",
            b"%PDF-1.4 fake pdf content for testing",
            content_type="application/pdf",
        )
        data = {
            "name": "Business Plan",
            "file": file,
            "document_type": "business_plan",
        }
        serializer = StartupDocumentSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        doc = serializer.save(startup=startup)
        assert doc.name == "Business Plan"
        assert doc.document_type == "business_plan"
        assert doc.startup == startup

    def test_invalid_file_extension_fails(self, db):
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile

        file = SimpleUploadedFile(
            "test.exe",
            b"binary content",
            content_type="application/x-msdownload",
        )
        data = {
            "name": "Malicious File",
            "file": file,
        }
        serializer = StartupDocumentSerializer(data=data)
        assert not serializer.is_valid()
        assert "file" in serializer.errors

    def test_file_size_too_large_fails(self, db):
        from django.core.files.uploadedfile import SimpleUploadedFile

        large_content = b"a" * (11 * 1024 * 1024)
        file = SimpleUploadedFile(
            "large.pdf",
            large_content,
            content_type="application/pdf",
        )
        data = {
            "name": "Large File",
            "file": file,
        }
        serializer = StartupDocumentSerializer(data=data)
        assert not serializer.is_valid()
        assert "file" in serializer.errors
