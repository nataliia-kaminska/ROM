# Research Opportunity Matcher

Intelligent system for personalized discovery of academic grants, exchange programs, fellowships, research positions, and other educational or career-related scientific opportunities.

The product is similar in spirit to Djinni, but instead of job hunting it focuses on academic and research growth. A researcher creates or imports a profile, the system gathers opportunities from real sources, and a matching engine ranks the best options with clear reasons and deadline workflow support.

## Product Goal

Build a complete web application that helps researchers:

- create a rich academic profile;
- import public profile data from ORCID and other safe integrations;
- discover relevant grants, exchanges, fellowships, trainings, and research positions;
- understand why each opportunity matches them;
- save, ignore, plan, apply, and track outcomes;
- receive deadline reminders;
- eventually get AI assistance for application preparation.

## System Scope

The full system includes:

- Python backend API;
- frontend web application;
- relational database;
- vector search database support;
- background workers for ingestion and reminders;
- external integrations;
- admin tools for opportunity curation;
- authentication and user ownership;
- deployment, monitoring, and production configuration.

## MVP Core

Current backend MVP covers:

- researcher profiles with disciplines, keywords, career stage, countries, and external links;
- richer profile details: summary, publications, degrees, languages, funding interests, unavailable countries, preferred opportunity types;
- opportunity catalog with eligibility, deadline, source, and topic metadata;
- live Grants.gov ingestion;
- curated bulk opportunity import;
- ORCID public profile import;
- deterministic recommendation scoring with human-readable reasons;
- saved, ignored, planned, applied, rejected, and accepted statuses;
- automatic and manual deadline reminders;
- isolated backend tests.

Local development uses SQLite by default. Production should use PostgreSQL with pgvector.

## Target Architecture

```text
frontend/
  web app: React or Next.js
  UI: researcher dashboard, opportunity feed, profile editor, reminders, admin import

backend/
  FastAPI REST API
  SQLAlchemy models and Alembic migrations
  recommendation and ingestion services
  auth, integrations, background jobs

database/
  PostgreSQL
  pgvector for semantic matching
  Redis for worker queues and caching

workers/
  opportunity ingestion jobs
  embedding generation jobs
  reminder and notification jobs

external services/
  Grants.gov
  ORCID
  curated EURAXESS/DAAD/Fulbright/Erasmus imports
  email provider
  optional OpenAI or local embedding provider
```

## Recommended Stack

Backend:

- Python 3.11+
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- Redis
- Celery or RQ
- Pydantic
- pytest

Frontend:

- React or Next.js
- TypeScript
- Tailwind CSS or another consistent design system
- TanStack Query for API state
- React Hook Form for profile and import forms
- Playwright for end-to-end tests

Infrastructure:

- Docker Compose for local development
- PostgreSQL and Redis containers
- GitHub Actions or similar CI
- production deployment on Render, Fly.io, Railway, DigitalOcean, AWS, or university infrastructure
- Sentry or equivalent error monitoring

## Run Locally

SQLite development mode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open:

- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

Run tests:

```powershell
python -m pytest
```

## Algorithm Description

Recommendations use a hybrid ranking model. The backend computes separate score components for semantic similarity, eligibility fit, deadline urgency, and user history. The final score is a weighted blend:

```text
final_score =
  w_semantic * semantic_score +
  w_eligibility * eligibility_score +
  w_deadline * deadline_score +
  w_history * user_history_score
```

Semantic embeddings use a provider abstraction. Local/test mode uses deterministic hash embeddings. V1-ready mode can use a local `sentence-transformers` model and PostgreSQL `pgvector` for nearest-neighbor candidate retrieval. User feedback from saved, planned, applied, accepted, and ignored statuses adjusts the history component and appears in recommendation explanations.

Make shortcuts:

```powershell
make setup
make backend
make frontend
make worker
make scheduler
make run-full-app
make test
make migrate
make docker-up
make docker-down
```

