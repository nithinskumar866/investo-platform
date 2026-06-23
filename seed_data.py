"""
Seed data script for Investo platform.
Creates demo users, startups, investor profiles, meetings, chats, and more.

Usage: python seed_data.py
"""

import os
import sys
from datetime import datetime, timedelta

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

# ─── Imports ──────────────────────────────────────────────────────────────────
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError

# ─── Section: Users ────────────────────────────────────────────────────────────
print("\n=== Creating Users ===")

from apps.accounts.models import User, EntrepreneurProfile, InvestorProfile

users_data = [
    {
        "email": "admin@investo.com",
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "User",
        "role": User.Role.ADMIN,
        "is_verified": True,
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "founder@investo.com",
        "password": "founder123",
        "first_name": "Sarah",
        "last_name": "Chen",
        "role": User.Role.ENTREPRENEUR,
        "is_verified": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "investor@investo.com",
        "password": "investor123",
        "first_name": "Marcus",
        "last_name": "Williams",
        "role": User.Role.INVESTOR,
        "is_verified": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "priya@investo.com",
        "password": "founder123",
        "first_name": "Priya",
        "last_name": "Patel",
        "role": User.Role.ENTREPRENEUR,
        "is_verified": True,
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "email": "elena@investo.com",
        "password": "investor123",
        "first_name": "Elena",
        "last_name": "Rodriguez",
        "role": User.Role.INVESTOR,
        "is_verified": True,
        "is_staff": False,
        "is_superuser": False,
    },
]

users = {}
for data in users_data:
    password = data.pop("password")
    user, created = User.objects.update_or_create(
        email=data["email"],
        defaults={**data, "username": data["email"].split("@")[0]},
    )
    user.set_password(password)
    user.save()
    users[data["email"]] = user
    print(f"  {'Created' if created else 'Updated'}: {user.email}")

# ─── Section: Investor Preferences ────────────────────────────────────────────
print("\n=== Creating Investor Preferences ===")

from apps.matching.models import InvestorPreference

investor_prefs_data = [
    {
        "user": users["investor@investo.com"],
        "preferred_industries": ["saas", "fintech", "ai_ml"],
        "preferred_stages": ["seed", "series_a"],
        "min_ticket_size": 50000,
        "max_ticket_size": 500000,
        "preferred_geographies": ["San Francisco", "United States"],
        "risk_appetite": InvestorPreference.RiskAppetite.MODERATE,
        "investment_focus": "B2B SaaS and fintech platforms",
    },
    {
        "user": users["elena@investo.com"],
        "preferred_industries": ["healthtech", "cleantech", "biotech"],
        "preferred_stages": ["pre_seed", "seed"],
        "min_ticket_size": 25000,
        "max_ticket_size": 250000,
        "preferred_geographies": ["New York", "United States"],
        "risk_appetite": InvestorPreference.RiskAppetite.AGGRESSIVE,
        "investment_focus": "Deep tech and sustainability",
    },
]

for pref_data in investor_prefs_data:
    obj, created = InvestorPreference.objects.update_or_create(
        user=pref_data["user"],
        defaults=pref_data,
    )
    print(f"  {'Created' if created else 'Updated'} preferences for {pref_data['user'].email}")

# ─── Section: Startups ────────────────────────────────────────────────────────
print("\n=== Creating Startups ===")

from apps.startups.models import Startup

founder = users["founder@investo.com"]
priya = users["priya@investo.com"]

startups_data = [
    {
        "owner": founder,
        "name": "Nova AI",
        "tagline": "AI-powered fintech intelligence platform",
        "short_description": "Nova AI provides real-time financial intelligence using cutting-edge machine learning.",
        "industry": Startup.Industry.AI_ML,
        "stage": Startup.Stage.SEED,
        "funding_goal": 500000,
        "equity_offered": 10.00,
        "valuation": 5000000,
        "location": "San Francisco, CA",
        "status": Startup.Status.ACTIVE,
        "is_visible": True,
        "is_verified": True,
    },
    {
        "owner": priya,
        "name": "GreenGrow",
        "tagline": "Sustainable agriculture for the future",
        "short_description": "GreenGrow uses IoT and data analytics to optimize crop yields sustainably.",
        "industry": Startup.Industry.CLEANTECH,
        "stage": Startup.Stage.SERIES_A,
        "funding_goal": 2000000,
        "equity_offered": 15.00,
        "valuation": 12000000,
        "location": "Austin, TX",
        "status": Startup.Status.ACTIVE,
        "is_visible": True,
        "is_verified": True,
    },
    {
        "owner": founder,
        "name": "HealthSync",
        "tagline": "Digital health platform connecting patients and providers",
        "short_description": "HealthSync streamlines healthcare coordination with a modern digital platform.",
        "industry": Startup.Industry.HEALTHTECH,
        "stage": Startup.Stage.PRE_SEED,
        "funding_goal": 250000,
        "equity_offered": 12.00,
        "valuation": 2000000,
        "location": "Boston, MA",
        "status": Startup.Status.ACTIVE,
        "is_visible": True,
        "is_verified": False,
    },
    {
        "owner": priya,
        "name": "BlockGrid",
        "tagline": "Enterprise blockchain infrastructure",
        "short_description": "BlockGrid provides scalable blockchain solutions for enterprise supply chains.",
        "industry": Startup.Industry.BLOCKCHAIN,
        "stage": Startup.Stage.SEED,
        "funding_goal": 750000,
        "equity_offered": 10.00,
        "valuation": 7500000,
        "location": "New York, NY",
        "status": Startup.Status.ACTIVE,
        "is_visible": True,
        "is_verified": True,
    },
    {
        "owner": founder,
        "name": "EduSpark",
        "tagline": "AI-powered personalized learning for everyone",
        "short_description": "EduSpark uses AI to create personalized learning paths for students worldwide.",
        "industry": Startup.Industry.EDTECH,
        "stage": Startup.Stage.PRE_SEED,
        "funding_goal": 150000,
        "equity_offered": 15.00,
        "valuation": 1000000,
        "location": "Remote",
        "status": Startup.Status.DRAFT,
        "is_visible": True,
        "is_verified": False,
    },
]

