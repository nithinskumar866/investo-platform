from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("register/", views.register, name="auth-register"),
    path("login/", views.login, name="auth-login"),
    path("logout/", views.logout, name="auth-logout"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", views.me, name="auth-me"),
    path("profile/entrepreneur/", views.entrepreneur_profile, name="auth-profile-entrepreneur"),
    path("profile/investor/", views.investor_profile, name="auth-profile-investor"),
    path("verify-email/", views.verify_email, name="auth-verify-email"),
    path("resend-verification/", views.resend_verification, name="auth-resend-verification"),
    path("forgot-password/", views.forgot_password, name="auth-forgot-password"),
    path("reset-password/", views.reset_password, name="auth-reset-password"),
]
