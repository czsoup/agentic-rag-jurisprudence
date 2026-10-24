"""Valeurs échangées avec un modèle de langage, indépendantes du serveur utilisé."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    """Appel d'outil *proposé* par le modèle. Rien n'est exécuté tant que le code ne l'a pas validé."""

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_name: str | None = None  # pour role="tool" : outil dont c'est le résultat


class ToolSpec(BaseModel):
    """Description d'un outil exposée au modèle (schéma JSON)."""

    name: str
    description: str
    parameters: dict[str, Any]


class GenerationParams(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: str
    temperature: float = Field(ge=0.0, le=2.0)
    seed: int
    top_p: float
    num_predict: int
    num_ctx: int
    # Qwen3/3.5 raisonnent avant de répondre par défaut ; on le désactive explicitement
    # là où une décision courte suffit (latence). Le raisonnement n'est jamais affiché.
    think: bool = False


class LLMResponse(BaseModel):
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    latency_ms: float
    model: str
    # Comptes réellement renvoyés par le serveur (None s'il ne les fournit pas).
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