startups = {}
for sdata in startups_data:
    name = sdata["name"]
    obj, created = Startup.objects.update_or_create(
        name=name,
        defaults=sdata,
    )
    startups[name] = obj
    print(f"  {'Created' if created else 'Updated'}: {name}")

# ─── Section: Investor Profiles ───────────────────────────────────────────────
print("\n=== Creating Investor Profiles ===")

investor = users["investor@investo.com"]
elena = users["elena@investo.com"]

investor_profiles_data = [
    {
        "user": investor,
        "investor_type": "vc",
        "bio": "Experienced VC focused on early-stage SaaS and fintech companies.",
        "tagline": "Investing in the future of fintech",
        "investment_focus": "SaaS, FinTech, AI/ML",
        "preferred_industries": ["saas", "fintech", "ai_ml"],
        "preferred_stages": ["seed", "series_a"],
        "ticket_size_min": 50000,
        "ticket_size_max": 500000,
        "preferred_geographies": ["San Francisco", "United States"],
        "city": "San Francisco",
        "country": "United States",
        "years_of_experience": 12,
        "investments_completed": 25,
        "lead_investor": True,
    },
    {
        "user": elena,
        "investor_type": "angel",
        "bio": "Angel investor passionate about health tech, climate tech, and deep tech.",
        "tagline": "Backing bold ideas that change the world",
        "investment_focus": "HealthTech, ClimateTech, DeepTech",
        "preferred_industries": ["healthtech", "cleantech", "biotech"],
        "preferred_stages": ["pre_seed", "seed"],
        "ticket_size_min": 25000,
        "ticket_size_max": 250000,
        "preferred_geographies": ["New York", "United States"],
        "city": "New York",
        "country": "United States",
        "years_of_experience": 8,
        "investments_completed": 15,
        "lead_investor": False,
    },
]

for ip_data in investor_profiles_data:
    obj, created = InvestorProfile.objects.update_or_create(
        user=ip_data["user"],
        defaults=ip_data,
    )
    print(f"  {'Created' if created else 'Updated'} profile for {ip_data['user'].email}")

# ─── Section: Entrepreneur Profiles ───────────────────────────────────────────
print("\n=== Creating Entrepreneur Profiles ===")

for user, company in [(founder, "Nova AI"), (priya, "GreenGrow")]:
    obj, created = EntrepreneurProfile.objects.update_or_create(
        user=user,
        defaults={
            "company_name": company,
            "industry": "Technology",
            "funding_stage": "seed",
            "city": "San Francisco" if user == founder else "Austin",
            "country": "United States",
            "is_public": True,
        },
    )
    print(f"  {'Created' if created else 'Updated'} entrepreneur profile for {user.email}")

# ─── Section: Match Scores ─────────────────────────────────────────────────────
print("\n=== Creating Match Scores ===")

from apps.matching.models import MatchScore

match_scores_data = [
    {"investor": investor, "startup": startups["Nova AI"], "score": 92.50, "status": MatchScore.Status.RECOMMENDED},
    {"investor": investor, "startup": startups["HealthSync"], "score": 78.00, "status": MatchScore.Status.RECOMMENDED},
    {"investor": investor, "startup": startups["EduSpark"], "score": 65.50, "status": MatchScore.Status.PENDING},
    {"investor": elena, "startup": startups["GreenGrow"], "score": 88.00, "status": MatchScore.Status.RECOMMENDED},
    {"investor": elena, "startup": startups["HealthSync"], "score": 82.00, "status": MatchScore.Status.RECOMMENDED},
    {"investor": elena, "startup": startups["BlockGrid"], "score": 71.50, "status": MatchScore.Status.PENDING},
    {"investor": elena, "startup": startups["Nova AI"], "score": 74.00, "status": MatchScore.Status.CONTACTED},
    {"investor": investor, "startup": startups["GreenGrow"], "score": 85.00, "status": MatchScore.Status.SAVED},
]

match_scores = []
for ms_data in match_scores_data:
    obj, created = MatchScore.objects.update_or_create(
        investor=ms_data["investor"],
        startup=ms_data["startup"],
        defaults={
            "score": ms_data["score"],
            "status": ms_data["status"],
            "score_breakdown": {
                "industry_match": 90,
                "stage_match": 85,
                "location_match": 80,
                "ticket_size_match": 95,
            },
        },
    )
    match_scores.append(obj)
    print(f"  {'Created' if created else 'Updated'} match: {obj}")

# ─── Section: Match Insights ──────────────────────────────────────────────────
print("\n=== Creating Match Insights ===")

from apps.match_intelligence.models import MatchInsight

