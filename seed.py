import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
from apps.accounts.models import EntrepreneurProfile, InvestorProfile
from apps.startups.models import Startup

User.objects.all().delete()

admin = User.objects.create_superuser('admin@investo.com', password='password123')
print("Created admin@investo.com")

founder = User.objects.create_user(email='founder@test.com', password='password123', first_name='Founder', last_name='Test', role='entrepreneur')
ep = EntrepreneurProfile.objects.get(user=founder)
ep.company_name = "Test Startup"
ep.industry = "SaaS"
ep.save()

Startup.objects.create(owner=founder, name="Test Startup", tagline="Tagline", industry="SaaS", stage="Idea")
print("Created founder@test.com")

investor = User.objects.create_user(email='investor@investo.com', password='password123', first_name='Investor', last_name='Test', role='investor')
ip = InvestorProfile.objects.get(user=investor)
ip.firm_name = "Test VC"
ip.investment_focus = "SaaS"
ip.save()
print("Created investor@investo.com")
