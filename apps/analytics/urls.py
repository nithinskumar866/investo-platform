from django.urls import path

from . import views

urlpatterns = [
    path("founder/dashboard/", views.founder_dashboard, name="analytics-founder-dashboard"),
    path("investor/dashboard/", views.investor_dashboard, name="analytics-investor-dashboard"),
    path("founder/funnel/", views.founder_funnel, name="analytics-founder-funnel"),
    path("investor/funnel/", views.investor_funnel, name="analytics-investor-funnel"),
    path("founder/charts/", views.founder_charts, name="analytics-founder-charts"),
    path("investor/charts/", views.investor_charts, name="analytics-investor-charts"),
    path("reports/", views.reports, name="analytics-reports"),
]