insights_data = [
    {
        "match": match_scores[0],
        "summary": "Strong alignment between Nova AI's fintech AI platform and Marcus's investment focus on AI/ML and fintech. Excellent stage and ticket size match.",
        "strengths": ["Industry alignment", "Stage fit", "Ticket size compatibility", "Geographic proximity"],
        "risks": ["Competitive market", "Early traction needed"],
        "recommendations": ["Schedule intro call", "Share pitch deck", "Arrange product demo"],
    },
    {
        "match": match_scores[3],
        "summary": "GreenGrow's sustainable agriculture mission aligns perfectly with Elena's climate tech focus. Strong synergy in impact investing.",
        "strengths": ["Mission alignment", "Scalable technology", "Experienced team"],
        "risks": ["Capital intensive", "Regulatory landscape"],
        "recommendations": ["Review business plan", "Discuss go-to-market strategy", "Connect with portfolio companies"],
    },
    {
        "match": match_scores[4],
        "summary": "HealthSync's digital health platform matches Elena's healthtech interest. Pre-seed stage fits her preferred investment range.",
        "strengths": ["Growing market", "Strong founding team", "Clear value proposition"],
        "risks": ["Early stage", "Competition from established players"],
        "recommendations": ["Evaluate product roadmap", "Assess technical capabilities", "Discuss clinical validation"],
    },
]

for insight_data in insights_data:
    obj, created = MatchInsight.objects.update_or_create(
        match=insight_data["match"],
        defaults={
            "summary": insight_data["summary"],
            "strengths": insight_data["strengths"],
            "risks": insight_data["risks"],
            "recommendations": insight_data["recommendations"],
        },
    )
    print(f"  {'Created' if created else 'Updated'} insight for match {insight_data['match'].id}")

# ─── Section: Meetings ────────────────────────────────────────────────────────
print("\n=== Creating Meetings ===")

from apps.meetings.models import Meeting, MeetingParticipant

now = timezone.now()
meetings_data = [
    {
        "organizer": founder,
        "startup": startups["Nova AI"],
        "investor": investor,
        "title": "Intro Call: Nova AI",
        "description": "Initial introduction call to discuss Nova AI's platform and investment opportunity.",
        "meeting_type": Meeting.MeetingType.INTRO_CALL,
        "status": Meeting.Status.COMPLETED,
        "scheduled_start": now - timedelta(days=14),
        "scheduled_end": now - timedelta(days=14, hours=-1),
        "meeting_link": "https://meet.google.com/abc-defg-hij",
        "notes": "Great introductory conversation. Marcus is interested in learning more.",
    },
    {
        "organizer": founder,
        "startup": startups["Nova AI"],
        "investor": investor,
        "title": "Pitch Meeting: Nova AI",
        "description": "Full pitch presentation with demo of the fintech AI platform.",
        "meeting_type": Meeting.MeetingType.PITCH_MEETING,
        "status": Meeting.Status.COMPLETED,
        "scheduled_start": now - timedelta(days=7),
        "scheduled_end": now - timedelta(days=7, hours=-2),
        "meeting_link": "https://meet.google.com/xyz-uvwx-yza",
        "notes": "Impressive demo. Discussed market size and competitive landscape.",
    },
    {
        "organizer": investor,
        "startup": startups["Nova AI"],
        "investor": investor,
        "title": "Due Diligence: Nova AI",
        "description": "Deep dive into financials, technology architecture, and team background.",
        "meeting_type": Meeting.MeetingType.DUE_DILIGENCE,
        "status": Meeting.Status.CONFIRMED,
        "scheduled_start": now + timedelta(days=3),
        "scheduled_end": now + timedelta(days=3, hours=-2),
        "meeting_link": "https://meet.google.com/mno-pqrs-tuv",
        "notes": "Prepare financial projections and technical documentation.",
    },
    {
        "organizer": founder,
        "startup": startups["Nova AI"],
        "investor": investor,
        "title": "Follow-up: Term Sheet Discussion",
        "description": "Discuss potential terms and next steps for investment.",
        "meeting_type": Meeting.MeetingType.FOLLOW_UP,
        "status": Meeting.Status.SCHEDULED,
        "scheduled_start": now + timedelta(days=10),
        "scheduled_end": now + timedelta(days=10, hours=-1),
        "meeting_link": "https://meet.google.com/def-ghij-klm",
    },
    {
        "organizer": founder,
        "startup": startups["HealthSync"],
        "investor": investor,
        "title": "Intro Call: HealthSync",
        "description": "Initial discussion about HealthSync's digital health platform.",
        "meeting_type": Meeting.MeetingType.INTRO_CALL,
        "status": Meeting.Status.CONFIRMED,
        "scheduled_start": now + timedelta(days=5),
        "scheduled_end": now + timedelta(days=5, hours=-1),
        "meeting_link": "https://meet.google.com/ghi-jklm-nop",
    },
]

for m_data in meetings_data:
    obj = Meeting.objects.create(**m_data)
    # Add participants
    MeetingParticipant.objects.get_or_create(
        meeting=obj,
        user=m_data["organizer"],
        defaults={"attendance_status": MeetingParticipant.Attendance.ACCEPTED},
    )
    MeetingParticipant.objects.get_or_create(
        meeting=obj,
        user=m_data["investor"],
        defaults={"attendance_status": MeetingParticipant.Attendance.ACCEPTED},
    )
    print(f"  Created meeting: {obj.title}")

