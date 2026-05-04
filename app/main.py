import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.api import admin, application_assistant, auth, ingestion, jobs, notifications, openalex, opportunities, orcid, profiles, recommendations, reminders, sources, statuses
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import Base, engine


configure_logging()
logger = logging.getLogger(__name__)

if settings.auto_create_tables:
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=f"{settings.app_name} API",
    version="0.1.0",
    description="MVP backend for personalized academic grants and exchange recommendations.",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(opportunities.router)
app.include_router(recommendations.router)
app.include_router(notifications.router)
app.include_router(admin.router)
app.include_router(application_assistant.router)
app.include_router(ingestion.router)
app.include_router(jobs.router)
app.include_router(statuses.router)
app.include_router(orcid.router)
app.include_router(openalex.router)
app.include_router(reminders.router)
app.include_router(sources.router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
