---
trigger: always_on
---

# Investo Workspace Context

## Project Overview

Investo is a founder-investor networking, matching, fundraising, and investment management platform.

The platform connects startup founders and investors through discovery, matching, communication, meetings, due diligence, investments, analytics, and portfolio workflows.

## Current Project State

Backend is largely implemented.

Major completed modules include:

* Authentication & User Management
* Founder Profiles
* Investor Profiles
* Startup Management
* Matching Engine
* AI Match Intelligence
* Chat System
* Meeting Scheduler
* Investment Pipeline
* Data Room & Document Management
* Notifications
* Activity Feed & Discovery
* Advanced Search
* Analytics & Dashboards
* Billing & Subscriptions
* Admin Operations Console
* Observability & Monitoring
* Onboarding
* Platform Settings
* Testing Infrastructure
* Real-Time Communication Layer

## Current Priority

The project is NOT in feature expansion mode.

Primary focus:

1. Frontend integration
2. UI/UX improvements
3. Bug fixing
4. End-to-end testing
5. Performance optimization
6. Production readiness
7. Deployment preparation

Before proposing new modules, evaluate whether the requirement can be solved using existing modules.

## Technology Stack

### Backend

* Django
* Django REST Framework
* PostgreSQL
* Redis
* Celery
* Django Channels
* JWT Authentication

### Frontend

* Next.js App Router
* TypeScript
* Zustand
* TanStack Query
* Tailwind CSS
* shadcn/ui

### Infrastructure Preference

Prefer:

* Free-tier friendly solutions
* Open-source tools
* Self-hostable services
* Low operational cost

Avoid introducing paid infrastructure unless explicitly requested.

## Engineering Rules

* Understand existing implementation before modifying code.
* Audit first, implement second.
* Prefer minimal changes over large refactors.
* Preserve existing architecture patterns.
* Fix root causes instead of applying temporary workarounds.
* Do not create placeholder implementations.
* Keep code production-oriented.

## Architecture Rules

Maintain:

View → Service → Repository → Model

Rules:

* No ORM queries inside views.
* Business logic belongs in services.
* Data access belongs in repositories.
* Keep responsibilities separated.

## Output Expectations

When working on tasks:

1. Explain findings briefly.
2. Identify affected files.
3. Describe implementation plan.
4. Implement changes.
5. Mention risks if any.
6. Suggest verification steps.

## Product Goal

Deliver a production-ready platform where:

Founder:
Register → Create Startup → Match → Chat → Meet → Data Room → Investment

Investor:
Register → Discover → Match → Chat → Meet → Due Diligence → Invest

Optimize all future work toward launch readiness rather than feature quantity.
