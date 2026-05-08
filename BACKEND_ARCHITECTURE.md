# Backend Architecture

The backend follows a pragmatic Clean Architecture layout. The goal is to keep
business concepts independent from FastAPI, SQLAlchemy, Redis/RQ, and external
providers while preserving the MVP API contracts.

## Layers

```text
app/domain/
  Framework-independent enums, entities, and domain exceptions.

app/application/
  Use cases and ports. This layer orchestrates flows such as recommendations
  and ingestion without knowing FastAPI router details.

app/infrastructure/
  Adapters for persistence and external systems. SQLAlchemy repositories and
  provider-specific clients live here or under app/integrations.

app/api/
  FastAPI routers, request/response schemas, dependency wiring, and HTTP error
  translation.

app/modules/
  SQLAlchemy ORM model definitions grouped by domain area. These are
  infrastructure persistence models, not domain entities.
```

## Recommendation Flow

Recommendations are executed through `ListRecommendationsUseCase`.

1. The API receives filters and builds a `RecommendationQuery`.
2. The use case validates profile access.
3. Candidate opportunities are selected through a strategy:
   - PostgreSQL uses pgvector distance when vector columns are available.
   - SQLite/local development falls back to all opportunities.
4. `recommendation_engine.score_opportunity` calculates the weighted score:
   - semantic similarity;
   - eligibility fit;
   - deadline urgency;
   - user history signals.
5. Gap analysis adds readiness score, strengths, and missing requirements.

The scoring formula is intentionally isolated from API and persistence concerns
so weights, explanations, and semantic matching can evolve independently.

## Ingestion Flow

Ingestion uses strategy-style use cases:

- `GrantsGovStrategy` for Grants.gov API ingestion.
- `ExternalFeedStrategy` for generic RSS/JSON feeds and source-specific
  connector normalization.

Adding a new source should require a new strategy/client/mapper, not changes to
API routing or shared import logic.

## Error Handling

Application and domain layers raise `AppError` subclasses from
`app.domain.exceptions`. FastAPI translates these into standard error envelopes
with request IDs in `app.api.errors`.

## Transaction Boundary

Existing endpoint services still use explicit `commit()` calls for backwards
compatibility. New multi-step use cases should prefer `SqlAlchemyUnitOfWork`
from `app.db.unit_of_work` so commits and rollbacks stay centralized.
