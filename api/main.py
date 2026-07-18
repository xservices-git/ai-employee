"""FastAPI application entry point."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import approvals, health, tasks
from core import __version__
from core.common.config import get_settings
from core.common.errors import AIEmployeeError
from core.common.logging import get_logger, setup_logging

# Setup logging first
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup + shutdown."""
    settings = get_settings()
    logger.info("api.starting", version=__version__, env=settings.app_env)
    yield
    logger.info("api.shutting_down")


def create_app() -> FastAPI:
    """Create and configure FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title="AI Employee V3.0 API",
        version=__version__,
        description="Local multi-agent AI system API",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_dev else ["https://your-domain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health.router)
    app.include_router(tasks.router)
    app.include_router(approvals.router)

    # Global exception handler
    @app.exception_handler(AIEmployeeError)
    async def ai_employee_error_handler(request, exc: AIEmployeeError):
        logger.error("api.error", code=exc.code, message=exc.message)
        return JSONResponse(
            status_code=400,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.get("/")
    async def root():
        return {
            "name": "ai-employee",
            "version": __version__,
            "env": settings.app_env,
            "docs": "/docs",
        }

    return app


app = create_app()


def main() -> None:
    """Run the API server."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_dev,
        workers=settings.api_workers if not settings.is_dev else 1,
    )


if __name__ == "__main__":
    sys.exit(main())