Windows note: PowerShell does not ship with GNU Make, so `make` can fail with `The term 'make' is not recognized`.
Either install Make through Chocolatey, Scoop, Git Bash/MSYS2, or WSL, or use the native runner:

```powershell
.\scripts\run-full-app.ps1
```

That starts the backend on `127.0.0.1:8000`, the frontend on `127.0.0.1:3000`, plus worker and scheduler windows.
Worker and scheduler require Redis on `127.0.0.1:6379`. The runner checks for Redis and tries `docker compose up -d redis` if Docker is available. If Redis is still unavailable, backend/frontend start and background processes are skipped with a warning.

For a full local run from PowerShell with infrastructure exposed from Docker Compose, use the local full env:

```powershell
Copy-Item .env.full.local.example .env
docker compose up -d postgres redis elasticsearch
.\scripts\run-full-app.ps1
```

Use `.env.full.example` only when the API, worker, and scheduler also run inside Docker Compose. Docker service names like `redis`, `postgres`, and `elasticsearch` do not resolve from a local `.venv` process.

Useful runner options:

```powershell
.\scripts\run-full-app.ps1 -RequireBackground  # fail if Redis is unavailable
.\scripts\run-full-app.ps1 -NoDockerRedis      # do not try to start Redis through Docker
.\scripts\run-full-app.ps1 -SkipWorker -SkipScheduler
```

Run migrations:

```powershell
python -m alembic upgrade head
```

Local note: if an older SQLite development database contains duplicate opportunity URLs from early testing, delete `research_matcher.db` before applying migrations locally.

Docker development mode with PostgreSQL, pgvector, Redis, Elasticsearch, Groq/local-advisor settings, the API, workers, scheduler, and frontend:

```powershell
Copy-Item .env.full.example .env
# Then replace JWT_SECRET_KEY and GROQ_API_KEY before using AI advisor generation.
docker compose up --build
```

Full mode uses `OPPORTUNITY_EXTRACTION_PROVIDER=groq` to normalize imported opportunity metadata into database fields, and `EMBEDDING_PROVIDER=sentence_transformers` to store real semantic vectors in PostgreSQL/pgvector. For a local `.venv` run without Docker, install the embedding extra before enabling that provider:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[embeddings]"
```

Local full mode also supports `EMBEDDING_AUTO_INSTALL=true`. When `sentence-transformers` is requested but missing, the backend will try to install it with the current Python executable, then load `EMBEDDING_MODEL_NAME`. If install or model download fails, the app logs a warning and falls back to deterministic hash embeddings instead of failing the Matches page.

Open:

- API: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:3000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Elasticsearch: `http://localhost:9200`

Docker Compose also starts:

- `worker`: RQ worker for ingestion and reminder jobs;
- `scheduler`: lightweight scheduler that periodically queues source sync and reminder scan jobs;
- `frontend`: React/Vite interface;
- `elasticsearch`: full-text search engine for indexed opportunity documents.

Realtime WebSocket notifications are exposed at `/ws/notifications`. In Docker mode, workers publish notification events through Redis pub/sub and the API forwards them to connected browser clients.

When `ELASTICSEARCH_ENABLED=true`, keyword opportunity search uses Elasticsearch `multi_match` queries over title, summary, eligibility, keywords, and disciplines. If Elasticsearch is disabled or unavailable, the backend falls back to the database search path.

Run a local worker against your local `.env` Redis/PostgreSQL configuration:

```powershell
python -m app.workers.worker
```

Run the local scheduler:

```powershell
python -m app.workers.scheduler
```

## Operations Checks

Admin monitoring is available from the Admin Console and `/admin/dashboard`. The dashboard reports:

- database connectivity;
- Redis connectivity;
- Elasticsearch cluster health when enabled;
- worker queue depth and failed jobs;
- configured email provider status.

Run a lightweight performance evidence check for the thesis non-functional requirement:

```powershell
.\scripts\performance-check.ps1
```

For authenticated checks, pass a token and profile id through environment variables:

```powershell
$env:ROM_ACCESS_TOKEN = "<access-token>"
$env:ROM_PROFILE_ID = "1"
.\scripts\performance-check.ps1 -RunFrontendBuild
```

The script measures `/opportunities`, `/profiles/me`, `/recommendations/{profile_id}`, and optionally `npm run build`. API checks are expected to complete within 3000 ms during normal local operation.

## Database Backup And Restore

PostgreSQL backups can be created with:

```powershell
.\scripts\backup-postgres.ps1
```

The script uses local `pg_dump` when `DATABASE_URL` and PostgreSQL client tools are available. Otherwise, it falls back to the Docker Compose `postgres` service and writes a timestamped `.dump` file into `backups/`.

Restore a backup with:

```powershell
.\scripts\restore-postgres.ps1 -BackupPath .\backups\research-matcher-YYYYMMDD-HHMMSS.dump
```

Restore uses `pg_restore --clean --if-exists`, so run it only against a database you intend to replace.

## First API Flow

1. `POST /auth/register`
2. Use the returned bearer token in `Authorization: Bearer <token>`
3. `POST /profiles`
4. `POST /opportunities`
5. `POST /ingestion/grants-gov/search`
6. `GET /recommendations/{profile_id}`
7. `PUT /profiles/{profile_id}/opportunities/{opportunity_id}/status`

## Authentication

Register:

```json
POST /auth/register
{
  "email": "ada@example.com",
  "password": "strong-password-123",
  "full_name": "Ada Kovalenko"
}
```

Login:

```json
POST /auth/login
{
  "email": "ada@example.com",
  "password": "strong-password-123"
}
```

Use the returned token:

```text
Authorization: Bearer <access_token>
```

Authenticated profile creation attaches the new profile to the current user. Owned profiles can only be accessed by their owner. Legacy anonymous profiles remain readable during MVP compatibility mode.

Current auth scope:

- JSON register and login endpoints;
- PBKDF2 password hashing;
- JWT bearer tokens;
- `/auth/me`;
- `/profiles/me`;
- owner checks for profile details, recommendations, statuses, and reminders;
- user roles are present for future admin enforcement.

## Real Data MVP

The first live source connector imports opportunities from Grants.gov:

```json
POST /ingestion/grants-gov/search
{
  "keyword": "machine learning",
  "limit": 10,
  "import_results": true
}
```

Imported opportunities are normalized into the shared `opportunities` catalog and can immediately appear in recommendations.

Opportunity lists support pagination and filters:

```text
GET /opportunities?source=daad_curated&opportunity_type=fellowship&country=Germany&career_stage=phd&keyword=AI&active_only=true&limit=20&offset=0
```

Curated sources can be imported in bulk when a provider has no stable public API:

```json
POST /opportunities/bulk-import
{
  "source": "euraxess_curated",
  "dry_run": false,
  "opportunities": [
    {
      "title": "European Research Exchange",
      "opportunity_type": "exchange",
      "source": "euraxess",
      "url": "https://example.org/exchange",
      "summary": "Exchange for data science researchers.",
      "disciplines": ["Computer Science"],
      "keywords": ["data science"],
      "countries": ["Germany"],
      "career_stages": ["phd"],
      "deadline": "2026-09-30"
    }
  ]
}
```

The importer deduplicates by URL, updates existing records, and supports `dry_run` previews.

External source imports support source-specific normalization for `euraxess`, `daad`, `daad_ukraine`, `fulbright`, `fulbright_ukraine`, `msca`, `msca4ukraine`, `nrfu`, `nauka_gov_ua`, `house_of_europe`, and `science_for_ukraine`. The importer accepts `rss`, `json`, and lightweight `html` source kinds so Ukrainian opportunity pages without stable APIs can still be discovered and reviewed.

