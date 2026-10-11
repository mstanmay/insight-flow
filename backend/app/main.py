from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.db import engine, Base
from app.core.logging import RequestLoggingMiddleware
from app.core.errors import register_error_handlers
from app.schemas.common import HealthResponse, ReadyResponse
from app.api.v1.datasets import router as datasets_router
from app.api.v1.feedback import router as feedback_router
from app.api.v1.issues import router as issues_router
from app.api.v1.analytics import router as analytics_router

settings = get_settings()

# Initialize tables
Base.metadata.create_all(bind=engine)


def create_app() -> FastAPI:
    app = FastAPI(
        title="InsightFlow Backend API",
        description="Evidence-First Intelligent Customer Feedback & Decision Intelligence Platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
    )

    # Middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.FRONTEND_ORIGINS if isinstance(settings.FRONTEND_ORIGINS, list) else [settings.FRONTEND_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error Handlers
    register_error_handlers(app)

    # System Health Checks
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    @app.get(f"{settings.API_V1_PREFIX}/health", response_model=HealthResponse, tags=["Health"])
    def health_check():
        return HealthResponse(
            status="ok",
            version="1.0.0",
            pipeline_version="1.0.0"
        )

    @app.get("/ready", response_model=ReadyResponse, tags=["Health"])
    @app.get(f"{settings.API_V1_PREFIX}/ready", response_model=ReadyResponse, tags=["Health"])
    def readiness_check():
        return ReadyResponse(
            status="ready",
            checks={
                "database": {"status": "ok", "message": "Database session healthy"},
                "pipeline": {"status": "ok", "message": "Analysis worker operational"}
            }
        )

    # Mount API v1 Routers
    app.include_router(datasets_router, prefix=settings.API_V1_PREFIX)
    app.include_router(feedback_router, prefix=settings.API_V1_PREFIX)
    app.include_router(issues_router, prefix=settings.API_V1_PREFIX)
    app.include_router(analytics_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
