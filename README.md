# Investo

A platform that connects startup founders with investors: discovery, AI-assisted matching, chat, meetings, data rooms and a deal pipeline.

**This is a college project. All money is simulated.** Subscriptions use a demo checkout and deals record dummy amounts; no real payment or investment takes place.

## Stack

- **Backend:** Django, Django REST Framework, Channels, Celery, PostgreSQL, Redis
- **Frontend:** Next.js 15, TypeScript, TanStack Query, Zustand, Tailwind CSS
- **AI:** local models through [Ollama](https://ollama.com), so nothing leaves your machine

## Run it locally

You need Python 3.12, Node 22 and Docker.

```bash
# 1. Configuration
cp .env.example .env              # then set DJANGO_SECRET_KEY to a long random string

# 2. Postgres and Redis (set POSTGRES_PORT and DB_PORT if 5432 is taken)
docker compose -f docker/docker-compose.yml up -d postgres redis

# 3. Backend
python -m venv .venv
.venv/Scripts/activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements/development.txt
python manage.py migrate
python seed_data.py
python manage.py runserver

# 4. Frontend, in a second terminal
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

Open http://localhost:3000.

### AI features (optional)

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
python manage.py pregenerate_insights --limit 10
```

Each match explanation takes up to a minute on a CPU, so generate them before a demo. If Ollama isn't running, the app still works: explanations use rule-based text and matching uses keywords.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Founder | founder@investo.com | founder123 |
| Investor | investor@investo.com | investor123 |
| Admin | admin@investo.com | admin123 |

These exist only in seeded local data.

## The core journey

1. A founder creates and publishes a startup, which generates investor matches.
2. An investor discovers the startup, reads the AI explanation of the match, and opens a chat or requests a meeting (with a real Jitsi video link).
3. The investor requests data room access, and the founder approves or denies it.
4. The investor expresses interest and moves the deal through its stages, then sends a term sheet.
5. The founder accepts the term sheet, and the investor closes the deal with a dummy amount.
6. The startup's funding progress updates.

## Tests

```bash
# Backend (needs Postgres and Redis running)
DJANGO_SETTINGS_MODULE=config.settings.testing pytest

# Frontend end-to-end (needs backend and frontend running, with seeded data)
cd frontend && npx playwright test tests/core_journey.spec.ts
```

## Project layout

- `apps/`: Django apps, each following View → Service → Repository → Model
- `config/`: settings, URLs, ASGI and Celery setup
- `frontend/`: Next.js app
- `docker/`, `nginx/`: container and proxy configuration
- `seed_data.py`: demo data

## Known limitations

- Real payments, KYC and e-signature are out of scope.
- Chat polls every 5 seconds; the WebSocket consumers exist but the frontend doesn't use them.
- Email verification is available but not required to use the app.
- Auth tokens are kept in browser localStorage, which is fine for a demo but not for production.