Useful Ukrainian and Ukraine-focused source URLs to try from the admin external importer:

- `nrfu`: `https://nrfu.org.ua/en/contests-posts-en/`
- `nauka_gov_ua`: `https://nauka.gov.ua/`
- `house_of_europe`: `https://houseofeurope.org.ua/en/opportunities`
- `science_for_ukraine`: `https://scienceforukraine.eu/`
- `msca4ukraine`: `https://sareurope.eu/msca4ukraine/`
- `daad_ukraine`: `https://www.daad-ukraine.org/en/`
- `fulbright_ukraine`: `https://fulbright.org.ua/en/`

Researchers can track their workflow with:

```json
PUT /profiles/{profile_id}/opportunities/{opportunity_id}/status
{
  "status": "saved",
  "notes": "Strong topic fit"
}
```

Supported statuses: `saved`, `ignored`, `planned`, `applied`, `rejected`, `accepted`.

Saving, planning, or applying to an opportunity with a deadline automatically creates a reminder seven days before the deadline.

Manual reminders are also supported:

```json
POST /profiles/{profile_id}/reminders
{
  "opportunity_id": 1,
  "remind_on": "2026-06-01",
  "message": "Draft proposal outline"
}
```

Use `GET /profiles/{profile_id}/reminders?due_only=true` for due reminders and `PUT /profiles/{profile_id}/reminders/{reminder_id}/complete` to mark one done.

## Profile Enrichment

ORCID public record import creates or enriches a researcher profile:

```json
POST /integrations/orcid/import
{
  "orcid_id": "0000-0002-1825-0097",
  "career_stage": "phd",
  "disciplines": ["Computer Science"],
  "preferred_countries": ["Germany"]
}
```

The importer reads public ORCID record data and extracts name, country, keywords, Google Scholar URL, and LinkedIn URL when those fields are present.

Additional profile details can be stored directly:

```json
PUT /profiles/{profile_id}/details
{
  "research_summary": "I study climate adaptation and urban heat resilience.",
  "publications": ["Urban Heat Resilience in Eastern Europe"],
  "degrees": ["PhD Environmental Science"],
  "languages": ["English", "Ukrainian"],
  "funding_interests": ["climate adaptation", "urban resilience"],
  "unavailable_countries": ["United States"],
  "preferred_opportunity_types": ["grant", "fellowship"],
  "min_duration_months": 3,
  "max_duration_months": 12
}
```

Recommendations use these details for text overlap, funding-interest matches, preferred opportunity types, unavailable-country penalties, and workflow status filtering. Ignored opportunities are hidden by default and can be included with `GET /recommendations/{profile_id}?include_ignored=true`.

Recommendation lists support pagination and score filtering:

```text
GET /recommendations/{profile_id}?min_score=70&limit=20&offset=0
```

## Full Implementation Plan

### Phase 1: Backend MVP Foundation

Status: complete for the backend foundation.

- FastAPI application structure.
- Researcher profile CRUD.
- Profile detail enrichment.
- Opportunity CRUD.
- Grants.gov ingestion.
- Curated bulk opportunity import.
- ORCID public import.
- Recommendation scoring V1.
- Opportunity workflow statuses.
- Deadline reminders.
- Backend tests.

Completed foundation items:

- Alembic migration scaffold and initial schema migration.
- Stricter duplicate protection for opportunity URLs.
- Pagination and filtering for opportunities and recommendations.
- Structured request logging.
- Environment-specific settings through `.env`.
- CORS configuration for the future frontend.
- Request IDs are returned through `X-Request-ID`.
- Handled API errors use a standard `{ "error": { "code", "message", "request_id" } }` envelope.
- Admin and job queue APIs require authenticated admin users.

Known Phase 1 limitations:

- Authentication is intentionally deferred to Phase 3.
- SQLite is still the default local database until the Docker/PostgreSQL phase.
- Semantic matching is deferred until pgvector is introduced.

### Phase 2: Database and Data Quality

