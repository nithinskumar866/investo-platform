import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.onboarding.models import (
    OnboardingWizard, OnboardingStep, FounderOnboardingData, InvestorOnboardingData,
)
from apps.onboarding.services import OnboardingService


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
def founder_wizard(db, founder):
    wizard = OnboardingWizard.objects.create(
        user=founder,
        wizard_type=OnboardingWizard.WizardType.FOUNDER,
        current_step="company_info",
    )
    for key, label in [
        ("company_info", "Company Information"),
        ("business_model", "Business Model"),
        ("traction", "Traction & Competitors"),
        ("pitch_deck", "Pitch Deck"),
        ("review", "Review & Complete"),
    ]:
        OnboardingStep.objects.create(wizard=wizard, step_key=key, step_label=label)
    return wizard


@pytest.fixture
def investor_wizard(db, investor):
    wizard = OnboardingWizard.objects.create(
        user=investor,
        wizard_type=OnboardingWizard.WizardType.INVESTOR,
        current_step="profile",
    )
    for key, label in [
        ("profile", "Profile & Bio"),
        ("focus", "Investment Focus"),
        ("ticket", "Ticket Size & Geography"),
        ("experience", "Experience"),
        ("review", "Review & Complete"),
    ]:
        OnboardingStep.objects.create(wizard=wizard, step_key=key, step_label=label)
    return wizard


# ── Model tests ──────────────────────────────────────────────────────────

class TestOnboardingWizardModel:
    def test_create_founder_wizard(self, founder_wizard):
        assert founder_wizard.pk is not None
        assert founder_wizard.wizard_type == "founder"
        assert str(founder_wizard) == "founder wizard for founder@example.com"

    def test_create_investor_wizard(self, investor_wizard):
        assert investor_wizard.pk is not None
        assert investor_wizard.wizard_type == "investor"


class TestOnboardingStepModel:
    def test_create_step(self, founder_wizard):
        step = founder_wizard.steps.first()
        assert step is not None
        assert step.step_key == "company_info"

    def test_step_ordering(self, founder_wizard):
        steps = founder_wizard.steps.all()
        assert steps[0].step_key == "company_info"
        assert steps[4].step_key == "review"


class TestFounderOnboardingDataModel:
    def test_create(self, founder):
        data = FounderOnboardingData.objects.create(
            user=founder,
            company_name="My Startup",
            industry="ai_ml",
        )
        assert data.pk is not None
        assert str(data) == "Founder data for founder@example.com"


class TestInvestorOnboardingDataModel:
    def test_create(self, investor):
        data = InvestorOnboardingData.objects.create(
            user=investor,
            investor_type="angel",
            bio="Experienced angel investor",
            preferred_industries=["ai_ml", "fintech"],
        )
        assert data.pk is not None
        assert str(data) == "Investor data for investor@example.com"


# ── Service tests ────────────────────────────────────────────────────────

