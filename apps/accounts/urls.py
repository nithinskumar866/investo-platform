from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("register/", views.register, name="auth-register"),
    path("login/", views.login, name="auth-login"),
    path("logout/", views.logout, name="auth-logout"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", views.me, name="auth-me"),
    # Profile endpoints
    path("profile/entrepreneur/", views.entrepreneur_profile, name="auth-profile-entrepreneur"),
    path("profile/entrepreneur/completeness/", views.entrepreneur_profile_completeness, name="auth-profile-entrepreneur-completeness"),
    path("profile/entrepreneur/startups/", views.entrepreneur_profile_startups, name="auth-profile-entrepreneur-startups"),
    path("profile/investor/", views.investor_profile, name="auth-profile-investor"),
    path("profile/investor/completeness/", views.investor_profile_completeness, name="auth-profile-investor-completeness"),
    path("profile/investor/statistics/", views.investor_profile_statistics, name="auth-profile-investor-statistics"),
    # Public profiles
    path("profiles/entrepreneur/", views.public_entrepreneur_profiles, name="public-entrepreneur-profiles"),
    path("profiles/entrepreneur/<int:profile_id>/", views.public_entrepreneur_profile_detail, name="public-entrepreneur-profile-detail"),
    path("profiles/investor/", views.public_investor_profiles, name="public-investor-profiles"),
    path("profiles/investor/<int:profile_id>/", views.public_investor_profile_detail, name="public-investor-profile-detail"),
    # Authentication
    path("verify-email/", views.verify_email, name="auth-verify-email"),
    path("resend-verification/", views.resend_verification, name="auth-resend-verification"),
    path("forgot-password/", views.forgot_password, name="auth-forgot-password"),
    path("reset-password/", views.reset_password, name="auth-reset-password"),
]
