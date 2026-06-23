import datetime
import factory
import factory.fuzzy
from decimal import Decimal
from factory.django import DjangoModelFactory
from django.utils import timezone

from apps.accounts.models import User, EntrepreneurProfile, InvestorProfile
from apps.startups.models import (
    Startup, StartupTeamMember, StartupSocialLink, StartupDocument,
    StartupFundingRound, StartupMetric,
)
from apps.matching.models import (
    InvestorPreference, MatchScore, SavedMatch, DismissedMatch, InteractionEvent,
)
from apps.chat.models import Conversation, ConversationParticipant, Message, MessageReadStatus
from apps.meetings.models import Meeting, MeetingParticipant, MeetingAvailability, MeetingEvent
from apps.investments.models import InvestmentOpportunity, InvestmentActivity
from apps.data_room.models import DataRoom, DataRoomDocument, DocumentAccess, DocumentViewEvent
from apps.notifications.models import Notification, NotificationPreference
from apps.activity_feed.models import ActivityFeed, FeedReaction, FeedBookmark, FeedComment
from apps.billing.models import SubscriptionPlan, UserSubscription, Invoice, Coupon
from apps.operations.models import AuditLog, SupportTicket, SupportMessage
from apps.observability.models import SystemError, RequestMetric, AlertRule, AlertEvent
from apps.settings.models import PlatformSetting, FeatureFlag, MaintenanceMode
from apps.onboarding.models import OnboardingWizard, OnboardingStep, FounderOnboardingData, InvestorOnboardingData
from apps.match_intelligence.models import MatchInsight, MatchFeedback
from apps.search_app.models import SavedSearch, SearchHistory, SearchClickEvent


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

class EntrepreneurProfileFactory(DjangoModelFactory):
    class Meta:
        model = EntrepreneurProfile

    user = factory.SubFactory('apps.common.tests.factories.UserFactory')
    company_name = factory.Sequence(lambda n: f"Acme Corp {n}")
    company_description = factory.Faker('paragraph')
    tagline = factory.Faker('catch_phrase')
    website = factory.Faker('url')
    industry = factory.Iterator([
        'ai_ml', 'fintech', 'healthtech', 'edtech', 'saas', 'ecommerce', 'blockchain', 'cleantech',
    ])
    funding_stage = factory.Iterator([
        'pre_seed', 'seed', 'series_a', 'series_b', 'series_c', 'growth',
    ])
    linkedin_url = factory.Faker('url')
    team_size = factory.Faker('random_int', min=1, max=100)
    achievements = factory.Faker('paragraph')
    city = factory.Faker('city')
    country = factory.Faker('country')
    is_public = True


class InvestorProfileFactory(DjangoModelFactory):
    class Meta:
        model = InvestorProfile

    user = factory.SubFactory('apps.common.tests.factories.UserFactory')
    investor_type = factory.Iterator([
        'angel', 'vc', 'corporate', 'accelerator', 'family_office', 'fund',
    ])
    bio = factory.Faker('paragraph')
    tagline = factory.Faker('catch_phrase')
    investment_focus = factory.Faker('paragraph')
    preferred_industries = ['ai_ml', 'fintech', 'saas']
    preferred_stages = ['seed', 'series_a']
    ticket_size_min = Decimal('50000.00')
    ticket_size_max = Decimal('5000000.00')
    preferred_geographies = ['North America', 'Europe']
    portfolio_companies = factory.List([factory.Faker('company') for _ in range(3)])
    linkedin_url = factory.Faker('url')
    website_url = factory.Faker('url')
    city = factory.Faker('city')
    country = factory.Faker('country')
    years_of_experience = factory.Faker('random_int', min=1, max=30)
    investments_completed = factory.Faker('random_int', min=0, max=50)
    is_public = True


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    role = User.Role.ENTREPRENEUR
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    phone = factory.Faker('phone_number')
    is_verified = True

    entrepreneur_profile = factory.RelatedFactory(
        EntrepreneurProfileFactory,
        factory_related_name='user',
    )


