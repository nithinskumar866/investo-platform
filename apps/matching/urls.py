from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"investor/matches", views.InvestorMatchViewSet, basename="investor-match")
router.register(r"entrepreneur/matches", views.EntrepreneurMatchViewSet, basename="entrepreneur-match")

urlpatterns = [
    # Legacy function-based endpoints
    path("matches/", views.my_matches, name="matching-matches"),
    path("preferences/", views.investor_preferences, name="matching-preferences"),
    path("interact/", views.interact, name="matching-interact"),
    path("history/", views.interaction_history, name="matching-history"),
    path("analytics/", views.match_analytics, name="matching-analytics"),
]

urlpatterns += router.urls
