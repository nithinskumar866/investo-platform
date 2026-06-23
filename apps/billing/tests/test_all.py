import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User
from apps.billing.models import (
    SubscriptionPlan, UserSubscription, Invoice, Coupon,
)
from apps.billing.services import BillingService
from apps.common.exceptions import ApplicationError


# ── User fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def founder(db):
    return User.objects.create_user(
        email="founder@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123",
    )


@pytest.fixture
def plans(db):
    data = [
        ("Free", "free", "free", Decimal("0.00"), Decimal("0.00"), 0),
        ("Founder Premium", "founder_premium", "founder_premium",
         Decimal("29.99"), Decimal("299.99"), 1),
        ("Investor Premium", "investor_premium", "investor_premium",
         Decimal("49.99"), Decimal("499.99"), 2),
        ("Enterprise", "enterprise", "enterprise",
         Decimal("99.99"), Decimal("999.99"), 3),
    ]
    plans_list = []
    for name, slug, tier, monthly, yearly, sort in data:
        p, _ = SubscriptionPlan.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "tier": tier,
                "monthly_price": monthly,
                "yearly_price": yearly,
                "sort_order": sort,
                "is_active": True,
                "features": {"analytics": True},
                "limits": {"matches": 100},
            },
        )
        plans_list.append(p)
    return plans_list


@pytest.fixture
def free_plan(plans):
    return plans[0]


@pytest.fixture
def premium_plan(plans):
    return plans[1]


@pytest.fixture
def coupon(db):
    return Coupon.objects.create(
        code="SAVE20",
        discount_type=Coupon.DiscountType.PERCENTAGE,
        discount_value=Decimal("20.00"),
        is_active=True,
        expires_at=timezone.now() + timedelta(days=30),
    )


@pytest.fixture
def subscription(db, user, premium_plan):
    return UserSubscription.objects.create(
        user=user,
        plan=premium_plan,
        status=UserSubscription.Status.ACTIVE,
        billing_cycle=UserSubscription.BillingCycle.MONTHLY,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        auto_renew=True,
    )


# ── Model tests ──────────────────────────────────────────────────────────

class TestSubscriptionPlanModel:
    def test_seed_plans(self, plans):
        assert len(plans) == 4
        assert plans[0].tier == SubscriptionPlan.Tier.FREE
        assert plans[2].tier == SubscriptionPlan.Tier.INVESTOR_PREMIUM

    def test_plan_ordering(self, plans):
        slugs = [p.slug for p in plans]
        assert slugs == ["free", "founder_premium", "investor_premium", "enterprise"]


class TestUserSubscriptionModel:
    def test_lifecycle(self, user, premium_plan):
        sub = UserSubscription.objects.create(
            user=user, plan=premium_plan,
            status=UserSubscription.Status.TRIAL,
        )
        assert sub.status == UserSubscription.Status.TRIAL
        sub.status = UserSubscription.Status.ACTIVE
        sub.save()
        sub.status = UserSubscription.Status.CANCELLED
        sub.save()
        sub.refresh_from_db()
        assert sub.status == UserSubscription.Status.CANCELLED

    def test_subscription_str(self, subscription):
        assert "user@example.com" in str(subscription)


class TestInvoiceModel:
    def test_create_on_subscription(self, user, subscription, premium_plan):
        inv = Invoice.objects.create(
            user=user,
            subscription=subscription,
            plan=premium_plan,
            amount=Decimal("29.99"),
            status=Invoice.Status.PAID,
            invoice_number="INV-TEST-001",
        )
        assert inv.pk is not None
        assert inv.status == Invoice.Status.PAID

    def test_invoice_ordering(self, user):
        Invoice.objects.create(
            user=user, amount=Decimal("10"), invoice_number="INV-001",
        )
        Invoice.objects.create(
            user=user, amount=Decimal("20"), invoice_number="INV-002",
        )
        qs = Invoice.objects.all()
        assert qs.first().invoice_number == "INV-002"


class TestCouponModel:
    def test_is_valid_active(self, coupon):
        assert coupon.is_valid is True

    def test_is_valid_expired(self, coupon):
        coupon.expires_at = timezone.now() - timedelta(days=1)
        coupon.save()
        assert coupon.is_valid is False

    def test_is_valid_usage_exceeded(self, coupon):
        coupon.usage_limit = 5
        coupon.used_count = 5
        coupon.save()
        assert coupon.is_valid is False

    def test_is_valid_inactive(self, coupon):
        coupon.is_active = False
        coupon.save()
        assert coupon.is_valid is False


# ── Service tests ────────────────────────────────────────────────────────