class FounderFactory(UserFactory):
    pass


class InvestorFactory(UserFactory):
    role = User.Role.INVESTOR
    entrepreneur_profile = None

    investor_profile = factory.RelatedFactory(
        InvestorProfileFactory,
        factory_related_name='user',
    )


class AdminFactory(UserFactory):
    role = User.Role.ADMIN
    is_staff = True
    is_superuser = True
    entrepreneur_profile = None


# ---------------------------------------------------------------------------
# Startups
# ---------------------------------------------------------------------------

class StartupFactory(DjangoModelFactory):
    class Meta:
        model = Startup

    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Startup {n}")
    slug = factory.Sequence(lambda n: f"startup-{n}")
    tagline = factory.Faker('catch_phrase')
    short_description = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    detailed_pitch = factory.Faker('paragraph')
    industry = factory.Iterator(Startup.Industry.values)
    stage = factory.Iterator(Startup.Stage.values)
    business_model = factory.Iterator(Startup.BusinessModel.values)
    funding_goal = Decimal('1000000.00')
    equity_offered = Decimal('10.00')
    valuation = Decimal('5000000.00')
    location = factory.Faker('city')
    website = factory.Faker('url')
    is_visible = True
    status = Startup.Status.ACTIVE
    team_size = factory.Faker('random_int', min=1, max=50)
    founded_date = factory.LazyFunction(lambda: timezone.now().date() - datetime.timedelta(days=365))


class StartupTeamMemberFactory(DjangoModelFactory):
    class Meta:
        model = StartupTeamMember

    startup = factory.SubFactory(StartupFactory)
    name = factory.Faker('name')
    role = factory.Iterator(['CEO', 'CTO', 'COO', 'CMO', 'CFO', 'Lead Engineer', 'Product Manager'])
    email = factory.Sequence(lambda n: f'member{n}@startup.com')
    linkedin_url = factory.Faker('url')
    bio = factory.Faker('paragraph')
    is_founder = factory.Faker('boolean')
    order = factory.Sequence(lambda n: n)


class StartupSocialLinkFactory(DjangoModelFactory):
    class Meta:
        model = StartupSocialLink

    startup = factory.SubFactory(StartupFactory)
    platform = factory.Iterator(StartupSocialLink.Platform.values)
    url = factory.Faker('url')


class StartupDocumentFactory(DjangoModelFactory):
    class Meta:
        model = StartupDocument

    startup = factory.SubFactory(StartupFactory)
    name = factory.Sequence(lambda n: f"Document {n}")
    file = factory.django.FileField(filename='test_doc.pdf')
    document_type = factory.Iterator(StartupDocument.DocumentType.values)


class StartupFundingRoundFactory(DjangoModelFactory):
    class Meta:
        model = StartupFundingRound

    startup = factory.SubFactory(StartupFactory)
    round_name = factory.Iterator(['Pre-Seed', 'Seed', 'Series A', 'Series B', 'Series C', 'Bridge'])
    amount = Decimal('1000000.00')
    date = factory.LazyFunction(lambda: timezone.now().date() - datetime.timedelta(days=30))
    investors = factory.Faker('company')
    valuation = Decimal('5000000.00')
    notes = factory.Faker('paragraph')


class StartupMetricFactory(DjangoModelFactory):
    class Meta:
        model = StartupMetric

    startup = factory.SubFactory(StartupFactory)
    monthly_revenue = Decimal('50000.00')
    annual_revenue = Decimal('600000.00')
    revenue_growth_pct = Decimal('15.50')
    monthly_active_users = factory.Faker('random_int', min=100, max=100000)
    total_users = factory.Faker('random_int', min=1000, max=1000000)
    gross_margin_pct = Decimal('65.00')
    burn_rate = Decimal('30000.00')
    runway_months = factory.Faker('random_int', min=3, max=36)
    traction_description = factory.Faker('paragraph')
    key_achievements = ['Launched MVP', 'First 1000 users', 'Closed seed round']


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