class TestOnboardingService:
    def test_start_onboarding_founder(self, founder):
        wizard = OnboardingService.start_onboarding(founder, "founder")
        assert wizard.wizard_type == "founder"
        assert wizard.steps.count() == 5
        assert wizard.current_step == "company_info"

    def test_start_onboarding_investor(self, investor):
        wizard = OnboardingService.start_onboarding(investor, "investor")
        assert wizard.wizard_type == "investor"
        assert wizard.steps.count() == 5
        assert wizard.current_step == "profile"

    def test_get_progress(self, founder_wizard):
        progress = OnboardingService.get_progress(founder_wizard.user)
        assert progress is not None
        assert progress["total_steps"] == 5
        assert progress["completed_steps"] == 0
        assert progress["is_complete"] is False

    def test_get_progress_no_wizard(self, user):
        progress = OnboardingService.get_progress(user)
        assert progress is None

    def test_complete_step(self, founder_wizard):
        progress = OnboardingService.complete_step(
            founder_wizard.user, "company_info",
            {"company_name": "TestCo", "industry": "ai_ml"},
        )
        assert progress is not None
        assert progress["completed_steps"] == 1
        assert progress["current_step"] == "business_model"

    def test_complete_step_invalid_key(self, founder_wizard):
        progress = OnboardingService.complete_step(
            founder_wizard.user, "invalid_key", {},
        )
        assert progress is None

    def test_complete_step_no_wizard(self, user):
        progress = OnboardingService.complete_step(user, "step1", {})
        assert progress is None

    def test_complete_onboarding(self, founder_wizard):
        wizard = OnboardingService.complete_onboarding(founder_wizard.user)
        assert wizard.is_complete is True
        assert FounderOnboardingData.objects.filter(user=founder_wizard.user).exists()

    def test_complete_onboarding_no_wizard(self, user):
        wizard = OnboardingService.complete_onboarding(user)
        assert wizard is None

    def test_complete_onboarding_investor(self, investor_wizard):
        wizard = OnboardingService.complete_onboarding(investor_wizard.user)
        assert wizard.is_complete is True
        assert InvestorOnboardingData.objects.filter(user=investor_wizard.user).exists()

    def test_get_founder_data(self, founder):
        data = OnboardingService.get_founder_data(founder)
        assert data is not None
        assert data.user == founder

    def test_get_investor_data(self, investor):
        data = OnboardingService.get_investor_data(investor)
        assert data is not None
        assert data.user == investor

    def test_full_flow(self, founder):
        wizard = OnboardingService.start_onboarding(founder, "founder")
        for step_key in ["company_info", "business_model", "traction", "pitch_deck"]:
            OnboardingService.complete_step(founder, step_key, {"done": True})
        progress = OnboardingService.get_progress(founder)
        assert progress["completed_steps"] == 4
        assert progress["current_step"] == "review"
        OnboardingService.complete_step(founder, "review", {"agreed": True})
        wizard = OnboardingService.complete_onboarding(founder)
        assert wizard.is_complete is True


# ── View tests ──────────────────────────────────────────────────────────

class TestOnboardingViews:
    def test_start_onboarding_founder(self, founder_client):
        resp = founder_client.post(
            "/api/v1/onboarding/start/",
            {"wizard_type": "founder"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "success"

    def test_start_onboarding_investor(self, investor_client):
        resp = investor_client.post(
            "/api/v1/onboarding/start/",
            {"wizard_type": "investor"},
            format="json",
        )
        assert resp.status_code == 201

    def test_progress(self, founder_client, founder_wizard):
        resp = founder_client.get("/api/v1/onboarding/progress/")
        assert resp.status_code == 200

    def test_progress_no_wizard(self, user):
        from conftest import get_tokens_for_user
        from rest_framework.test import APIClient
        client = APIClient()
        tokens = get_tokens_for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        resp = client.get("/api/v1/onboarding/progress/")
        assert resp.status_code == 404

    def test_complete_step(self, founder_client, founder_wizard):
        resp = founder_client.post(
            "/api/v1/onboarding/step/",
            {"step_key": "company_info", "data": {"company_name": "TestCo"}},
            format="json",
        )
        assert resp.status_code == 200

    def test_complete_step_missing_key(self, founder_client):
        resp = founder_client.post(
            "/api/v1/onboarding/step/",
            {"data": {}},
            format="json",
        )
        assert resp.status_code == 400

    def test_complete_onboarding(self, founder_client, founder_wizard):
        resp = founder_client.post("/api/v1/onboarding/complete/")
        assert resp.status_code == 200

    def test_founder_data_get(self, founder_client):
        resp = founder_client.get("/api/v1/onboarding/data/founder/")
        assert resp.status_code == 200

    def test_founder_data_update(self, founder_client):
        resp = founder_client.post(
            "/api/v1/onboarding/data/founder/",
            {"company_name": "UpdatedCo"},
            format="json",
        )
        assert resp.status_code == 200

    def test_investor_data_get(self, investor_client):
        resp = investor_client.get("/api/v1/onboarding/data/investor/")
        assert resp.status_code == 200

    def test_investor_data_update(self, investor_client):
        resp = investor_client.post(
            "/api/v1/onboarding/data/investor/",
            {"bio": "Updated bio"},
            format="json",
        )
        assert resp.status_code == 200

    def test_founder_data_permission(self, investor_client):
        resp = investor_client.get("/api/v1/onboarding/data/founder/")
        assert resp.status_code == 403

    def test_investor_data_permission(self, founder_client):
        resp = founder_client.get("/api/v1/onboarding/data/investor/")
        assert resp.status_code == 403
