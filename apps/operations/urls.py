from django.urls import path

from . import views

urlpatterns = [
    # Dashboard
    path("dashboard/", views.dashboard, name="ops-dashboard"),
    # User management
    path("users/", views.user_list, name="ops-user-list"),
    path("users/<int:user_id>/", views.user_detail, name="ops-user-detail"),
    path("users/<int:user_id>/suspend/", views.user_suspend, name="ops-user-suspend"),
    path("users/<int:user_id>/restore/", views.user_restore, name="ops-user-restore"),
    path("users/<int:user_id>/verify/", views.user_verify, name="ops-user-verify"),
    # Startup moderation
    path("startups/", views.startup_list, name="ops-startup-list"),
    path("startups/<int:startup_id>/", views.startup_detail, name="ops-startup-detail"),
    path("startups/<int:startup_id>/moderate/", views.startup_moderate, name="ops-startup-moderate"),
    path("startups/<int:startup_id>/verify/", views.startup_verify, name="ops-startup-verify"),
    # Investment oversight
    path("investments/", views.investment_list, name="ops-investment-list"),
    path("investments/pipeline/", views.pipeline_health, name="ops-pipeline-health"),
    # Data room moderation
    path("documents/", views.document_list, name="ops-document-list"),
    path("documents/<int:document_id>/views/", views.document_views, name="ops-document-views"),
    # Support tickets
    path("tickets/", views.ticket_list, name="ops-ticket-list"),
    path("tickets/create/", views.ticket_create, name="ops-ticket-create"),
    path("tickets/<int:ticket_id>/", views.ticket_detail, name="ops-ticket-detail"),
    path("tickets/<int:ticket_id>/update/", views.ticket_update, name="ops-ticket-update"),
    path("tickets/<int:ticket_id>/messages/", views.ticket_messages, name="ops-ticket-messages"),
    path("tickets/<int:ticket_id>/send/", views.ticket_send_message, name="ops-ticket-send"),
    # Audit logs
    path("audit/", views.audit_log_list, name="ops-audit-list"),
    path("audit/<int:log_id>/", views.audit_log_detail, name="ops-audit-detail"),
    # Revenue analytics
    path("revenue/", views.revenue, name="ops-revenue"),
    # Risk monitoring
    path("risk/", views.risk, name="ops-risk"),
]
