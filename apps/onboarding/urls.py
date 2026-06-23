from django.urls import path

from . import views

urlpatterns = [
    path("start/", views.start_onboarding, name="onboarding-start"),
    path("progress/", views.onboarding_progress, name="onboarding-progress"),
    path("step/", views.complete_step, name="onboarding-step"),
    path("complete/", views.complete_onboarding, name="onboarding-complete"),
    path("data/founder/", views.founder_onboarding_data, name="onboarding-data-founder"),
    path("data/investor/", views.investor_onboarding_data, name="onboarding-data-investor"),
]
