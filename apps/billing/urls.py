from django.urls import path

from . import views

urlpatterns = [
    path("plans/", views.plan_list, name="billing-plans"),
    path("subscription/", views.subscription_detail, name="billing-subscription"),
    path("subscribe/", views.subscribe, name="billing-subscribe"),
    path("cancel/", views.cancel_subscription, name="billing-cancel"),
    path("renew/", views.renew_subscription, name="billing-renew"),
    path("apply-coupon/", views.apply_coupon, name="billing-apply-coupon"),
    path("invoices/", views.invoice_list, name="billing-invoices"),
    path("usage/", views.usage, name="billing-usage"),
    path("features/", views.features, name="billing-features"),
]
