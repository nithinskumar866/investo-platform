from rest_framework import serializers

from .models import InvestorPreference, MatchScore, SavedMatch, DismissedMatch, InteractionEvent


class InvestorPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestorPreference
        fields = [
            "id",
            "preferred_industries",
            "preferred_stages",
            "min_ticket_size",
            "max_ticket_size",
            "preferred_geographies",
            "risk_appetite",
            "investment_focus",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MatchScoreListSerializer(serializers.ModelSerializer):
    startup_name = serializers.CharField(source="startup.name", read_only=True)
    startup_slug = serializers.CharField(source="startup.slug", read_only=True)
    startup_logo = serializers.ImageField(source="startup.logo", read_only=True)
    startup_industry = serializers.CharField(source="startup.industry", read_only=True)
    startup_stage = serializers.CharField(source="startup.stage", read_only=True)
    startup_location = serializers.CharField(source="startup.location", read_only=True)
    startup_tagline = serializers.CharField(source="startup.tagline", read_only=True)
    startup_funding_goal = serializers.DecimalField(
        source="startup.funding_goal", max_digits=15, decimal_places=2, read_only=True,
    )
    startup_owner_name = serializers.SerializerMethodField()
    startup_owner_id = serializers.IntegerField(source="startup.owner_id", read_only=True)
    investor_name = serializers.SerializerMethodField()
    investor_type = serializers.SerializerMethodField()

    class Meta:
        model = MatchScore
        fields = [
            "id", "investor_id", "startup_id",
            "startup_name", "startup_slug", "startup_logo",
            "startup_industry", "startup_stage", "startup_location",
            "startup_tagline", "startup_funding_goal", "startup_owner_name", "startup_owner_id",
            "investor_name", "investor_type",
            "score", "score_breakdown", "status",
            "is_viewed", "viewed_at",
            "is_bookmarked", "bookmarked_at",
            "is_contacted", "contacted_at",
            "is_ignored", "ignored_at",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_startup_owner_name(self, obj):
        owner = obj.startup.owner
        return f"{owner.first_name} {owner.last_name}".strip() or owner.email

    def get_investor_name(self, obj):
        return f"{obj.investor.first_name} {obj.investor.last_name}".strip() or obj.investor.email

    def get_investor_type(self, obj):
        profile = getattr(obj.investor, "investor_profile", None)
        return profile.investor_type if profile else None


class MatchScoreDetailSerializer(MatchScoreListSerializer):
    startup_detail = serializers.SerializerMethodField()
    investor_detail = serializers.SerializerMethodField()

    class Meta(MatchScoreListSerializer.Meta):
        fields = MatchScoreListSerializer.Meta.fields + [
            "startup_detail", "investor_detail",
        ]

    def get_startup_detail(self, obj):
        from apps.startups.serializers import StartupListSerializer
        return StartupListSerializer(obj.startup).data

    def get_investor_detail(self, obj):
        from apps.accounts.serializers import UserSerializer
        return UserSerializer(obj.investor).data


class SavedMatchSerializer(serializers.ModelSerializer):
    match_details = MatchScoreListSerializer(source="match", read_only=True)

    class Meta:
        model = SavedMatch
        fields = ["id", "match", "match_details", "created_at"]
        read_only_fields = ["id", "created_at"]


class DismissedMatchSerializer(serializers.ModelSerializer):
    match_details = MatchScoreListSerializer(source="match", read_only=True)

    class Meta:
        model = DismissedMatch
        fields = ["id", "match", "match_details", "created_at"]
        read_only_fields = ["id", "created_at"]


class InteractionEventSerializer(serializers.ModelSerializer):
    startup_name = serializers.CharField(source="startup.name", read_only=True, allow_null=True)

    class Meta:
        model = InteractionEvent
        fields = [
            "id", "event_type", "startup_id", "startup_name",
            "metadata", "session_id", "created_at",
        ]
        read_only_fields = fields


class MatchActionSerializer(serializers.Serializer):
    match_id = serializers.IntegerField()
