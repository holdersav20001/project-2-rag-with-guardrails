"""FastAPI application factory."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from rag_guardrails.core.logging import configure_logging

limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="RAG with Guardrails",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS — restrict in production via environment
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    from rag_guardrails.api.routes.health import router as health_router
    from rag_guardrails.api.routes.documents import router as documents_router
    from rag_guardrails.api.routes.query import router as query_router
    from rag_guardrails.api.routes.evaluations import router as evaluations_router

    app.include_router(health_router, prefix="/api")
    app.include_router(documents_router, prefix="/api")
    app.include_router(query_router, prefix="/api")
    app.include_router(evaluations_router, prefix="/api")

    return app


app = create_app()
