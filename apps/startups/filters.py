import django_filters
from django.db import models

from .models import Startup


class StartupFilter(django_filters.FilterSet):
    industry = django_filters.CharFilter(lookup_expr="exact")
    stage = django_filters.CharFilter(lookup_expr="exact")
    status = django_filters.CharFilter(lookup_expr="exact")
    is_verified = django_filters.BooleanFilter()
    min_funding_goal = django_filters.NumberFilter(field_name="funding_goal", lookup_expr="gte")
    max_funding_goal = django_filters.NumberFilter(field_name="funding_goal", lookup_expr="lte")
    min_equity = django_filters.NumberFilter(field_name="equity_offered", lookup_expr="gte")
    max_equity = django_filters.NumberFilter(field_name="equity_offered", lookup_expr="lte")
    min_team_size = django_filters.NumberFilter(field_name="team_size", lookup_expr="gte")
    max_team_size = django_filters.NumberFilter(field_name="team_size", lookup_expr="lte")
    min_valuation = django_filters.NumberFilter(field_name="valuation", lookup_expr="gte")
    max_valuation = django_filters.NumberFilter(field_name="valuation", lookup_expr="lte")
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Startup
        fields = [
            "industry", "stage", "status", "is_verified",
            "business_model", "location",
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(name__icontains=value)
            | models.Q(tagline__icontains=value)
            | models.Q(description__icontains=value)
            | models.Q(location__icontains=value)
        )