# ─── Section: Chat Conversations ──────────────────────────────────────────────
print("\n=== Creating Chat Conversations ===")

from apps.chat.models import Conversation, ConversationParticipant, Message, MessageReadStatus

# Conversation 1: General discussion about Nova AI
conv1 = Conversation.objects.create(created_by=founder)
ConversationParticipant.objects.create(conversation=conv1, user=founder)
ConversationParticipant.objects.create(conversation=conv1, user=investor)

conv1_messages = [
    {"sender": founder, "content": "Hi Marcus! Thanks for taking the time to connect."},
    {"sender": investor, "content": "Hi Sarah! I've been impressed with what I've seen of Nova AI so far."},
    {"sender": founder, "content": "That's great to hear! I'd love to share more about our platform."},
    {"sender": investor, "content": "Please do. Your fintech AI approach is exactly what I've been looking for."},
    {"sender": founder, "content": "We've built a real-time financial intelligence platform that uses ML to predict market trends."},
    {"sender": investor, "content": "Interesting. What's your current traction looking like?"},
    {"sender": founder, "content": "We have 3 enterprise clients in beta and $50K MRR growing at 20% month-over-month."},
    {"sender": investor, "content": "Those are solid numbers. I'd love to see a demo when you're ready."},
    {"sender": founder, "content": "Absolutely! I'll send over a deck and we can schedule a demo."},
    {"sender": investor, "content": "Perfect, looking forward to it."},
]

for i, msg_data in enumerate(conv1_messages):
    msg = Message.objects.create(
        conversation=conv1,
        sender=msg_data["sender"],
        content=msg_data["content"],
        created_at=now - timedelta(days=14) + timedelta(hours=i),
    )
    MessageReadStatus.objects.create(message=msg, user=msg_data["sender"])
    if msg_data["sender"] != founder:
        MessageReadStatus.objects.create(message=msg, user=founder)

print(f"  Created conversation 1 with {len(conv1_messages)} messages")

# Conversation 2: Investment details
conv2 = Conversation.objects.create(created_by=investor)
ConversationParticipant.objects.create(conversation=conv2, user=founder)
ConversationParticipant.objects.create(conversation=conv2, user=investor)

conv2_messages = [
    {"sender": investor, "content": "I've reviewed your pitch deck and I'm very interested in moving forward."},
    {"sender": founder, "content": "That's wonderful! What questions do you have?"},
    {"sender": investor, "content": "I'd like to understand more about your tech stack and data pipeline."},
    {"sender": founder, "content": "We use Python with TensorFlow for ML models, and our data pipeline is built on Apache Kafka."},
    {"sender": investor, "content": "Great tech choices. What about your team composition?"},
    {"sender": founder, "content": "We're 8 people: 3 engineers, 2 data scientists, 1 product manager, 1 BD, and myself as CEO."},
    {"sender": investor, "content": "Lean team, impressive output. I'm thinking about a $200K investment."},
    {"sender": founder, "content": "That would be fantastic. Let's discuss terms in our next meeting."},
]

for i, msg_data in enumerate(conv2_messages):
    msg = Message.objects.create(
        conversation=conv2,
        sender=msg_data["sender"],
        content=msg_data["content"],
        created_at=now - timedelta(days=3) + timedelta(hours=i),
    )
    MessageReadStatus.objects.create(message=msg, user=msg_data["sender"])
    if msg_data["sender"] != founder:
        MessageReadStatus.objects.create(message=msg, user=founder)

print(f"  Created conversation 2 with {len(conv2_messages)} messages")

# ─── Section: Notifications ───────────────────────────────────────────────────
print("\n=== Creating Notifications ===")

from apps.notifications.models import Notification

# Notifications for founder Sarah
founder_notifications = [
    {
        "recipient": founder,
        "actor": None,
        "notification_type": Notification.Type.NEW_MATCH,
        "title": "New Match Found!",
        "message": "You've been matched with investor Marcus Williams. Your Nova AI startup aligns well with his investment criteria.",
        "is_read": True,
    },
    {
        "recipient": founder,
        "actor": investor,
        "notification_type": Notification.Type.MESSAGE_RECEIVED,
        "title": "New Message from Marcus Williams",
        "message": "Marcus Williams sent you a message: 'I've reviewed your pitch deck and I'm very interested.'",
        "is_read": True,
    },
    {
        "recipient": founder,
        "actor": investor,
        "notification_type": Notification.Type.DEAL_CREATED,
        "title": "Investment Interest Received",
        "message": "Marcus Williams is interested in investing $200K in Nova AI.",
        "is_read": False,
    },
    {
        "recipient": founder,
        "actor": None,
        "notification_type": Notification.Type.PROFILE_VIEWED,
        "title": "Profile Viewed",
        "message": "Your Nova AI startup profile was viewed by Elena Rodriguez.",
        "is_read": False,
    },
    {
        "recipient": founder,
        "actor": investor,
        "notification_type": Notification.Type.SYSTEM,
        "title": "Meeting Confirmed",
        "message": "Due Diligence meeting with Marcus Williams has been confirmed for June 22.",
        "is_read": True,
    },
    {
        "recipient": founder,
        "actor": None,
        "notification_type": Notification.Type.SYSTEM,
        "title": "New Feature Available",
        "message": "The AI-powered match insights feature is now available. Check your matches for detailed analysis.",
        "is_read": False,
    },
    {
        "recipient": founder,
        "actor": investor,
        "notification_type": Notification.Type.DOCUMENT_UPLOADED,
        "title": "Document Requested",
        "message": "Marcus Williams has requested access to your financial documents.",
        "is_read": False,
    },
]

