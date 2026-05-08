from fastapi import APIRouter

from app.api import (
    admin,
    application_assistant,
    auth,
    ingestion,
    jobs,
    notifications,
    openalex,
    opportunities,
    orcid,
    profiles,
    recommendations,
    reminders,
    sources,
    statuses,
)


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(profiles.router)
api_router.include_router(opportunities.router)
api_router.include_router(recommendations.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
api_router.include_router(application_assistant.router)
api_router.include_router(ingestion.router)
api_router.include_router(jobs.router)
api_router.include_router(statuses.router)
api_router.include_router(orcid.router)
api_router.include_router(openalex.router)
api_router.include_router(reminders.router)
api_router.include_router(sources.router)