class InvestorPreferenceFactory(DjangoModelFactory):
    class Meta:
        model = InvestorPreference

    user = factory.SubFactory('apps.common.tests.factories.UserFactory')
    preferred_industries = ['ai_ml', 'fintech', 'saas']
    preferred_stages = ['seed', 'series_a']
    min_ticket_size = Decimal('50000.00')
    max_ticket_size = Decimal('5000000.00')
    preferred_geographies = ['North America']
    risk_appetite = InvestorPreference.RiskAppetite.MODERATE
    investment_focus = factory.Faker('paragraph')
    is_active = True


class MatchScoreFactory(DjangoModelFactory):
    class Meta:
        model = MatchScore

    investor = factory.SubFactory(UserFactory)
    startup = factory.SubFactory(StartupFactory)
    score = factory.fuzzy.FuzzyDecimal(0, 100)
    score_breakdown = {'industry_match': 85, 'stage_match': 70, 'location_match': 60}
    status = MatchScore.Status.RECOMMENDED


class SavedMatchFactory(DjangoModelFactory):
    class Meta:
        model = SavedMatch

    user = factory.SubFactory(UserFactory)
    match = factory.SubFactory(MatchScoreFactory)


class DismissedMatchFactory(DjangoModelFactory):
    class Meta:
        model = DismissedMatch

    user = factory.SubFactory(UserFactory)
    match = factory.SubFactory(MatchScoreFactory)


class InteractionEventFactory(DjangoModelFactory):
    class Meta:
        model = InteractionEvent

    user = factory.SubFactory(UserFactory)
    startup = factory.SubFactory(StartupFactory)
    event_type = factory.Iterator(InteractionEvent.EventType.values)
    metadata = {'source': 'test'}
    session_id = factory.Sequence(lambda n: f'session-{n}')


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ConversationFactory(DjangoModelFactory):
    class Meta:
        model = Conversation

    created_by = factory.SubFactory(UserFactory)
    is_active = True


class ConversationParticipantFactory(DjangoModelFactory):
    class Meta:
        model = ConversationParticipant

    conversation = factory.SubFactory(ConversationFactory)
    user = factory.SubFactory(UserFactory)


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message

    conversation = factory.SubFactory(ConversationFactory)
    sender = factory.SubFactory(UserFactory)
    message_type = Message.MessageType.TEXT
    content = factory.Faker('sentence')
    metadata = {}


class MessageReadStatusFactory(DjangoModelFactory):
    class Meta:
        model = MessageReadStatus

    message = factory.SubFactory(MessageFactory)
    user = factory.SubFactory(UserFactory)


# ---------------------------------------------------------------------------
# Meetings
# ---------------------------------------------------------------------------

class MeetingFactory(DjangoModelFactory):
    class Meta:
        model = Meeting

    organizer = factory.SubFactory(UserFactory)
    startup = factory.SubFactory(StartupFactory)
    investor = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Meeting {n}")
    description = factory.Faker('paragraph')
    meeting_type = factory.Iterator(Meeting.MeetingType.values)
    status = Meeting.Status.SCHEDULED
    scheduled_start = factory.LazyFunction(lambda: timezone.now() + datetime.timedelta(days=7))
    scheduled_end = factory.LazyAttribute(
        lambda o: o.scheduled_start + datetime.timedelta(hours=1),
    )
    timezone = 'UTC'
    meeting_link = factory.Faker('url')
    location = factory.Faker('city')
    notes = factory.Faker('paragraph')


class MeetingParticipantFactory(DjangoModelFactory):
    class Meta:
        model = MeetingParticipant

    meeting = factory.SubFactory(MeetingFactory)
    user = factory.SubFactory(UserFactory)
    attendance_status = MeetingParticipant.Attendance.PENDING


class MeetingAvailabilityFactory(DjangoModelFactory):
    class Meta:
        model = MeetingAvailability

    user = factory.SubFactory(UserFactory)
    day_of_week = factory.Iterator(range(7))
    start_time = datetime.time(9, 0)
    end_time = datetime.time(17, 0)
    timezone = 'UTC'