for notif_data in founder_notifications:
    Notification.objects.create(**notif_data)

print(f"  Created {len(founder_notifications)} notifications for Sarah")

# Notifications for investor Marcus
investor_notifications = [
    {
        "recipient": investor,
        "actor": None,
        "notification_type": Notification.Type.NEW_MATCH,
        "title": "New Match Found!",
        "message": "You've been matched with founder Sarah Chen. Her startup Nova AI aligns with your fintech focus.",
        "is_read": True,
    },
    {
        "recipient": investor,
        "actor": founder,
        "notification_type": Notification.Type.MESSAGE_RECEIVED,
        "title": "New Message from Sarah Chen",
        "message": "Sarah Chen sent you a message in 'General Discussion'.",
        "is_read": True,
    },
    {
        "recipient": investor,
        "actor": None,
        "notification_type": Notification.Type.DEAL_STAGE_CHANGED,
        "title": "Deal Progress Update",
        "message": "Your investment opportunity with Nova AI has progressed to Due Diligence stage.",
        "is_read": True,
    },
    {
        "recipient": investor,
        "actor": None,
        "notification_type": Notification.Type.NEW_MATCH,
        "title": "New Match: GreenGrow",
        "message": "You've been matched with GreenGrow, a sustainable agriculture startup.",
        "is_read": False,
    },
    {
        "recipient": investor,
        "actor": founder,
        "notification_type": Notification.Type.SYSTEM,
        "title": "Meeting Confirmed",
        "message": "Due Diligence meeting with Sarah Chen has been confirmed for June 22.",
        "is_read": True,
    },
    {
        "recipient": investor,
        "actor": None,
        "notification_type": Notification.Type.SYSTEM,
        "title": "Weekly Digest Available",
        "message": "Your weekly investment digest is ready. View new matches and updates.",
        "is_read": False,
    },
    {
        "recipient": investor,
        "actor": None,
        "notification_type": Notification.Type.PROFILE_VIEWED,
        "title": "Profile Viewed",
        "message": "Your investor profile was viewed by Priya Patel (founder of BlockGrid).",
        "is_read": False,
    },
    {
        "recipient": investor,
        "actor": founder,
        "notification_type": Notification.Type.MESSAGE_RECEIVED,
        "title": "New Message from Sarah Chen",
        "message": "Sarah Chen sent you a message: 'That would be fantastic. Let's discuss terms.'",
        "is_read": False,
    },
]

for notif_data in investor_notifications:
    Notification.objects.create(**notif_data)

print(f"  Created {len(investor_notifications)} notifications for Marcus")

# ─── Section: Investment Opportunities ────────────────────────────────────────
print("\n=== Creating Investment Opportunities ===")

from apps.investments.models import InvestmentOpportunity

invs_data = [
    {
        "startup": startups["Nova AI"],
        "investor": investor,
        "amount_requested": 500000,
        "amount_offered": 200000,
        "equity_requested": 10.00,
        "equity_offered": 5.00,
        "valuation": 5000000,
        "proposed_valuation": 4000000,
        "status": InvestmentOpportunity.Status.INTERESTED,
        "notes": "Interested in investing $200K at $4M valuation.",
    },
    {
        "startup": startups["HealthSync"],
        "investor": investor,
        "amount_requested": 250000,
        "amount_offered": 150000,
        "equity_requested": 12.00,
        "equity_offered": 8.00,
        "valuation": 2000000,
        "proposed_valuation": 1800000,
        "status": InvestmentOpportunity.Status.DUE_DILIGENCE,
        "notes": "Proceeding with due diligence - reviewing financials and market analysis.",
    },
    {
        "startup": startups["GreenGrow"],
        "investor": elena,
        "amount_requested": 2000000,
        "amount_offered": 200000,
        "equity_requested": 15.00,
        "equity_offered": 3.00,
        "valuation": 12000000,
        "proposed_valuation": 10000000,
        "status": InvestmentOpportunity.Status.MEETING_SCHEDULED,
        "notes": "Initial meeting scheduled to discuss partnership.",
    },
]

for inv_data in invs_data:
    obj, created = InvestmentOpportunity.objects.update_or_create(
        startup=inv_data["startup"],
        investor=inv_data["investor"],
        defaults=inv_data,
    )
    print(f"  {'Created' if created else 'Updated'} investment: {obj}")

# ─── Section: Activity Feed ───────────────────────────────────────────────────
print("\n=== Creating Activity Feed ===")

from apps.activity_feed.models import ActivityFeed