Goal: make the backend production-ready.

- Move from SQLite to PostgreSQL.
- Add Redis for future workers and caching.
- Add Docker Compose development stack.
- Add Alembic migration history.
- Add database indexes for deadline, source, country, career stage, and opportunity type.
- Add unique indexes for external source identifiers and URLs.
- Add source ingestion audit records.
- Track import batches, errors, and source freshness.
- Add soft-delete or archive status for expired opportunities.
- Add normalized lookup tables later if needed: countries, disciplines, opportunity types.

Current Phase 2 status:

- Dockerfile added.
- Docker Compose added for API, PostgreSQL with pgvector, and Redis.
- `.env.example` added.
- PostgreSQL driver added.
- Redis client dependency added.
- Opportunity source audit table added.
- Ingestion batch and error tables added.
- Grants.gov and bulk imports now create batch audit records.
- `/sources` and `/sources/batches` expose source freshness and import history.

### Phase 3: Authentication and User Ownership

Goal: support real users safely.

- Add `users` table.
- Add password or OAuth login.
- Add JWT session handling.
- Connect each researcher profile to a user.
- Restrict profile, status, and reminder endpoints by authenticated user.
- Add admin role for bulk imports and source management.
- Add basic rate limiting for public ingestion endpoints.

Current Phase 3 status:

- `users` table added.
- Password registration and login added.
- JWT bearer auth added.
- `researcher_profiles.user_id` ownership added.
- Authenticated profile creation attaches profiles to users.
- `/auth/me` and `/profiles/me` added.
- Owner checks added for user-specific profile workflows.
- Admin role enum and dependency added for future admin-only routes.

Remaining hardening:

- enforce admin-only access for ingestion/admin endpoints once a frontend admin flow exists;
- add OAuth providers if required;
- add password reset;
- add rate limiting;
- rotate `JWT_SECRET_KEY` through production secrets.

### Phase 4: Frontend MVP

Goal: build the first usable web application.

Pages:

- sign in / sign up;
- onboarding profile wizard;
- ORCID import screen;
- researcher profile editor;
- opportunity feed;
- opportunity detail page;
- saved/planned/applied board;
- reminders page;
- admin opportunity import page;
- API error and empty states.

Core UI workflows:

- create profile manually;
- enrich with ORCID;
- browse recommended opportunities;
- filter by type, country, deadline, source, career stage;
- save, ignore, plan, apply;
- view match reasons;
- create and complete reminders;
- admin imports curated opportunity lists.

Current Phase 4 status:

- React + TypeScript frontend scaffold added under `frontend/`.
- Sign in and sign up screens added with bearer token persistence.
- Authenticated dashboard added with profile selection.
- Profile creation, detail enrichment, and ORCID import screens added.
- Opportunity feed added with recommendation scores, reasons, filters, detail drawer, and status actions.
- Saved/planned/applied workflow board added.
- Reminder creation and completion UI added.
- Admin import UI added for Grants.gov search and curated bulk JSON imports.
- API error and empty states added.

### Phase 5: Background Jobs

Goal: remove long-running work from request/response APIs.

- Add Redis.
- Add Celery or RQ.
- Move Grants.gov ingestion into background jobs.
- Schedule recurring source syncs.
- Add reminder scan job.
- Add email notification job.
- Add failed-job retry behavior and admin visibility.

Current Phase 5 status:

- RQ dependency added for Redis-backed background jobs.
- Shared Grants.gov ingestion service extracted for API and worker use.
- `/jobs/ingestion/grants-gov` queues Grants.gov imports with retry behavior.
- `/jobs/reminders/scan` queues due reminder scans.
- Reminder email notification job stub added with logging and skip reasons.
- `/jobs`, `/jobs/{job_id}`, and `/jobs/{job_id}/retry` expose queue visibility and failed-job retry support.
- Docker Compose now runs separate `worker` and `scheduler` services.
- Scheduler queues recurring Grants.gov source syncs and reminder scans based on environment settings.
- Frontend admin screen can queue jobs, view queue stats, and inspect job details.

