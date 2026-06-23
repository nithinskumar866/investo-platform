from django.contrib import admin

from .models import Coupon, Invoice, SubscriptionPlan, UserSubscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "tier", "monthly_price", "yearly_price", "is_active", "is_popular", "sort_order"]
    list_filter = ["tier", "is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "status", "billing_cycle", "start_date", "end_date", "auto_renew"]
    list_filter = ["status", "billing_cycle", "plan"]
    search_fields = ["user__email", "user__first_name"]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "user", "amount", "status", "billing_cycle", "created_at"]
    list_filter = ["status", "billing_cycle"]
    search_fields = ["invoice_number", "user__email"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "discount_value", "usage_limit", "used_count", "is_active", "expires_at"]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code"]
