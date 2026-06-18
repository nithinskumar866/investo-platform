from rest_framework import serializers

from .models import SavedSearch, SearchHistory


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = ["id", "name", "search_type", "filters", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]


class SaveSearchSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    search_type = serializers.ChoiceField(
        choices=["startups", "investors", "founders", "opportunities"],
    )
    filters = serializers.JSONField(default=dict)


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ["id", "query", "search_type", "filters", "results_count", "created_at"]
        read_only_fields = fields


class SearchStartupResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    tagline = serializers.CharField()
    industry = serializers.CharField()
    stage = serializers.CharField()
    location = serializers.CharField()
    funding_goal = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    valuation = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    team_size = serializers.IntegerField(allow_null=True)
    is_verified = serializers.BooleanField()
    status = serializers.CharField()
    logo = serializers.ImageField(allow_null=True)
    owner_email = serializers.EmailField(source="owner.email")
    relevance = serializers.IntegerField()


class SearchInvestorResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    investor_type = serializers.SerializerMethodField()
    tagline = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    ticket_size_min = serializers.SerializerMethodField()
    ticket_size_max = serializers.SerializerMethodField()
    lead_investor = serializers.SerializerMethodField()
    years_of_experience = serializers.SerializerMethodField()
    investments_completed = serializers.SerializerMethodField()
    relevance = serializers.IntegerField()

    def get_investor_type(self, obj):
        p = getattr(obj, "investor_profile", None)
        return p.investor_type if p else None

    def get_tagline(self, obj):
        p = getattr(obj, "investor_profile", None)
        return p.tagline if p else ""

    def get_bio(self, obj):
        p = getattr(obj, "investor_profile", None)
        return p.bio if p else ""

    def get_ticket_size_min(self, obj):
        pref = getattr(obj, "investor_preferences", None)
        return float(pref.min_ticket_size) if pref and pref.min_ticket_size else None

    def get_ticket_size_max(self, obj):
        pref = getattr(obj, "investor_preferences", None)
        return float(pref.max_ticket_size) if pref and pref.max_ticket_size else None

    def get_lead_investor(self, obj):
        p = getattr(obj, "investor_profile", None)
        return p.lead_investor if p else False

    def get_years_of_experience(self, obj):
        p = getattr(obj, "investor_profile", None)
        return p.years_of_experience if p else None

    def get_investments_completed(self, obj):
        p = getattr(obj, "investor_profile", None)
        return p.investments_completed if p else None


class SearchFounderResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    company_name = serializers.SerializerMethodField()
    tagline = serializers.SerializerMethodField()
    industry = serializers.SerializerMethodField()
    funding_stage = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()
    relevance = serializers.IntegerField()

    def get_company_name(self, obj):
        p = getattr(obj, "entrepreneur_profile", None)
        return p.company_name if p else ""

    def get_tagline(self, obj):
        p = getattr(obj, "entrepreneur_profile", None)
        return p.tagline if p else ""

    def get_industry(self, obj):
        p = getattr(obj, "entrepreneur_profile", None)
        return p.industry if p else ""

    def get_funding_stage(self, obj):
        p = getattr(obj, "entrepreneur_profile", None)
        return p.funding_stage if p else ""

    def get_city(self, obj):
        p = getattr(obj, "entrepreneur_profile", None)
        return p.city if p else ""

    def get_country(self, obj):
        p = getattr(obj, "entrepreneur_profile", None)
        return p.country if p else ""

    def get_achievements(self, obj):
        p = getattr(obj, "entrepreneur_profile", None)
        return p.achievements if p else ""


class SearchOpportunityResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    startup_name = serializers.CharField(source="startup.name")
    investor_email = serializers.EmailField(source="investor.email")
    status = serializers.CharField()
    amount_requested = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    created_at = serializers.DateTimeField()


class AutocompleteResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()
    subtitle = serializers.CharField()
    type = serializers.CharField()


class SearchAnalyticsSerializer(serializers.Serializer):
    total_searches = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    ctr = serializers.FloatField()
    top_queries = serializers.ListField()
    by_type = serializers.ListField()
    last_7_days = serializers.IntegerField()


class RecommendedResultSerializer(serializers.Serializer):
    startups = serializers.ListField()
    investors = serializers.ListField()
    trending_startups = serializers.ListField()
    recently_funded = serializers.ListField()