### Phase 6: AI and Semantic Matching

Goal: improve match quality beyond keyword overlap.

- Add profile text embedding.
- Add opportunity text embedding.
- Store vectors in PostgreSQL with pgvector.
- Combine deterministic eligibility filters with semantic similarity.
- Add explainable recommendation reasons:
  - topic fit;
  - eligibility fit;
  - country and mobility fit;
  - career stage fit;
  - deadline urgency;
  - similarity to publications and research summary.
- Add feedback loop from saved, ignored, and applied statuses.

Current Phase 6 status:

- Portable local embedding service added using deterministic text vectors.
- Profile detail embeddings and opportunity embeddings are persisted.
- Alembic migration `20260504_0004` adds embedding columns and enables PostgreSQL `vector` extension when available.
- Recommendations now blend semantic similarity with deterministic eligibility and metadata scoring.
- Recommendation responses include `semantic_score`.
- Semantic explanations are included for moderate and strong profile/opportunity similarity.
- Embedding refresh worker jobs added for profiles and opportunities.
- `/jobs/embeddings/refresh` queues a full embedding backfill.
- Frontend opportunity cards show semantic score and the admin screen can queue embedding refreshes.
- Feedback from saved, planned, applied, and ignored statuses remains part of ranking/filtering.

### Phase 7: More Integrations

Goal: broaden real opportunity coverage and profile quality.

Opportunity sources:

- Grants.gov;
- EURAXESS;
- Erasmus+;
- MSCA;
- DAAD;
- Fulbright;
- national research funders;
- university and foundation curated lists.

Profile sources:

- ORCID public API;
- OpenAlex;
- Crossref;
- Semantic Scholar where appropriate;
- LinkedIn as an optional profile link or limited OAuth integration;
- Google Scholar as a user-provided URL, not as a scraped dependency.

Current Phase 7 status:

- Generic external opportunity source importer added for RSS and JSON feeds.
- `/ingestion/external-source/import` normalizes EURAXESS/DAAD/Fulbright/Erasmus/MSCA-style feeds into the shared opportunity catalog.
- External source imports create source freshness and batch audit records.
- OpenAlex profile enrichment added through `/integrations/openalex/import`.
- OpenAlex enrichment merges public concepts, works, funding interests, and profile detail summaries without overwriting user-entered data.
- OpenAlex base URL is configurable through `OPENALEX_BASE_URL`.
- Frontend admin screen can import external RSS/JSON opportunity feeds.
- Frontend integration screen can enrich the active profile with OpenAlex by ORCID or OpenAlex author id.

### Phase 8: Notifications

Goal: make the system proactive.

- Email reminders for upcoming deadlines.
- Weekly recommendation digest.
- Alerts for new high-match opportunities.
- Notification preferences per user.
- Reminder history and unsubscribe controls.

Current Phase 8 status:

- Notification preferences table and API added.
- Notification history table and API added.
- Deadline reminder worker now records persistent notification history.
- Deadline reminder email sends respect user notification preferences.
- Email provider abstraction added with local console delivery and SMTP delivery.
- Notification history stores provider, recipient, provider message id, attempt count, and last error.
- Weekly digest and high-match alert worker jobs added.
- Scheduler can enqueue weekly digest and high-match alert jobs.
- Notification read/unread and unsubscribe controls added.
- Frontend notifications section added with preferences, history, mark-read, and unsubscribe actions.
- Weekly digest and high-match alert preferences are used by scheduled notification jobs.

### Phase 9: Admin and Operations

Goal: make data management sustainable.

- Admin dashboard for opportunity review.
- Import batch history.
- Failed ingestion diagnostics.
- Source freshness indicators.
- Manual opportunity editing.
- Duplicate merge tools.
- Basic analytics:
  - most saved opportunities;
  - most common fields;
  - source quality;
  - match score distribution.