feed_data = [
    {
        "actor": founder,
        "activity_type": ActivityFeed.ActivityType.STARTUP_CREATED,
        "startup": startups["Nova AI"],
        "title": "Sarah Chen launched Nova AI",
        "description": "A new fintech AI platform has joined the Investo community.",
        "visibility": ActivityFeed.Visibility.PUBLIC,
    },
    {
        "actor": investor,
        "activity_type": ActivityFeed.ActivityType.INVESTOR_JOINED,
        "investor": investor,
        "title": "Marcus Williams joined as an investor",
        "description": "Experienced VC focusing on SaaS, FinTech, and AI/ML startups.",
        "visibility": ActivityFeed.Visibility.PUBLIC,
    },
    {
        "actor": founder,
        "activity_type": ActivityFeed.ActivityType.MEETING_SCHEDULED,
        "startup": startups["Nova AI"],
        "investor": investor,
        "title": "Meeting scheduled with Marcus Williams",
        "description": "Due Diligence meeting scheduled to discuss Nova AI investment opportunity.",
        "visibility": ActivityFeed.Visibility.CONNECTIONS,
    },
    {
        "actor": founder,
        "activity_type": ActivityFeed.ActivityType.MEETING_COMPLETED,
        "startup": startups["Nova AI"],
        "investor": investor,
        "title": "Pitch meeting completed successfully",
        "description": "Nova AI delivered an impressive pitch to Marcus Williams.",
        "visibility": ActivityFeed.Visibility.CONNECTIONS,
    },
    {
        "actor": priya,
        "activity_type": ActivityFeed.ActivityType.STARTUP_PUBLISHED,
        "startup": startups["GreenGrow"],
        "title": "GreenGrow is now seeking Series A funding",
        "description": "Sustainable agriculture startup GreenGrow is raising $2M for Series A.",
        "visibility": ActivityFeed.Visibility.PUBLIC,
    },
    {
        "actor": founder,
        "activity_type": ActivityFeed.ActivityType.STARTUP_CREATED,
        "startup": startups["HealthSync"],
        "title": "Sarah Chen launched HealthSync",
        "description": "A new digital health platform connecting patients and providers.",
        "visibility": ActivityFeed.Visibility.PUBLIC,
    },
    {
        "actor": elena,
        "activity_type": ActivityFeed.ActivityType.INVESTOR_JOINED,
        "investor": elena,
        "title": "Elena Rodriguez joined as an investor",
        "description": "Angel investor passionate about health tech, climate tech, and deep tech.",
        "visibility": ActivityFeed.Visibility.PUBLIC,
    },
]

for feed_item_data in feed_data:
    ActivityFeed.objects.create(**feed_item_data)

print(f"  Created {len(feed_data)} feed activities")

# ─── Section: Data Room ──────────────────────────────────────────────────────
print("\n=== Creating Data Room ===")

from apps.data_room.models import DataRoom, DataRoomDocument

data_rooms_data = [
    {
        "startup": startups["Nova AI"],
        "title": "Nova AI - Investor Data Room",
        "description": "Comprehensive data room for potential investors in Nova AI.",
        "visibility": DataRoom.Visibility.MATCHED_INVESTORS,
        "created_by": founder,
    },
    {
        "startup": startups["GreenGrow"],
        "title": "GreenGrow - Series A Data Room",
        "description": "Due diligence documents for Series A investors.",
        "visibility": DataRoom.Visibility.SELECTED_INVESTORS,
        "created_by": priya,
    },
    {
        "startup": startups["HealthSync"],
        "title": "HealthSync - Pitch Materials",
        "description": "Pitch deck and supporting materials for HealthSync.",
        "visibility": DataRoom.Visibility.MATCHED_INVESTORS,
        "created_by": founder,
    },
]

for dr_data in data_rooms_data:
    dr, created = DataRoom.objects.get_or_create(
        startup=dr_data["startup"],
        title=dr_data["title"],
        defaults=dr_data,
    )

    # Add documents to each data room
    docs_data = [
        {"title": "Pitch Deck", "document_type": DataRoomDocument.DocumentType.PITCH_DECK},
        {"title": "Financial Projections", "document_type": DataRoomDocument.DocumentType.FINANCIALS},
        {"title": "Cap Table", "document_type": DataRoomDocument.DocumentType.CAP_TABLE},
    ]
    for doc_data in docs_data:
        doc, doc_created = DataRoomDocument.objects.get_or_create(
            data_room=dr,
            title=doc_data["title"],
            defaults={
                "document_type": doc_data["document_type"],
                "uploaded_by": dr_data["created_by"],
                "file_size": 1024,
                "mime_type": "application/pdf",
            },
        )
        if doc_created:
            print(f"    Created document: {doc.title}")
    print(f"  {'Created' if created else 'Updated'} data room: {dr.title}")

# ─── Section: Billing / Subscription Plans ────────────────────────────────────
print("\n=== Creating Subscription Plans ===")

from apps.billing.models import SubscriptionPlan, UserSubscription

plans_data = [
    {
        "name": "Free",
        "slug": "free",
        "tier": SubscriptionPlan.Tier.FREE,
        "description": "Basic access to the Investo platform",
        "monthly_price": 0,
        "yearly_price": 0,
        "features": {
            "startup_profiles": 1,
            "matches_per_month": 5,
            "messages_per_day": 10,
        },
        "limits": {
            "max_startups": 1,
            "max_documents": 5,
        },
        "sort_order": 0,
        "is_active": True,
    },
    {
        "name": "Pro",
        "slug": "pro",
        "tier": SubscriptionPlan.Tier.FOUNDER_PREMIUM,
        "description": "Premium access for serious founders",
        "monthly_price": 29.00,
        "yearly_price": 290.00,
        "features": {
            "startup_profiles": 5,
            "matches_per_month": 50,
            "messages_per_day": 100,
            "priority_support": True,
        },
        "limits": {
            "max_startups": 5,
            "max_documents": 50,
        },
        "sort_order": 1,
        "is_active": True,
        "is_popular": True,
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "tier": SubscriptionPlan.Tier.ENTERPRISE,
        "description": "Full platform access with premium features",
        "monthly_price": 99.00,
        "yearly_price": 990.00,
        "features": {
            "startup_profiles": "unlimited",
            "matches_per_month": "unlimited",
            "messages_per_day": "unlimited",
            "priority_support": True,
            "dedicated_account_manager": True,
            "advanced_analytics": True,
        },
        "limits": {
            "max_startups": 999,
            "max_documents": 999,
        },
        "sort_order": 2,
        "is_active": True,
    },
]

