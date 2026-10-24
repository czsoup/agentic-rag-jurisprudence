"""Application FastAPI (service API)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from jurirag.config import Settings, get_settings
from jurirag.domain.errors import (
    CaseNotFoundError,
    IndexNotReadyError,
    LLMError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from jurirag.interfaces.http.container import build_container
from jurirag.interfaces.http.routers import agent, cases, system
from jurirag.logging_config import configure_logging


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(settings.log_level)
        async with build_container(settings) as container:
            app.state.container = container
            yield

    app = FastAPI(title="JuriRAG — Agentic RAG jurisprudence", version="0.1.0", lifespan=lifespan)
    app.include_router(system.router)
    app.include_router(cases.router)
    app.include_router(agent.router)

    @app.exception_handler(LLMError)
    async def llm_error(_: Request, exc: LLMError) -> JSONResponse:
        if isinstance(exc, LLMUnavailableError):
            return _error(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
        if isinstance(exc, LLMTimeoutError):
            return _error(status.HTTP_504_GATEWAY_TIMEOUT, str(exc))
        return _error(status.HTTP_502_BAD_GATEWAY, str(exc))

    @app.exception_handler(CaseNotFoundError)
    async def case_not_found(_: Request, exc: CaseNotFoundError) -> JSONResponse:
        return _error(status.HTTP_404_NOT_FOUND, f"Décision inconnue : {exc}")

    @app.exception_handler(IndexNotReadyError)
    async def index_not_ready(_: Request, exc: IndexNotReadyError) -> JSONResponse:
        return _error(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))

    return app


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "jurirag.interfaces.http.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
    )
