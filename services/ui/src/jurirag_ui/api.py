"""Client HTTP de l'API. L'interface ne parle jamais à Ollama."""

import json
import os
from collections.abc import Iterator
from typing import Any

import httpx

API_URL = os.environ.get("JURIRAG_API_URL", "http://127.0.0.1:8000")
# Un run d'agent peut durer plusieurs minutes sur un modèle local : délai de lecture large.
TIMEOUT = httpx.Timeout(10.0, read=600.0)


class ApiError(Exception):
    """Erreur renvoyée par l'API, avec un message lisible."""


def _detail(response: httpx.Response) -> str:
    try:
        return str(response.json().get("detail", response.text))
    except ValueError:
        return response.text


def _call(method: str, path: str, **kwargs: Any) -> Any:
    try:
        response = httpx.request(method, API_URL + path, timeout=TIMEOUT, **kwargs)
    except httpx.TransportError as exc:
        raise ApiError(f"API injoignable sur {API_URL} — lancer `make api`.") from exc
    if response.is_error:
        raise ApiError(f"{response.status_code} — {_detail(response)}")
    return response.json()


def health() -> dict[str, Any]:
    return _call("GET", "/health")


def search(q: str, k: int, method: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {"q": q, "k": k}
    if method:
        params["method"] = method
    return _call("GET", "/api/v1/cases/search", params=params)


def get_case(case_id: str) -> dict[str, Any]:
    return _call("GET", f"/api/v1/cases/{case_id}")


def summarize(case_id: str) -> dict[str, Any]:
    return _call("POST", f"/api/v1/cases/{case_id}/summary")


def ask_static(question: str, case_id: str | None, k: int = 5) -> dict[str, Any]:
    return _call("POST", "/api/v1/rag/ask", json={"question": question, "case_id": case_id, "k": k})


def session(session_id: str) -> dict[str, Any]:
    return _call("GET", f"/api/v1/sessions/{session_id}")


def reset_session(session_id: str) -> dict[str, Any]:
    return _call("DELETE", f"/api/v1/sessions/{session_id}")


def runs(limit: int = 200) -> list[dict[str, Any]]:
    return _call("GET", "/api/v1/runs", params={"limit": limit})


def run(run_id: str) -> dict[str, Any]:
    return _call("GET", f"/api/v1/runs/{run_id}")


def metrics() -> dict[str, Any]:
    return _call("GET", "/api/v1/metrics")


def request_export(run_id: str) -> dict[str, Any]:
    return _call("POST", f"/api/v1/runs/{run_id}/export", json={})


def decide(approval_id: str, decision: str) -> dict[str, Any]:
    return _call("POST", f"/api/v1/approvals/{approval_id}", json={"decision": decision})


def _stream(path: str, payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Lit le flux NDJSON ligne par ligne : chaque événement arrive dès qu'il est émis."""
    try:
        with httpx.stream("POST", API_URL + path, json=payload, timeout=TIMEOUT) as response:
            if response.is_error:
                response.read()
                raise ApiError(f"{response.status_code} — {_detail(response)}")
            # Découpage sur « \n » uniquement (et non iter_lines, qui coupe aussi sur
            # U+2028/U+2029) : une ligne NDJSON = un événement complet.
            buffer = b""
            for chunk in response.iter_bytes():
                buffer += chunk
                *lines, buffer = buffer.split(b"\n")
                for line in lines:
                    if line.strip():
                        yield json.loads(line)
            if buffer.strip():
                yield json.loads(buffer)
    except httpx.TransportError as exc:
        raise ApiError(f"API injoignable ou flux interrompu ({exc}).") from exc


def run_agent(
    session_id: str, question: str, mode: str, case_id: str | None
) -> Iterator[dict[str, Any]]:
    return _stream(
        "/api/v1/runs",
        {"session_id": session_id, "question": question, "mode": mode, "case_id": case_id},
    )


def resume(session_id: str, decision: str) -> Iterator[dict[str, Any]]:
    return _stream(f"/api/v1/sessions/{session_id}/resume", {"decision": decision})
