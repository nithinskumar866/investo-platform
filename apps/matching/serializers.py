from rest_framework import serializers

from .models import InvestorPreference, MatchScore, InteractionEvent


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


class MatchScoreSerializer(serializers.ModelSerializer):
    startup_name = serializers.CharField(source="startup.name", read_only=True)
    investor_email = serializers.CharField(source="investor.email", read_only=True)

    class Meta:
        model = MatchScore
        fields = [
            "id", "investor_id", "investor_email", "startup_id", "startup_name",
            "score", "details", "is_viewed", "viewed_at",
            "is_bookmarked", "bookmarked_at", "is_contacted", "contacted_at",
            "is_ignored", "ignored_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class InteractionEventSerializer(serializers.ModelSerializer):
    startup_name = serializers.CharField(source="startup.name", read_only=True, allow_null=True)

    class Meta:
        model = InteractionEvent
        fields = [
            "id", "event_type", "startup_id", "startup_name",
            "metadata", "session_id", "created_at",
        ]
        read_only_fields = fields
