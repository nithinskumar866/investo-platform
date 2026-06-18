from rest_framework import serializers

from .models import InvestmentOpportunity, InvestmentActivity


class InvestmentActivitySerializer(serializers.ModelSerializer):
    actor = serializers.SerializerMethodField()

    class Meta:
        model = InvestmentActivity
        fields = ["id", "actor", "action", "metadata", "timestamp"]
        read_only_fields = ["id", "actor", "timestamp"]

    def get_actor(self, obj):
        if not obj.actor:
            return None
        return {
            "id": obj.actor.id,
            "first_name": obj.actor.first_name,
            "last_name": obj.actor.last_name,
            "email": obj.actor.email,
        }


class InvestmentOpportunityListSerializer(serializers.ModelSerializer):
    startup = serializers.SerializerMethodField()
    investor = serializers.SerializerMethodField()

    class Meta:
        model = InvestmentOpportunity
        fields = [
            "id",
            "startup",
            "investor",
            "amount_requested",
            "amount_offered",
            "equity_requested",
            "equity_offered",
            "valuation",
            "proposed_valuation",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_startup(self, obj):
        return {
            "id": obj.startup.id,
            "name": obj.startup.name,
            "slug": obj.startup.slug,
            "industry": obj.startup.industry,
            "stage": obj.startup.stage,
            "logo": obj.startup.logo.url if obj.startup.logo else None,
            "location": obj.startup.location,
        }

    def get_investor(self, obj):
        profile = getattr(obj.investor, "investor_profile", None)
        return {
            "id": obj.investor.id,
            "first_name": obj.investor.first_name,
            "last_name": obj.investor.last_name,
            "email": obj.investor.email,
            "investor_type": profile.investor_type if profile else None,
        }


class InvestmentOpportunityDetailSerializer(serializers.ModelSerializer):
    startup = serializers.SerializerMethodField()
    investor = serializers.SerializerMethodField()
    activities = InvestmentActivitySerializer(many=True, read_only=True)
    recent_activities = InvestmentActivitySerializer(many=True, read_only=True, source="activities")

    class Meta:
        model = InvestmentOpportunity
        fields = [
            "id",
            "startup",
            "investor",
            "amount_requested",
            "amount_offered",
            "equity_requested",
            "equity_offered",
            "valuation",
            "proposed_valuation",
            "status",
            "notes",
            "term_sheet_url",
            "created_at",
            "updated_at",
            "activities",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_startup(self, obj):
        return {
            "id": obj.startup.id,
            "name": obj.startup.name,
            "slug": obj.startup.slug,
            "tagline": obj.startup.tagline,
            "description": obj.startup.short_description,
            "industry": obj.startup.industry,
            "stage": obj.startup.stage,
            "funding_goal": obj.startup.funding_goal,
            "equity_offered": obj.startup.equity_offered,
            "valuation": obj.startup.valuation,
            "logo": obj.startup.logo.url if obj.startup.logo else None,
            "location": obj.startup.location,
            "team_size": obj.startup.team_size,
        }

    def get_investor(self, obj):
        profile = getattr(obj.investor, "investor_profile", None)
        return {
            "id": obj.investor.id,
            "first_name": obj.investor.first_name,
            "last_name": obj.investor.last_name,
            "email": obj.investor.email,
            "avatar": obj.investor.avatar.url if obj.investor.avatar else None,
            "investor_type": profile.investor_type if profile else None,
            "ticket_size_min": str(profile.ticket_size_min) if profile and profile.ticket_size_min else None,
            "ticket_size_max": str(profile.ticket_size_max) if profile and profile.ticket_size_max else None,
        }


class CreateInvestmentOpportunitySerializer(serializers.Serializer):
    startup_id = serializers.IntegerField()
    amount_requested = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True,
    )
    equity_requested = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True,
    )
    valuation = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class UpdateStageSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            "interested", "meeting_scheduled", "due_diligence",
            "negotiating", "term_sheet_sent", "invested",
            "rejected", "withdrawn",
        ],
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class ScheduleMeetingSerializer(serializers.Serializer):
    meeting_url = serializers.URLField(required=False, allow_blank=True)
    meeting_time = serializers.DateTimeField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)


class SendTermSheetSerializer(serializers.Serializer):
    amount_offered = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True,
    )
    equity_offered = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True,
    )
    valuation = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True,
    )
    term_sheet_url = serializers.URLField(required=False, allow_blank=True)


class MarkInvestedSerializer(serializers.Serializer):
    amount_offered = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True,
    )
    equity_offered = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True,
    )
    valuation = serializers.DecimalField(
        max_digits=15, decimal_places=2, required=False, allow_null=True,
    )


class RejectDealSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class WithdrawDealSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class InvestorAnalyticsSerializer(serializers.Serializer):
    total_deals = serializers.IntegerField()
    active_deals = serializers.IntegerField()
    invested_deals = serializers.IntegerField()
    rejected_deals = serializers.IntegerField()
    withdrawn_deals = serializers.IntegerField()
    avg_ticket_size = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    total_invested = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    conversion_rate = serializers.FloatField()
    by_stage = serializers.DictField(child=serializers.IntegerField())


class StartupAnalyticsSerializer(serializers.Serializer):
    interested_investors = serializers.IntegerField()
    active_negotiations = serializers.IntegerField()
    invested_deals = serializers.IntegerField()
    funds_raised = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    pipeline_value = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    total_offers = serializers.IntegerField()
    by_stage = serializers.DictField(child=serializers.IntegerField())