for plan_data in plans_data:
    obj, created = SubscriptionPlan.objects.update_or_create(
        slug=plan_data["slug"],
        defaults=plan_data,
    )
    print(f"  {'Created' if created else 'Updated'} plan: {obj.name} (${obj.monthly_price}/mo)")

# Subscribe founder Sarah to Pro plan
pro_plan = SubscriptionPlan.objects.get(slug="pro")
UserSubscription.objects.update_or_create(
    user=founder,
    defaults={
        "plan": pro_plan,
        "status": UserSubscription.Status.ACTIVE,
        "billing_cycle": UserSubscription.BillingCycle.MONTHLY,
        "start_date": now - timedelta(days=30),
        "auto_renew": True,
    },
)
print(f"  Subscribed Sarah to Pro plan")

# Subscribe investor Marcus to Enterprise plan
enterprise_plan = SubscriptionPlan.objects.get(slug="enterprise")
UserSubscription.objects.update_or_create(
    user=investor,
    defaults={
        "plan": enterprise_plan,
        "status": UserSubscription.Status.ACTIVE,
        "billing_cycle": UserSubscription.BillingCycle.YEARLY,
        "start_date": now - timedelta(days=60),
        "auto_renew": True,
    },
)
print(f"  Subscribed Marcus to Enterprise plan")

# ─── Section: Platform Settings ───────────────────────────────────────────────
print("\n=== Creating Platform Settings ===")

from apps.settings.models import PlatformSetting, FeatureFlag, MaintenanceMode

settings_data = [
    {
        "key": "platform_name",
        "label": "Platform Name",
        "value_type": PlatformSetting.ValueType.STRING,
        "string_value": "Investo",
        "group": "general",
    },
    {
        "key": "max_startups_per_user",
        "label": "Maximum Startups Per User",
        "value_type": PlatformSetting.ValueType.INTEGER,
        "integer_value": 10,
        "group": "limits",
    },
    {
        "key": "match_auto_approve",
        "label": "Auto Approve Matches",
        "value_type": PlatformSetting.ValueType.BOOLEAN,
        "boolean_value": True,
        "group": "matching",
    },
    {
        "key": "default_match_threshold",
        "label": "Default Match Threshold",
        "value_type": PlatformSetting.ValueType.FLOAT,
        "float_value": 60.0,
        "group": "matching",
    },
    {
        "key": "welcome_message",
        "label": "Welcome Message",
        "value_type": PlatformSetting.ValueType.STRING,
        "string_value": "Welcome to Investo! Start connecting with investors and founders.",
        "group": "general",
    },
]

for s_data in settings_data:
    obj, created = PlatformSetting.objects.update_or_create(
        key=s_data["key"],
        defaults=s_data,
    )
    print(f"  {'Created' if created else 'Updated'} setting: {obj}")

# Feature Flags
feature_flags_data = [
    {
        "key": "ai_match_insights",
        "label": "AI Match Insights",
        "description": "Enable AI-powered match insights and recommendations",
        "enabled": True,
        "enabled_for_roles": ["entrepreneur", "investor"],
    },
    {
        "key": "video_meetings",
        "label": "Video Meetings",
        "description": "Enable in-platform video meeting capabilities",
        "enabled": True,
        "enabled_for_roles": ["entrepreneur", "investor", "mentor"],
    },
    {
        "key": "data_room",
        "label": "Data Room",
        "description": "Enable data room for document sharing",
        "enabled": True,
        "enabled_for_roles": ["entrepreneur", "investor"],
    },
    {
        "key": "advanced_analytics",
        "label": "Advanced Analytics",
        "description": "Enable advanced analytics dashboard",
        "enabled": False,
        "enabled_for_roles": ["enterprise"],
    },
]

for ff_data in feature_flags_data:
    obj, created = FeatureFlag.objects.update_or_create(
        key=ff_data["key"],
        defaults=ff_data,
    )
    print(f"  {'Created' if created else 'Updated'} feature flag: {obj}")

# Maintenance Mode
MaintenanceMode.objects.update_or_create(
    pk=1,
    defaults={
        "is_active": False,
        "title": "Under Maintenance",
        "message": "We are performing scheduled maintenance. Please check back shortly.",
    },
)
print("  Created maintenance mode entry (inactive)")

# ─── Section: Onboarding ───────────────────────────────────────────────────────
print("\n=== Creating Onboarding Data ===")

from apps.onboarding.models import (
    OnboardingWizard,
    OnboardingStep,
    FounderOnboardingData,
    InvestorOnboardingData,
)

# Sarah's founder onboarding
wizard_founder, created = OnboardingWizard.objects.update_or_create(
    user=founder,
    defaults={
        "wizard_type": OnboardingWizard.WizardType.FOUNDER,
        "current_step": "complete",
        "is_complete": True,
    },
)
print(f"  {'Created' if created else 'Updated'} founder onboarding wizard for Sarah")

