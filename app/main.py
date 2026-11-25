import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.tools import validate_registry
from api.router import api_router
from core.config import get_settings
from core.exceptions import DomainError
from core.logging import configure_logging
from db.init_db import init_db
from db.session import SessionLocal
from services.notifications import NotificationScheduler
from services.query_engine import build_query_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    validate_registry()
    app.state.query_engine = build_query_engine()
    app.state.query_engine.self_check()
    scheduler = NotificationScheduler(SessionLocal, settings.notification_poll_seconds)
    scheduler.start()
    logger.info("%s backend is ready", settings.app_name)
    yield
    await scheduler.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    application.include_router(api_router, prefix=settings.api_prefix)
    return application


api = create_app()
