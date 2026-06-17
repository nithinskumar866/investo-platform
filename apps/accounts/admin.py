from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

from .models import EntrepreneurProfile, InvestorProfile

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "role", "first_name", "last_name", "is_verified", "is_active", "date_joined"]
    list_filter = ["role", "is_verified", "is_active", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "phone", "avatar")}),
        ("Roles & Status", {"fields": ("role", "is_verified", "email_verified_at", "is_active")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "last_login_ip", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser"),
        }),
    )


@admin.register(EntrepreneurProfile)
class EntrepreneurProfileAdmin(admin.ModelAdmin):
    list_display = ["company_name", "user_email", "industry", "funding_stage", "team_size", "created_at"]
    search_fields = ["company_name", "user__email"]
    list_filter = ["industry", "funding_stage"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"


@admin.register(InvestorProfile)
class InvestorProfileAdmin(admin.ModelAdmin):
    list_display = ["user_email", "investor_type", "preferred_stage", "portfolio_count", "created_at"]
    search_fields = ["user__email"]
    list_filter = ["investor_type", "preferred_stage"]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"
