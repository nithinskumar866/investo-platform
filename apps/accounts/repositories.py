from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg

from .models import EntrepreneurProfile, InvestorProfile

User = get_user_model()


class UserRepository:
    """
    Data access layer for User operations.

    Why a separate repository:
    Queries are abstracted behind methods. If we later add caching
    (Redis for frequent user lookups), we change the repository
    implementation, not the services that call it.

    Methods are deliberately thin now. They become richer as we add
    features like user feed filtering, admin user search, etc.
    """

    @staticmethod
    def get_by_email(email: str):
        return User.objects.filter(email=email.lower().strip()).first()

    @staticmethod
    def get_by_id(user_id: int):
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def email_exists(email: str) -> bool:
        return User.objects.filter(email=email.lower().strip()).exists()

    @staticmethod
    def get_active_users():
        return User.objects.filter(is_active=True)

    @staticmethod
    def get_users_by_role(role: str):
        return User.objects.filter(role=role, is_active=True)


class EntrepreneurProfileRepository:
    """Data access layer for entrepreneur profiles."""

    @staticmethod
    def get_by_user(user) -> EntrepreneurProfile | None:
        try:
            return EntrepreneurProfile.objects.select_related("user").get(user=user)
        except EntrepreneurProfile.DoesNotExist:
            return None

    @staticmethod
    def get_or_create(user) -> EntrepreneurProfile:
        profile, _ = EntrepreneurProfile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def get_public_profiles():
        return EntrepreneurProfile.objects.filter(
            is_public=True,
            user__is_active=True,
        ).select_related("user").only(
            "id", "company_name", "tagline", "industry", "funding_stage",
            "city", "country", "team_size", "is_public",
            "user__id", "user__first_name", "user__last_name", "user__avatar",
        )

    @staticmethod
    def search_public_profiles(query: str):
        return EntrepreneurProfileRepository.get_public_profiles().filter(
            Q(company_name__icontains=query)
            | Q(tagline__icontains=query)
            | Q(industry__icontains=query)
            | Q(city__icontains=query)
            | Q(company_description__icontains=query)
        )

    @staticmethod
    def get_by_industry(industry: str):
        return EntrepreneurProfileRepository.get_public_profiles().filter(
            industry__iexact=industry,
        )

    @staticmethod
    def update_profile(profile, data: dict) -> EntrepreneurProfile:
        for field, value in data.items():
            setattr(profile, field, value)
        profile.save()
        return profile

    @staticmethod
    def get_startups_for_entrepreneur(user):
        from apps.startups.models import Startup
        return Startup.objects.filter(owner=user).select_related(
            "metrics",
        ).order_by("-created_at")

    @staticmethod
    def get_profile_completeness(profile) -> dict:
        fields = [
            "company_name", "company_description", "tagline", "website",
            "industry", "funding_stage", "linkedin_url", "team_size",
            "achievements", "city", "country",
        ]
        total = len(fields)
        filled = sum(1 for f in fields if getattr(profile, f, None))
        return {
            "total": total,
            "filled": filled,
            "percentage": round((filled / total) * 100) if total else 0,
            "missing": [f for f in fields if not getattr(profile, f, None)],
        }


class InvestorProfileRepository:
    """Data access layer for investor profiles."""

    @staticmethod
    def get_by_user(user) -> InvestorProfile | None:
        try:
            return InvestorProfile.objects.select_related("user").get(user=user)
        except InvestorProfile.DoesNotExist:
            return None

    @staticmethod
    def get_or_create(user) -> InvestorProfile:
        profile, _ = InvestorProfile.objects.get_or_create(user=user)
        return profile

    @staticmethod
    def get_public_profiles():
        return InvestorProfile.objects.filter(
            is_public=True,
            user__is_active=True,
            user__role="investor",
        ).select_related("user").only(
            "id", "investor_type", "tagline", "preferred_industries",
            "preferred_stages", "ticket_size_min", "ticket_size_max",
            "preferred_geographies", "city", "country",
            "years_of_experience", "investments_completed",
            "lead_investor", "follow_on_investor", "is_public",
            "user__id", "user__first_name", "user__last_name", "user__avatar",
        )

    @staticmethod
    def search_public_profiles(query: str):
        return InvestorProfileRepository.get_public_profiles().filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(tagline__icontains=query)
            | Q(investment_focus__icontains=query)
            | Q(bio__icontains=query)
            | Q(city__icontains=query)
            | Q(country__icontains=query)
        )

    @staticmethod
    def filter_profiles(
        industry=None, geography=None,
        ticket_min: Decimal = None, ticket_max: Decimal = None,
    ):
        qs = InvestorProfileRepository.get_public_profiles()
        if industry:
            qs = qs.filter(preferred_industries__contains=[industry])
        if geography:
            qs = qs.filter(preferred_geographies__contains=[geography])
        if ticket_min is not None:
            qs = qs.filter(ticket_size_max__gte=ticket_min)
        if ticket_max is not None:
            qs = qs.filter(ticket_size_min__lte=ticket_max)
        return qs

    @staticmethod
    def get_by_industry(industry: str):
        return InvestorProfileRepository.get_public_profiles().filter(
            preferred_industries__contains=[industry],
        )

    @staticmethod
    def get_by_geography(geo: str):
        return InvestorProfileRepository.get_public_profiles().filter(
            preferred_geographies__contains=[geo],
        )

    @staticmethod
    def update_profile(profile, data: dict) -> InvestorProfile:
        for field, value in data.items():
            setattr(profile, field, value)
        profile.save()
        return profile

    @staticmethod
    def get_profile_completeness(profile) -> dict:
        fields = [
            "investor_type", "bio", "tagline", "investment_focus",
            "preferred_industries", "preferred_stages",
            "ticket_size_min", "ticket_size_max",
            "preferred_geographies", "linkedin_url", "website_url",
            "city", "country", "years_of_experience",
        ]
        total = len(fields)
        filled = sum(1 for f in fields if getattr(profile, f, None))
        return {
            "total": total,
            "filled": filled,
            "percentage": round((filled / total) * 100) if total else 0,
            "missing": [f for f in fields if not getattr(profile, f, None)],
        }

    @staticmethod
    def get_investor_statistics():
        qs = InvestorProfile.objects.filter(user__is_active=True, user__role="investor")
        return {
            "total_investors": qs.count(),
            "by_type": dict(
                qs.values("investor_type").annotate(count=Count("id"))
                .values_list("investor_type", "count")
            ),
            "avg_ticket_min": qs.aggregate(avg=Avg("ticket_size_min"))["avg"],
            "avg_ticket_max": qs.aggregate(avg=Avg("ticket_size_max"))["avg"],
            "avg_experience": qs.aggregate(avg=Avg("years_of_experience"))["avg"],
            "lead_investors": qs.filter(lead_investor=True).count(),
            "public_profiles": qs.filter(is_public=True).count(),
        }
