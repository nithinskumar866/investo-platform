web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2 --worker-class gthread
channels: daphne -b 0.0.0.0 -p 8001 config.asgi:application
worker: celery -A config worker -l info -c 4
beat: celery -A config beat -l info
