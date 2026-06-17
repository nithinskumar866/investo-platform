from django.urls import path

from . import views

urlpatterns = [
    path("matches/", views.my_matches, name="matching-matches"),
    path("matches/<int:startup_id>/", views.match_detail, name="matching-detail"),
    path("recommended/", views.recommended_startups, name="matching-recommended"),
    path("interact/", views.interact, name="matching-interact"),
    path("history/", views.interaction_history, name="matching-history"),
    path("analytics/", views.match_analytics, name="matching-analytics"),
    path("preferences/", views.investor_preferences, name="matching-preferences"),
]
