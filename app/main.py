from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.api.errors import install_error_handlers
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.request_id import install_request_id_middleware
from app.db.session import Base, engine
from app.services.realtime_notifications import start_redis_notification_listener, stop_redis_notification_listener


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()
    logger.info(
        "starting application env=%s debug=%s database=%s redis=%s elasticsearch_enabled=%s websocket_redis_enabled=%s",
        settings.app_env,
        settings.debug,
        settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url,
        settings.redis_url,
        settings.elasticsearch_enabled,
        settings.websocket_redis_enabled,
    )
    if settings.auto_create_tables:
        logger.info("auto creating database tables")
        try:
            Base.metadata.create_all(bind=engine)
        except SQLAlchemyError:
            if settings.app_env.lower() in {"local", "test"}:
                logger.exception("auto table creation failed in local/test mode; continuing startup")
            else:
                raise

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        start_redis_notification_listener(application)
        try:
            yield
        finally:
            stop_redis_notification_listener(application)

    application = FastAPI(
        title=f"{settings.app_name} API",
        version="0.1.0",
        description="MVP backend for personalized academic grants and exchange recommendations.",
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_request_id_middleware(application)
    install_error_handlers(application)
    application.include_router(api_router)

    @application.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok", "environment": settings.app_env}

    return application


app = create_app()
