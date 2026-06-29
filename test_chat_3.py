import os
import sys
import django

sys.path.append('e:/projects from desktops/investo-main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.chat.models import ConversationParticipant

ps = ConversationParticipant.objects.filter(conversation_id=16)
print("Participants in 16:")
for p in ps:
    print(f"- User ID: {p.user_id}, Email: {p.user.email}")
