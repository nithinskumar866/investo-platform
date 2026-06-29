import os
import sys
import django

sys.path.append('e:/projects from desktops/investo-main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.chat.repositories import ChatRepository
from django.contrib.auth import get_user_model
User = get_user_model()

# Get the last 2 created users
users = User.objects.order_by('-id')[:2]
if len(users) == 2:
    u1, u2 = users
    
    # Check conversations for u1
    qs1 = ChatRepository.get_user_conversations(u1)
    print(f'Query for u1: {qs1.query}')
    
    # Check conversations for u2
    qs2 = ChatRepository.get_user_conversations(u2)
    print(f'Query for u2: {qs2.query}')