class MeetingEventFactory(DjangoModelFactory):
    class Meta:
        model = MeetingEvent

    meeting = factory.SubFactory(MeetingFactory)
    actor = factory.SubFactory(UserFactory)
    action = factory.Iterator(MeetingEvent.Action.values)
    metadata = {}


# ---------------------------------------------------------------------------
# Investments
# ---------------------------------------------------------------------------

class InvestmentOpportunityFactory(DjangoModelFactory):
    class Meta:
        model = InvestmentOpportunity

    startup = factory.SubFactory(StartupFactory)
    investor = factory.SubFactory(UserFactory)
    amount_requested = Decimal('1000000.00')
    amount_offered = Decimal('750000.00')
    equity_requested = Decimal('10.00')
    equity_offered = Decimal('8.00')
    valuation = Decimal('5000000.00')
    proposed_valuation = Decimal('5500000.00')
    status = InvestmentOpportunity.Status.INTERESTED
    notes = factory.Faker('paragraph')


class InvestmentActivityFactory(DjangoModelFactory):
    class Meta:
        model = InvestmentActivity

    opportunity = factory.SubFactory(InvestmentOpportunityFactory)
    actor = factory.SubFactory(UserFactory)
    action = factory.Iterator([
        'created', 'status_changed', 'note_added', 'term_sheet_sent', 'invested',
    ])
    metadata = {}


# ---------------------------------------------------------------------------
# Data Room
# ---------------------------------------------------------------------------

class DataRoomFactory(DjangoModelFactory):
    class Meta:
        model = DataRoom

    startup = factory.SubFactory(StartupFactory)
    title = factory.Sequence(lambda n: f"Data Room {n}")
    description = factory.Faker('paragraph')
    visibility = factory.Iterator(DataRoom.Visibility.values)
    created_by = factory.SubFactory(UserFactory)


class DataRoomDocumentFactory(DjangoModelFactory):
    class Meta:
        model = DataRoomDocument

    data_room = factory.SubFactory(DataRoomFactory)
    file = factory.django.FileField(filename='test_document.pdf')
    title = factory.Sequence(lambda n: f"Document {n}")
    document_type = factory.Iterator(DataRoomDocument.DocumentType.values)
    uploaded_by = factory.SubFactory(UserFactory)
    file_size = 1024
    mime_type = 'application/pdf'


class DocumentAccessFactory(DjangoModelFactory):
    class Meta:
        model = DocumentAccess

    document = factory.SubFactory(DataRoomDocumentFactory)
    investor = factory.SubFactory(UserFactory)
    granted_by = factory.SubFactory(UserFactory)


class DocumentViewEventFactory(DjangoModelFactory):
    class Meta:
        model = DocumentViewEvent

    document = factory.SubFactory(DataRoomDocumentFactory)
    investor = factory.SubFactory(UserFactory)
    duration_seconds = factory.Faker('random_int', min=5, max=600)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    actor = factory.SubFactory(UserFactory)
    notification_type = factory.Iterator(Notification.Type.values)
    title = factory.Faker('sentence')
    message = factory.Faker('paragraph')
    data = {}
    is_read = False


class NotificationPreferenceFactory(DjangoModelFactory):
    class Meta:
        model = NotificationPreference

    user = factory.SubFactory(UserFactory)
    email_enabled = True
    push_enabled = True
    in_app_enabled = True
    matching_notifications = True
    investment_notifications = True
    chat_notifications = True
    document_notifications = True
    marketing_notifications = False


# ---------------------------------------------------------------------------
# Activity Feed
# ---------------------------------------------------------------------------

class ActivityFeedFactory(DjangoModelFactory):
    class Meta:
        model = ActivityFeed

    actor = factory.SubFactory(UserFactory)
    activity_type = factory.Iterator(ActivityFeed.ActivityType.values)
    startup = factory.SubFactory(StartupFactory)
    title = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    metadata = {}
    visibility = ActivityFeed.Visibility.PUBLIC