class TestBillingService:
    def test_get_plans(self, plans):
        result = BillingService.get_plans()
        assert len(result) == 4

    def test_get_subscription_creates_free(self, user, free_plan):
        sub = BillingService.get_subscription(user)
        assert sub is not None
        assert sub.plan.tier == SubscriptionPlan.Tier.FREE

    def test_subscribe(self, user, premium_plan):
        sub = BillingService.subscribe(user, "founder_premium")
        assert sub.plan.slug == "founder_premium"
        assert sub.status == UserSubscription.Status.ACTIVE
        assert Invoice.objects.filter(user=user).count() == 1

    def test_subscribe_invalid_plan(self, user):
        with pytest.raises(ApplicationError, match="not found"):
            BillingService.subscribe(user, "nonexistent")

    def test_subscribe_free_plan_raises(self, user, free_plan):
        with pytest.raises(ApplicationError, match="Cannot subscribe"):
            BillingService.subscribe(user, "free")

    def test_subscribe_with_coupon(self, user, premium_plan, coupon):
        sub = BillingService.subscribe(
            user, "founder_premium", coupon_code="SAVE20",
        )
        assert sub.coupon == coupon

    def test_subscribe_already_subscribed(self, subscription, premium_plan):
        with pytest.raises(ApplicationError, match="Already subscribed"):
            BillingService.subscribe(subscription.user, "founder_premium")

    def test_cancel_subscription(self, subscription):
        sub = BillingService.cancel_subscription(subscription.user)
        assert sub.status == UserSubscription.Status.CANCELLED

    def test_cancel_no_subscription(self, user):
        with pytest.raises(ApplicationError, match="No active subscription"):
            BillingService.cancel_subscription(user)

    def test_renew_subscription(self, subscription):
        sub = BillingService.renew_subscription(subscription.user)
        assert sub.status == UserSubscription.Status.ACTIVE

    def test_apply_coupon(self, subscription, coupon):
        result = BillingService.apply_coupon(subscription.user, "SAVE20")
        assert "original_price" in result
        assert "discounted_price" in result

    def test_apply_invalid_coupon(self, subscription):
        with pytest.raises(ApplicationError, match="Invalid coupon"):
            BillingService.apply_coupon(subscription.user, "INVALID")

    def test_get_invoices(self, subscription, user):
        Invoice.objects.create(
            user=user, subscription=subscription,
            plan=subscription.plan,
            amount=Decimal("29.99"), status=Invoice.Status.PAID,
            invoice_number="INV-NUM-001",
        )
        invoices = BillingService.get_invoices(user)
        assert len(invoices) == 1

    def test_get_features(self, user, plans):
        data = BillingService.get_features(user)
        assert len(data) == 4
        assert any(d["slug"] == "free" for d in data)

    def test_get_usage(self, user, free_plan):
        usage = BillingService.get_usage(user)
        assert "plan" in usage
        assert "usage" in usage

    def test_check_feature_access(self, user):
        result = BillingService.check_feature_access(user, "analytics")
        assert "has_access" in result

    def test_check_usage_limit(self, user):
        result = BillingService.check_usage_limit(user, "matches", current_count=5)
        assert "within_limit" in result


# ── View tests ──────────────────────────────────────────────────────────

class TestBillingViews:
    def test_plan_list(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/billing/plans/")
        assert resp.status_code == 200

    def test_subscription_detail(self, authenticated_client, subscription):
        resp = authenticated_client.get("/api/v1/billing/subscription/")
        assert resp.status_code == 200

    def test_subscribe(self, authenticated_client, premium_plan):
        resp = authenticated_client.post(
            "/api/v1/billing/subscribe/",
            {"plan_slug": "founder_premium"},
            format="json",
        )
        assert resp.status_code == 201

    def test_cancel(self, authenticated_client, subscription):
        resp = authenticated_client.post("/api/v1/billing/cancel/")
        assert resp.status_code == 200

    def test_renew(self, authenticated_client, subscription):
        resp = authenticated_client.post("/api/v1/billing/renew/")
        assert resp.status_code == 200

    def test_apply_coupon(self, authenticated_client, subscription, coupon):
        resp = authenticated_client.post(
            "/api/v1/billing/apply-coupon/",
            {"coupon_code": "SAVE20"},
            format="json",
        )
        assert resp.status_code == 200

    def test_invoices(self, authenticated_client, subscription):
        resp = authenticated_client.get("/api/v1/billing/invoices/")
        assert resp.status_code == 200

    def test_usage(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/billing/usage/")
        assert resp.status_code == 200

    def test_features(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/billing/features/")
        assert resp.status_code == 200
