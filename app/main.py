import logging
import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

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
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%s request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
    )
    return response


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _error_response(request: Request, status_code: int, code: str, message: str, headers: dict[str, str] | None = None) -> JSONResponse:
    request_id = _request_id(request)
    response = JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
        headers=headers,
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: HTTPException | StarletteHTTPException) -> JSONResponse:
    status_code = exc.status_code
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    code = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        503: "service_unavailable",
    }.get(status_code, "http_error")
    return _error_response(request, status_code, code, detail, getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    parts = []
    for error in exc.errors():
        location = ".".join(str(item) for item in error.get("loc", [])[1:])
        message = error.get("msg", "Invalid value")
        parts.append(f"{location}: {message}" if location else message)
    return _error_response(request, 422, "validation_error", "; ".join(parts) or "Validation failed")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled exception request_id=%s", _request_id(request))
    return _error_response(request, 500, "internal_error", "Internal server error")

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
