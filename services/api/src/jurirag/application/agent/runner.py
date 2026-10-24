"""Exécution d'un run : diffusion des événements, persistance, validation humaine.

Le runner fait le lien entre le graphe (couche application) et l'API : il ouvre le run,
relaie chaque événement de trace dès qu'il est émis, enregistre les métriques et gère les
interruptions humaines (expiration comprise).
"""

import time
import uuid
from collections.abc import AsyncIterator
from typing import Any, cast

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from jurirag.application.agent.state import AgentState
from jurirag.application.ports import RunStore
from jurirag.domain.trace import RunMetrics, TraceEvent

APPROVAL_DECISIONS = ("approve", "reject")


class AgentRunner:
    def __init__(
        self,
        graphs: dict[str, Any],  # mode → graphe compilé (même checkpointer)
        checkpointer: BaseCheckpointSaver[Any],
        store: RunStore,
        model: str,
        hitl_timeout_s: float,
    ) -> None:
        self._graphs = graphs
        self._checkpointer = checkpointer
        self._store = store
        self._model = model
        self._hitl_timeout_s = hitl_timeout_s

    @property
    def modes(self) -> list[str]:
        return list(self._graphs)

    @staticmethod
    def _config(session_id: str) -> dict[str, Any]:
        # thread_id = session : la mémoire est isolée par session (pas de contamination).
        return {"configurable": {"thread_id": session_id}}

    async def snapshot(self, session_id: str) -> dict[str, Any]:
        graph = next(iter(self._graphs.values()))
        state = await graph.aget_state(self._config(session_id))
        values = cast(AgentState, state.values or {})
        interrupts = [i.value for i in getattr(state, "interrupts", ()) or ()]
        return {"values": values, "pending": interrupts[0] if interrupts else None}

    async def run(
        self,
        session_id: str,
        question: str,
        mode: str = "single",
        selected_case_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        graph = self._graphs[mode]
        current = await self.snapshot(session_id)
        if current["pending"] is not None:
            # Une validation restée sans réponse est close avant toute nouvelle question.
            async for item in self.resume(session_id, "timeout", forced=True):
                yield item

        run_id = uuid.uuid4().hex[:12]
        self._store.start_run(run_id, session_id, question, mode, self._model)
        yield {"type": "run", "run_id": run_id, "status": "started", "mode": mode}
        inputs: AgentState = {
            "run_id": run_id,
            "question": question,
            "mode": mode,
            "selected_case_id": selected_case_id,
        }
        async for item in self._stream(graph, inputs, session_id, run_id):
            yield item

    async def resume(
        self, session_id: str, decision: str, forced: bool = False
    ) -> AsyncIterator[dict[str, Any]]:
        current = await self.snapshot(session_id)
        pending = current["pending"]
        if pending is None:
            yield {"type": "status", "status": "no_pending_approval"}
            return
        values = current["values"]
        run_id = values.get("run_id", "?")
        mode = values.get("mode", "single")
        requested = float(pending.get("requested_at") or time.time())
        if forced or time.time() - requested > self._hitl_timeout_s:
            decision = "timeout"  # absence de réponse dans le délai : l'action est annulée
        elif decision not in APPROVAL_DECISIONS:
            decision = "reject"
        yield {"type": "run", "run_id": run_id, "status": "resumed", "decision": decision}
        async for item in self._stream(
            self._graphs[mode], Command(resume=decision), session_id, run_id
        ):
            yield item

    async def _stream(
        self, graph: Any, inputs: Any, session_id: str, run_id: str
    ) -> AsyncIterator[dict[str, Any]]:
        async for chunk in graph.astream(inputs, self._config(session_id), stream_mode="custom"):
            if isinstance(chunk, dict) and "trace" in chunk:
                event = TraceEvent.model_validate(chunk["trace"])
                self._store.save_event(event)
                yield {"type": "event", "event": event.model_dump(mode="json")}

        current = await self.snapshot(session_id)
        values = current["values"]
        metrics = RunMetrics.model_validate(values.get("metrics") or {})
        if current["pending"] is not None:
            yield {
                "type": "status",
                "status": "awaiting_approval",
                "run_id": run_id,
                "approval": current["pending"],
                "timeout_s": self._hitl_timeout_s,
                "metrics": metrics.model_dump(mode="json"),
            }
            return
        final = values.get("final") or {}
        self._store.finish_run(run_id, metrics, final.get("answer"))
        yield {
            "type": "status",
            "status": "done",
            "run_id": run_id,
            "final": final,
            "metrics": metrics.model_dump(mode="json"),
            "memory": {
                "case_id": values.get("session_case_id"),
                "turns": values.get("memory") or [],
            },
        }

    async def reset(self, session_id: str) -> None:
        """Réinitialise la session : mémoire et état du dernier run sont effacés."""
        await self._checkpointer.adelete_thread(session_id)
