from rest_framework import serializers

from .models import (
    Startup, StartupTeamMember, StartupSocialLink,
    StartupDocument, StartupFundingRound, StartupMetric,
)


class StartupTeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupTeamMember
        fields = [
            "id", "name", "role", "email", "linkedin_url",
            "photo", "bio", "is_founder", "order",
        ]


class StartupSocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupSocialLink
        fields = ["id", "platform", "url"]


class StartupDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupDocument
        fields = ["id", "name", "file", "document_type", "uploaded_at"]
        read_only_fields = ["uploaded_at"]


class StartupFundingRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupFundingRound
        fields = ["id", "round_name", "amount", "date", "investors", "valuation", "notes"]


class StartupMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupMetric
        fields = [
            "monthly_revenue", "annual_revenue", "revenue_growth_pct",
            "monthly_active_users", "total_users", "gross_margin_pct",
            "burn_rate", "runway_months", "traction_description",
            "key_achievements",
        ]


class StartupListSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()

    class Meta:
        model = Startup
        fields = [
            "id", "name", "tagline", "industry", "stage",
            "funding_goal", "equity_offered", "location",
            "logo", "team_size", "is_verified", "status",
            "view_count", "bookmark_count", "created_at",
            "owner_name", "match_score",
        ]

    def get_owner_name(self, obj) -> str:
        return f"{obj.owner.first_name} {obj.owner.last_name}".strip() or obj.owner.email

    def get_match_score(self, obj) -> float | None:
        return None


class StartupDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    team_members = StartupTeamMemberSerializer(many=True, read_only=True)
    social_links = StartupSocialLinkSerializer(many=True, read_only=True)
    documents = StartupDocumentSerializer(many=True, read_only=True)
    funding_rounds = StartupFundingRoundSerializer(many=True, read_only=True)
    metrics = StartupMetricSerializer(read_only=True)

    class Meta:
        model = Startup
        fields = [
            "id", "name", "tagline", "description",
            "industry", "stage", "business_model",
            "funding_goal", "min_funding", "max_funding",
            "equity_offered", "valuation", "currency",
            "location", "website", "logo", "pitch_deck",
            "founded_date", "team_size",
            "is_verified", "is_visible", "status",
            "view_count", "bookmark_count",
            "created_at", "updated_at",
            "owner_name",
            "team_members", "social_links", "documents",
            "funding_rounds", "metrics",
        ]
        read_only_fields = [
            "id", "is_verified", "verified_at",
            "view_count", "bookmark_count",
            "created_at", "updated_at",
        ]

    def get_owner_name(self, obj) -> str:
        return f"{obj.owner.first_name} {obj.owner.last_name}".strip() or obj.owner.email


class StartupCreateSerializer(serializers.ModelSerializer):
    team_members = StartupTeamMemberSerializer(many=True, required=False)
    social_links = StartupSocialLinkSerializer(many=True, required=False)
    metrics = StartupMetricSerializer(required=False)

    class Meta:
        model = Startup
        fields = [
            "name", "tagline", "description",
            "industry", "stage", "business_model",
            "funding_goal", "min_funding", "max_funding",
            "equity_offered", "valuation", "currency",
            "location", "website", "logo", "pitch_deck",
            "founded_date", "team_size",
            "is_visible",
            "team_members", "social_links", "metrics",
        ]

    def create(self, validated_data):
        team_data = validated_data.pop("team_members", [])
        social_data = validated_data.pop("social_links", [])
        metrics_data = validated_data.pop("metrics", None)

        startup = Startup.objects.create(**validated_data)

        for member_data in team_data:
            StartupTeamMember.objects.create(startup=startup, **member_data)
        for link_data in social_data:
            StartupSocialLink.objects.create(startup=startup, **link_data)
        if metrics_data:
            StartupMetric.objects.create(startup=startup, **metrics_data)

        return startup

    def update(self, instance, validated_data):
        team_data = validated_data.pop("team_members", None)
        social_data = validated_data.pop("social_links", None)
        metrics_data = validated_data.pop("metrics", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if team_data is not None:
            instance.team_members.all().delete()
            for member_data in team_data:
                StartupTeamMember.objects.create(startup=instance, **member_data)
        if social_data is not None:
            instance.social_links.all().delete()
            for link_data in social_data:
                StartupSocialLink.objects.create(startup=instance, **link_data)
        if metrics_data is not None:
            StartupMetric.objects.update_or_create(startup=instance, defaults=metrics_data)

        return instance


class StartupUpdateSerializer(serializers.ModelSerializer):
    team_members = StartupTeamMemberSerializer(many=True, required=False)
    social_links = StartupSocialLinkSerializer(many=True, required=False)
    metrics = StartupMetricSerializer(required=False)

    class Meta:
        model = Startup
        exclude = ["owner", "created_at", "updated_at"]
        read_only_fields = [
            "id", "is_verified", "verified_at",
            "view_count", "bookmark_count",
        ]
