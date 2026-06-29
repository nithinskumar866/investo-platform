import sys
import time
import json
from django.db import connection, reset_queries

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

def measure_endpoint(url, method='get', user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    
    reset_queries()
    
    start_time = time.time()
    
    if method == 'get':
        response = client.get(url)
    
    end_time = time.time()
    
    response_time = (end_time - start_time) * 1000  # ms
    queries = connection.queries
    query_count = len(queries)
    db_time = sum(float(q.get('time', 0)) for q in queries) * 1000  # ms
    
    content = response.content
    payload_size = len(content)
    
    # Try to parse objects count
    try:
        data = response.json()
        if isinstance(data, list):
            obj_count = len(data)
        elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
            obj_count = len(data['data'])
        elif isinstance(data, dict) and 'results' in data and isinstance(data['results'], list):
            obj_count = len(data['results'])
        else:
            obj_count = 1
    except:
        obj_count = 0

    return {
        'status_code': response.status_code,
        'response_time_ms': round(response_time, 2),
        'query_count': query_count,
        'db_time_ms': round(db_time, 2),
        'payload_size_bytes': payload_size,
        'returned_objects': obj_count
    }

def run_audit():
    User = get_user_model()
    # Find an admin, founder, and investor
    admin = User.objects.filter(is_staff=True).first()
    founder = User.objects.filter(role='entrepreneur').first()
    investor = User.objects.filter(role='investor').first()
    
    endpoints = [
        {"url": "/api/v1/auth/profiles/investor/", "user": None, "name": "Public Investor Profiles"},
        {"url": "/api/v1/admin/users/", "user": admin, "name": "Admin Users List"},
        {"url": "/api/v1/admin/tickets/", "user": admin, "name": "Admin Tickets List"},
        {"url": "/api/v1/admin/revenue/", "user": admin, "name": "Admin Revenue"},
        {"url": "/api/v1/analytics/founder/charts/", "user": founder, "name": "Founder Analytics Charts"},
        {"url": "/api/v1/analytics/investor/charts/", "user": investor, "name": "Investor Analytics Charts"},
    ]
    
    results = {}
    for ep in endpoints:
        print(f"Measuring {ep['name']}...")
        if not ep['user'] and ep['name'] != "Public Investor Profiles":
            print(f"Skipping {ep['name']} (no suitable user found)")
            continue
        try:
            res = measure_endpoint(ep['url'], user=ep['user'])
            results[ep['name']] = res
        except Exception as e:
            print(f"Error measuring {ep['name']}: {e}")
            results[ep['name']] = {"error": str(e)}
            
    print("\n--- RESULTS ---\n")
    print(json.dumps(results, indent=2))