class FeedReactionFactory(DjangoModelFactory):
    class Meta:
        model = FeedReaction

    user = factory.SubFactory(UserFactory)
    feed_item = factory.SubFactory(ActivityFeedFactory)
    reaction_type = factory.Iterator(['like', 'celebrate', 'support', 'insightful', 'curious'])


class FeedBookmarkFactory(DjangoModelFactory):
    class Meta:
        model = FeedBookmark

    user = factory.SubFactory(UserFactory)
    feed_item = factory.SubFactory(ActivityFeedFactory)


class FeedCommentFactory(DjangoModelFactory):
    class Meta:
        model = FeedComment

    user = factory.SubFactory(UserFactory)
    feed_item = factory.SubFactory(ActivityFeedFactory)
    content = factory.Faker('paragraph')
    parent_comment = None


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------

class SubscriptionPlanFactory(DjangoModelFactory):
    class Meta:
        model = SubscriptionPlan
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: [
        'Free', 'Founder Premium', 'Investor Premium', 'Enterprise',
    ][n % 4])
    slug = factory.Sequence(lambda n: [
        'free', 'founder_premium', 'investor_premium', 'enterprise',
    ][n % 4])
    tier = factory.Sequence(lambda n: [
        SubscriptionPlan.Tier.FREE,
        SubscriptionPlan.Tier.FOUNDER_PREMIUM,
        SubscriptionPlan.Tier.INVESTOR_PREMIUM,
        SubscriptionPlan.Tier.ENTERPRISE,
    ][n % 4])
    description = factory.Faker('paragraph')
    monthly_price = factory.Sequence(lambda n: [
        Decimal('0.00'), Decimal('29.99'), Decimal('49.99'), Decimal('99.99'),
    ][n % 4])
    yearly_price = factory.Sequence(lambda n: [
        Decimal('0.00'), Decimal('299.99'), Decimal('499.99'), Decimal('999.99'),
    ][n % 4])
    features = {'analytics': True, 'support': 'basic'}
    limits = {'startups': 1, 'matches': 10}
    sort_order = factory.Sequence(lambda n: n % 4)
    is_active = True
    is_popular = factory.Sequence(lambda n: [False, True, True, False][n % 4])


class CouponFactory(DjangoModelFactory):
    class Meta:
        model = Coupon

    code = factory.Sequence(lambda n: f'COUPON{n}')
    discount_type = factory.Iterator(Coupon.DiscountType.values)
    discount_value = Decimal('20.00')
    description = factory.Faker('sentence')
    is_active = True


class UserSubscriptionFactory(DjangoModelFactory):
    class Meta:
        model = UserSubscription

    user = factory.SubFactory(UserFactory)
    plan = factory.SubFactory(SubscriptionPlanFactory)
    status = UserSubscription.Status.ACTIVE
    billing_cycle = UserSubscription.BillingCycle.MONTHLY
    start_date = factory.LazyFunction(lambda: timezone.now())
    end_date = factory.LazyFunction(lambda: timezone.now() + datetime.timedelta(days=30))
    auto_renew = True
    coupon = None
    metadata = {}


class InvoiceFactory(DjangoModelFactory):
    class Meta:
        model = Invoice

    user = factory.SubFactory(UserFactory)
    subscription = factory.SubFactory(UserSubscriptionFactory)
    plan = factory.SubFactory(SubscriptionPlanFactory)
    amount = Decimal('29.99')
    currency = 'USD'
    status = Invoice.Status.PENDING
    invoice_number = factory.Sequence(lambda n: f'INV-{n:06d}')
    payment_provider = 'stripe'
    billing_cycle = UserSubscription.BillingCycle.MONTHLY


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

class AuditLogFactory(DjangoModelFactory):
    class Meta:
        model = AuditLog

    actor = factory.SubFactory(UserFactory)
    action_type = factory.Iterator(AuditLog.ActionType.values)
    target_type = 'User'
    target_id = factory.Sequence(lambda n: n)
    target_repr = factory.Faker('email')
    description = factory.Faker('paragraph')
    metadata = {}