Current Phase 9 status:

- Admin dashboard API added with source freshness, recent batches, failed batches, and analytics.
- Admin audit log table and API added.
- Manual opportunity editing API added with audit logging.
- Duplicate opportunity detection and merge APIs added.
- Merge tool reassigns statuses, reminders, and notifications before deleting duplicates.
- Basic analytics added for saved opportunities, common disciplines, source quality, and totals.
- Frontend admin operations panel added for dashboard, duplicates, analytics, and audit visibility.

### Phase 10: Application Assistant

Goal: help researchers act on opportunities.

- Generate application checklist from opportunity text.
- Draft motivation letter outline.
- Draft research fit statement.
- Suggest missing profile fields.
- Warn about eligibility gaps.
- Export application notes.

Current Phase 10 status:

- Application assistant service added.
- `/application-assistant` generates an application checklist, motivation letter outline, research fit statement, missing profile field suggestions, eligibility warnings, and exportable notes.
- Assistant uses profile details, opportunity metadata, deadlines, countries, career stage, and unavailable countries.
- Assistant now builds deterministic readiness/gap facts first, then generates an advisor memo through `ADVISOR_PROVIDER`.
- `ADVISOR_PROVIDER=deterministic` is the default and requires no network access.
- `ADVISOR_PROVIDER=groq` uses Groq when `GROQ_API_KEY` is set; `ADVISOR_PROVIDER=local` uses an OpenAI-compatible local endpoint such as Ollama or LM Studio.
- Frontend application assistant tab added.
- Exportable Markdown-style notes are displayed in the app for application prep.

## Database Plan

Current tables:

- `researcher_profiles`
- `researcher_profile_details`
- `opportunities`
- `profile_opportunity_statuses`
- `opportunity_reminders`

Planned tables:

- `users`
- `external_accounts`
- `publications`
- `opportunity_sources`
- `ingestion_batches`
- `ingestion_errors`
- `embeddings`
- `notifications`
- `admin_audit_log`

Production database requirements:

- PostgreSQL as source of truth.
- pgvector extension for embeddings.
- Alembic migrations for every schema change.
- Seed scripts for initial opportunity sources.
- Backup strategy before production use.

## Frontend Plan

The frontend should feel like a focused researcher dashboard, not a marketing landing page.

Main areas:

- left navigation with Feed, Saved, Applied, Reminders, Profile, Admin;
- compact opportunity cards with match score and deadline;
- detail panel with reasons, eligibility, source URL, and actions;
- profile completeness indicator;
- admin import workflow with dry-run preview.

Important frontend states:

- loading recommendations;
- no profile yet;
- no matches yet;
- source ingestion running;
- deadline overdue;
- opportunity already applied;
- import validation errors.

## API Stabilization Checklist

- Add pagination to list endpoints.
- Add filtering to opportunities and recommendations.
- Add consistent error response format.
- Add request IDs.
- Add CORS configuration for frontend.
- Add API version prefix, for example `/api/v1`.
- Add OpenAPI tags and descriptions.
- Add integration tests for common frontend flows.

## Definition of MVP Complete

The MVP is complete when a researcher can:

1. Create an account.
2. Build or import an academic profile.
3. Receive real recommendations from at least two opportunity data sources.
4. Understand why each opportunity is recommended.
5. Save, ignore, plan, and mark applications.
6. Receive deadline reminders.
7. Use a frontend dashboard without touching Swagger.
8. Admin-import curated opportunities.
9. Run the system locally with Docker Compose.
10. Deploy the system to a hosted environment.

## Near-Term Next Steps

Recommended development order:

1. Add PostgreSQL and Redis Docker Compose setup.
2. Add API versioning.
3. Start the React or Next.js frontend.
4. Build the opportunity feed UI.
5. Add worker-based ingestion.
6. Add pgvector semantic matching.
