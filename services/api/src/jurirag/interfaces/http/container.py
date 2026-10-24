"""Assemblage des dépendances de l'API (une instance par processus)."""

import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import httpx
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from jurirag.application.agent.graph import AgentConfig, AgentGraph
from jurirag.application.agent.multi import MultiAgentGraph
from jurirag.application.agent.runner import AgentRunner
from jurirag.application.agent.tools import CaseTools, ToolExecutor
from jurirag.application.rag import StaticRAG
from jurirag.bootstrap import IndexBundle, load_index, make_llm
from jurirag.config import Settings
from jurirag.domain.errors import IndexNotReadyError
from jurirag.infrastructure.ollama import OllamaClient
from jurirag.infrastructure.run_store import SqliteRunStore

logger = logging.getLogger(__name__)


@dataclass
class Container:
    settings: Settings
    http: httpx.AsyncClient
    llm: OllamaClient
    runs: SqliteRunStore
    index: IndexBundle | None = None
    index_error: str | None = None
    runner: AgentRunner | None = None
    rag: StaticRAG | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@asynccontextmanager
async def build_container(settings: Settings) -> AsyncIterator[Container]:
    async with AsyncExitStack() as stack:
        http = await stack.enter_async_context(
            httpx.AsyncClient(timeout=settings.request_timeout_s)
        )
        container = Container(
            settings=settings,
            http=http,
            llm=make_llm(settings, http),
            runs=SqliteRunStore(settings.db_path),
        )
        try:
            container.index = load_index(settings, http)
        except IndexNotReadyError as exc:
            # L'API démarre quand même : /health explique quoi faire.
            container.index_error = str(exc)
            logger.warning("%s", exc)

        if container.index is not None:
            saver = await stack.enter_async_context(
                AsyncSqliteSaver.from_conn_string(str(settings.data_dir / "checkpoints.db"))
            )
            params = settings.generation_params()
            decide = settings.generation_params(think=settings.think_decide)
            judge = settings.generation_params(temperature=settings.judge_temperature)
            config = AgentConfig(
                params=decide,
                judge_params=judge,
                write_params=params,
                max_iterations=settings.agent_max_iterations,
                memory_ttl_s=settings.memory_ttl_s,
            )
            executor = ToolExecutor(
                CaseTools(
                    container.index.retriever, container.index.store, settings.max_passages_per_read
                )
            )
            graphs = {
                "single": AgentGraph(container.llm, executor, container.index.store, config)
                .builder()
                .compile(checkpointer=saver),
                "multi": MultiAgentGraph(container.llm, executor, container.index.store, config)
                .builder()
                .compile(checkpointer=saver),
            }
            container.runner = AgentRunner(
                graphs, saver, container.runs, settings.ollama_model, settings.hitl_timeout_s
            )
            container.rag = StaticRAG(
                container.llm, container.index.retriever, container.index.store, params, judge
            )
        yield container