founder_steps = [
    {"step_key": "profile", "step_label": "Create Profile", "is_completed": True},
    {"step_key": "company", "step_label": "Company Details", "is_completed": True},
    {"step_key": "pitch", "step_label": "Pitch Deck", "is_completed": True},
    {"step_key": "team", "step_label": "Team Information", "is_completed": True},
    {"step_key": "funding", "step_label": "Funding Requirements", "is_completed": True},
    {"step_key": "complete", "step_label": "Complete", "is_completed": True},
]
for step_data in founder_steps:
    OnboardingStep.objects.update_or_create(
        wizard=wizard_founder,
        step_key=step_data["step_key"],
        defaults={
            "step_label": step_data["step_label"],
            "is_completed": step_data["is_completed"],
            "completed_at": now - timedelta(days=20) if step_data["is_completed"] else None,
            "data": {"completed": True},
        },
    )
print(f"  Created {len(founder_steps)} onboarding steps for Sarah")

FounderOnboardingData.objects.update_or_create(
    user=founder,
    defaults={
        "company_name": "Nova AI",
        "tagline": "AI-powered fintech intelligence platform",
        "industry": "ai_ml",
        "funding_stage": "seed",
        "team_size": 8,
        "business_model": "B2B SaaS",
        "target_market": "Financial institutions and investment firms",
        "revenue_model": "Subscription-based pricing with enterprise tiers",
        "traction": "$50K MRR, 3 enterprise clients, 20% MoM growth",
        "competitors": "Bloomberg Terminal, AlphaSense, Sentieo",
    },
)
print("  Created founder onboarding data for Sarah")

# Marcus's investor onboarding
wizard_investor, created = OnboardingWizard.objects.update_or_create(
    user=investor,
    defaults={
        "wizard_type": OnboardingWizard.WizardType.INVESTOR,
        "current_step": "complete",
        "is_complete": True,
    },
)
print(f"  {'Created' if created else 'Updated'} investor onboarding wizard for Marcus")

investor_steps = [
    {"step_key": "profile", "step_label": "Create Profile", "is_completed": True},
    {"step_key": "preferences", "step_label": "Investment Preferences", "is_completed": True},
    {"step_key": "focus", "step_label": "Areas of Focus", "is_completed": True},
    {"step_key": "portfolio", "step_label": "Portfolio", "is_completed": True},
    {"step_key": "complete", "step_label": "Complete", "is_completed": True},
]
for step_data in investor_steps:
    OnboardingStep.objects.update_or_create(
        wizard=wizard_investor,
        step_key=step_data["step_key"],
        defaults={
            "step_label": step_data["step_label"],
            "is_completed": step_data["is_completed"],
            "completed_at": now - timedelta(days=25) if step_data["is_completed"] else None,
            "data": {"completed": True},
        },
    )
print(f"  Created {len(investor_steps)} onboarding steps for Marcus")

InvestorOnboardingData.objects.update_or_create(
    user=investor,
    defaults={
        "investor_type": "vc",
        "bio": "Experienced VC focused on early-stage SaaS and fintech companies.",
        "investment_focus": "SaaS, FinTech, AI/ML",
        "preferred_industries": ["saas", "fintech", "ai_ml"],
        "preferred_stages": ["seed", "series_a"],
        "ticket_size_min": 50000,
        "ticket_size_max": 500000,
        "preferred_geographies": ["San Francisco", "United States"],
        "years_experience": 12,
        "portfolio_companies": ["DataStream Analytics", "PayFlow Solutions", "CloudSecure Inc."],
    },
)
print("  Created investor onboarding data for Marcus")

# ─── Section: Analytics (if model exists) ──────────────────────────────────────
print("\n=== Creating Analytics ===")

try:
    from apps.analytics.models import AnalyticsSnapshot

    analytics_data = [
        {
            "name": "Platform Overview",
            "metric_key": "total_users",
            "metric_value": 5,
        },
        {
            "name": "Platform Overview",
            "metric_key": "total_startups",
            "metric_value": 5,
        },
        {
            "name": "Platform Overview",
            "metric_key": "total_matches",
            "metric_value": 8,
        },
        {
            "name": "Platform Overview",
            "metric_key": "total_meetings",
            "metric_value": 5,
        },
    ]
    for a_data in analytics_data:
        AnalyticsSnapshot.objects.create(**a_data)
    print(f"  Created {len(analytics_data)} analytics snapshots")
except (ImportError, AttributeError):
    print("  AnalyticsSnapshot model not found - skipping")

# ─── Section: Notification Preferences ──────────────────────────────────────
print("\n=== Creating Notification Preferences ===")

from apps.notifications.models import NotificationPreference

for user_obj in [founder, investor, priya, elena]:
    obj, created = NotificationPreference.objects.update_or_create(
        user=user_obj,
        defaults={
            "email_enabled": True,
            "push_enabled": True,
            "in_app_enabled": True,
            "matching_notifications": True,
            "investment_notifications": True,
            "chat_notifications": True,
            "document_notifications": True,
        },
    )
    print(f"  {'Created' if created else 'Updated'} notification preferences for {user_obj.email}")

# ─── Final Message ────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("✅ Seed data created successfully!")
print("=" * 50)
