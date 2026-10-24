"""Configuration centralisée, surchargeable par variables d'environnement ou `.env`.

Les chemins sont relatifs à la racine du projet, d'où toutes les commandes du Makefile
sont lancées.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from jurirag.domain.llm import GenerationParams
from jurirag.domain.models import RetrievalMethod


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Ollama (serveur LLM local) ---
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:9b"  # génération (agent, rédaction, juge)
    ollama_embed_model: str = "qwen3-embedding:0.6b"  # embeddings : modèle distinct
    request_timeout_s: float = 180.0
    # Ollama décharge un modèle inactif après 5 min ; on le garde chargé pendant une session.
    ollama_keep_alive: str = "30m"

    # --- Génération ---
    temperature: float = Field(0.1, ge=0.0, le=2.0)  # factuel
    judge_temperature: float = Field(0.0, ge=0.0, le=2.0)  # juge : sortie JSON reproductible
    seed: int = 42
    top_p: float = 0.9
    num_predict: int = 1024
    num_ctx: int = 16384  # passages + historique d'outils d'un run
    think: bool = False  # rédaction statique, résumé, juge : sorties contraintes, sans raisonnement
    # Décisions de l'agent (choix d'outil) : raisonnement activé. Banc d'essai DEC-016 :
    # 12/12 décisions correctes avec, 9/12 sans (la lecture de l'affaire était omise).
    think_decide: bool = True

    # --- Agent ---
    agent_max_iterations: int = Field(5, ge=1, le=20)  # budget de la boucle
    hitl_timeout_s: float = 300.0  # sans réponse humaine : l'action est annulée
    memory_ttl_s: float = 7200.0  # durée de vie d'une session de mémoire

    # --- Retrieval ---
    retrieval_k: int = Field(5, ge=1, le=50)
    retrieval_method: RetrievalMethod = RetrievalMethod.HYBRID
    retrieval_candidates: int = 50  # profondeur de chaque liste avant fusion RRF
    rrf_k: int = 60  # Cormack et al. 2009
    max_passages_per_read: int = 8  # read_case : passages renvoyés au maximum

    # --- Corpus & index ---
    dataset_repo: str = "antoinejeannot/jurisprudence"
    dataset_revision: str = "8019db1080cf6dc8a34d73ee44d704a8e90b558e"  # v2025.03.20
    dataset_split: str = "cour_de_cassation"
    data_dir: Path = Path("data")
    index_name: str = "main"  # plusieurs index peuvent coexister (ex. « dev » pour évaluer)
    chunk_tokens: int = 450  # 300–800 tokens comme point de départ usuel
    chunk_overlap: float = 0.15  # 10–20 %

    # --- API ---
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index" / self.index_name

    @property
    def db_path(self) -> Path:
        """Runs, événements de trace et mémoire de session (SQLite)."""
        return self.data_dir / "app.db"

    def generation_params(
        self,
        temperature: float | None = None,
        think: bool | None = None,
        num_predict: int | None = None,
        model: str | None = None,
    ) -> GenerationParams:
        return GenerationParams(
            model=model or self.ollama_model,
            temperature=self.temperature if temperature is None else temperature,
            seed=self.seed,
            top_p=self.top_p,
            num_predict=self.num_predict if num_predict is None else num_predict,
            num_ctx=self.num_ctx,
            think=self.think if think is None else think,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
