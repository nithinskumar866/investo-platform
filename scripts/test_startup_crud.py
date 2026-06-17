import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, 'E:\\projects from desktops\\investo-main')
django.setup()

from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.startups.services import StartupService
from apps.startups.models import Startup

User = get_user_model()
entrepreneur = User.objects.get(email='entrepreneur@test.com')

# Test create startup
data = {
    'name': 'New Test Startup',
    'tagline': 'Revolutionizing fintech',
    'description': 'A new AI-powered fintech platform',
    'industry': 'fintech',
    'stage': 'pre_seed',
    'business_model': 'b2b',
    'funding_goal': Decimal('100000'),
    'min_funding': Decimal('50000'),
    'max_funding': Decimal('200000'),
    'equity_offered': Decimal('10'),
    'valuation': Decimal('1000000'),
    'currency': 'USD',
    'location': 'New York',
    'website': 'https://teststartup.com',
    'founded_date': '2024-01-01',
    'team_size': 5,
    'is_visible': True,
    'team_members': [
        {'name': 'John Doe', 'role': 'CEO', 'email': 'john@test.com', 'is_founder': True, 'order': 0},
        {'name': 'Jane Smith', 'role': 'CTO', 'email': 'jane@test.com', 'is_founder': True, 'order': 1},
    ],
    'social_links': [
        {'platform': 'linkedin', 'url': 'https://linkedin.com/company/test'},
    ],
    'metrics': {
        'monthly_revenue': Decimal('10000'),
        'annual_revenue': Decimal('120000'),
        'revenue_growth_pct': Decimal('25'),
        'monthly_active_users': 100,
        'total_users': 500,
        'traction_description': 'Growing 25% MoM',
    }
}

startup = StartupService.create_startup(entrepreneur, data)
print(f'Created startup: {startup.name} (ID: {startup.id})')
print(f'Team members: {startup.team_members.count()}')
print(f'Social links: {startup.social_links.count()}')
print(f'Has metrics: {hasattr(startup, "metrics")}')

# Test update
update_data = {
    'name': 'Updated Startup Name',
    'tagline': 'Updated tagline',
    'team_members': [
        {'name': 'John Doe', 'role': 'CEO', 'email': 'john@test.com', 'is_founder': True, 'order': 0},
        {'name': 'Jane Smith', 'role': 'CTO', 'email': 'jane@test.com', 'is_founder': True, 'order': 1},
        {'name': 'Bob Wilson', 'role': 'COO', 'email': 'bob@test.com', 'is_founder': False, 'order': 2},
    ],
}
updated = StartupService.update_startup(startup, update_data)
print(f'Updated startup name: {updated.name}')
print(f'Team members after update: {updated.team_members.count()}')

# Test view count increment
StartupService.increment_view_count(startup)
startup.refresh_from_db()
print(f'View count after increment: {startup.view_count}')

print('SUCCESS: Startup CRUD operations work!')