class SupportTicketFactory(DjangoModelFactory):
    class Meta:
        model = SupportTicket

    user = factory.SubFactory(UserFactory)
    subject = factory.Faker('sentence')
    description = factory.Faker('paragraph')
    category = factory.Iterator(SupportTicket.Category.values)
    priority = SupportTicket.Priority.MEDIUM
    status = SupportTicket.Status.OPEN
    assigned_to = None
    metadata = {}


class SupportMessageFactory(DjangoModelFactory):
    class Meta:
        model = SupportMessage

    ticket = factory.SubFactory(SupportTicketFactory)
    sender = factory.SubFactory(UserFactory)
    content = factory.Faker('paragraph')
    is_internal = False
    attachments = []


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------

class SystemErrorFactory(DjangoModelFactory):
    class Meta:
        model = SystemError

    source = factory.Iterator(SystemError.Source.values)
    severity = factory.Iterator(SystemError.Severity.values)
    error_type = factory.Iterator(['ValueError', 'KeyError', 'Http404', 'PermissionDenied', 'IntegrityError'])
    message = factory.Faker('sentence')
    traceback = factory.Faker('paragraph')
    endpoint = '/api/test/'
    user = None
    request_id = factory.Sequence(lambda n: f'req-{n}')
    correlation_id = factory.Sequence(lambda n: f'corr-{n}')
    metadata = {}


