import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import requests

User = get_user_model()
founder = User.objects.get(email='founder@test.com')
investor = User.objects.get(email='investor@test.com')

def get_token(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)

founder_token = get_token(founder)
investor_token = get_token(investor)

print("=== 1. STARTUPS ===")
res = requests.get('http://localhost:8000/api/v1/startups/', headers={'Authorization': f'Bearer {founder_token}'})
print("Status:", res.status_code)
print("Data is list:", isinstance(res.json().get('data', res.json()), list) if res.status_code == 200 else False)

print("\n=== 2. CHAT ===")
res = requests.get('http://localhost:8000/api/v1/chat/conversations/', headers={'Authorization': f'Bearer {founder_token}'})
print("Status:", res.status_code)
data = res.json()
print("Top-level keys:", list(data.keys()))
if 'results' in data:
    print("Results keys:", list(data['results'].keys()))

print("\n=== 3. MATCHES (FOUNDER) ===")
res = requests.get('http://localhost:8000/api/v1/matching/investor/matches/', headers={'Authorization': f'Bearer {founder_token}'})
print("Status:", res.status_code)

print("\n=== 4. MATCHES (INVESTOR) ===")
res = requests.get('http://localhost:8000/api/v1/matching/entrepreneur/matches/', headers={'Authorization': f'Bearer {investor_token}'})
print("Status:", res.status_code)