class RequestMetricFactory(DjangoModelFactory):
    class Meta:
        model = RequestMetric

    method = factory.Iterator(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
    endpoint = factory.Iterator(['/api/startups/', '/api/matches/', '/api/investors/', '/api/meetings/'])
    status_code = factory.Iterator([200, 201, 400, 404, 500])
    duration_ms = factory.Faker('random_int', min=10, max=5000)
    user = None
    request_id = factory.Sequence(lambda n: f'req-metric-{n}')
    is_error = False


class AlertRuleFactory(DjangoModelFactory):
    class Meta:
        model = AlertRule

    name = factory.Sequence(lambda n: f"Alert Rule {n}")
    metric = factory.Iterator(AlertRule.Metric.values)
    operator = factory.Iterator(AlertRule.Operator.values)
    threshold = 90.0
    window_minutes = 5
    cooldown_minutes = 30
    is_active = True
    notify_slack = False
    notify_email = False


class AlertEventFactory(DjangoModelFactory):
    class Meta:
        model = AlertEvent

    rule = factory.SubFactory(AlertRuleFactory)
    status = AlertEvent.Status.TRIGGERED
    metric_value = 95.0
    message = factory.Faker('sentence')
    acknowledged_by = None


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class PlatformSettingFactory(DjangoModelFactory):
    class Meta:
        model = PlatformSetting

    key = factory.Sequence(lambda n: f'setting_key_{n}')
    label = factory.Sequence(lambda n: f"Setting {n}")
    description = factory.Faker('sentence')
    value_type = PlatformSetting.ValueType.STRING
    string_value = factory.Faker('word')
    group = factory.Iterator(['general', 'email', 'api', 'security', 'limits'])
    is_public = True
    is_encrypted = False


class FeatureFlagFactory(DjangoModelFactory):
    class Meta:
        model = FeatureFlag

    key = factory.Sequence(lambda n: f'feature_flag_{n}')
    label = factory.Sequence(lambda n: f"Feature Flag {n}")
    description = factory.Faker('sentence')
    enabled = False
    enabled_for_roles = []
    user_percentage = 100


class MaintenanceModeFactory(DjangoModelFactory):
    class Meta:
        model = MaintenanceMode

    is_active = False
    title = 'Under Maintenance'
    message = 'We are performing scheduled maintenance. Please check back shortly.'
    allowed_ips = []
    allowed_user_ids = []


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

class OnboardingWizardFactory(DjangoModelFactory):
    class Meta:
        model = OnboardingWizard

    user = factory.SubFactory(UserFactory)
    wizard_type = factory.Iterator(OnboardingWizard.WizardType.values)
    current_step = ''
    is_complete = False
    metadata = {}


class OnboardingStepFactory(DjangoModelFactory):
    class Meta:
        model = OnboardingStep

    wizard = factory.SubFactory(OnboardingWizardFactory)
    step_key = factory.Sequence(lambda n: f'step_{n}')
    step_label = factory.Sequence(lambda n: f"Step {n}")
    is_completed = False
    data = {}


class FounderOnboardingDataFactory(DjangoModelFactory):
    class Meta:
        model = FounderOnboardingData

    user = factory.SubFactory(UserFactory)
    company_name = factory.Sequence(lambda n: f"Startup Co. {n}")
    tagline = factory.Faker('catch_phrase')
    industry = factory.Iterator(['ai_ml', 'fintech', 'healthtech', 'saas'])
    funding_stage = factory.Iterator(['pre_seed', 'seed', 'series_a'])
    website = factory.Faker('url')
    linkedin = factory.Faker('url')
    team_size = factory.Faker('random_int', min=1, max=50)
    business_model = factory.Iterator(['b2b', 'b2c', 'saas', 'marketplace'])
    target_market = factory.Faker('paragraph')
    revenue_model = factory.Faker('paragraph')
    traction = factory.Faker('paragraph')
    competitors = factory.Faker('paragraph')


class InvestorOnboardingDataFactory(DjangoModelFactory):
    class Meta:
        model = InvestorOnboardingData

    user = factory.SubFactory(UserFactory)
    investor_type = factory.Iterator(['angel', 'vc', 'corporate', 'accelerator'])
    bio = factory.Faker('paragraph')
    investment_focus = factory.Faker('paragraph')
    preferred_industries = ['ai_ml', 'fintech', 'saas']
    preferred_stages = ['seed', 'series_a']
    ticket_size_min = Decimal('50000.00')
    ticket_size_max = Decimal('5000000.00')
    preferred_geographies = ['North America']
    linkedin_url = factory.Faker('url')
    website_url = factory.Faker('url')
    years_experience = factory.Faker('random_int', min=1, max=25)
    portfolio_companies = ['Previous Co', 'Another Co']


# ---------------------------------------------------------------------------
# Match Intelligence
# ---------------------------------------------------------------------------

class MatchInsightFactory(DjangoModelFactory):
    class Meta:
        model = MatchInsight

    match = factory.SubFactory(MatchScoreFactory)
    summary = factory.Faker('paragraph')
    strengths = ['Strong industry alignment', 'Proven traction', 'Experienced team']
    risks = ['Competitive market', 'Early stage']
    recommendations = ['Schedule intro call', 'Share pitch deck']
    generated_at = factory.LazyFunction(timezone.now)


class MatchFeedbackFactory(DjangoModelFactory):
    class Meta:
        model = MatchFeedback

    user = factory.SubFactory(UserFactory)
    match = factory.SubFactory(MatchScoreFactory)
    rating = factory.Faker('random_int', min=1, max=5)
    feedback = factory.Faker('paragraph')


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

class SavedSearchFactory(DjangoModelFactory):
    class Meta:
        model = SavedSearch

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Saved Search {n}")
    search_type = factory.Iterator(SavedSearch.SearchType.values)
    filters = {'industry': 'ai_ml', 'stage': 'seed'}


class SearchHistoryFactory(DjangoModelFactory):
    class Meta:
        model = SearchHistory

    user = factory.SubFactory(UserFactory)
    query = factory.Faker('word')
    search_type = factory.Iterator(['startups', 'investors', 'founders'])
    filters = {}
    results_count = factory.Faker('random_int', min=0, max=100)


class SearchClickEventFactory(DjangoModelFactory):
    class Meta:
        model = SearchClickEvent

    user = factory.SubFactory(UserFactory)
    result_type = factory.Iterator(['startup', 'investor', 'founder'])
    result_id = factory.Sequence(lambda n: n)
    query = factory.Faker('word')
