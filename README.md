# JuriRAG — Agentic RAG sur la jurisprudence

Assistant de recherche en jurisprudence de la Cour de cassation, en local. L'agent **décide** quand chercher dans le corpus et quelle décision lire. Sa réponse est soumise à un **vérificateur de preuves** avant d'être rendue, avec ses citations. Toute l'exécution est **visible en direct**.

Corpus : [`antoinejeannot/jurisprudence`](https://huggingface.co/datasets/antoinejeannot/jurisprudence), licence Etalab 2.0. Modèles : Ollama, aucun appel externe.

```
UI Streamlit ──HTTP / NDJSON──▶ API FastAPI ──▶ Ollama (natif, GPU)
  recherche, lecture,            agent LangGraph,     qwen3.5:9b          (décision, rédaction, juge)
  trace en direct,               outils, vérificateur, qwen3-embedding:0.6b (embeddings)
  validation humaine             index hybride, SQLite
                     ▲
       jurirag-build (job hors ligne) : corpus → passages → BM25 + embeddings
```

Rapport : [`report/rapport.pdf`](report/rapport.pdf) · décisions : [`docs/DECISIONS.md`](docs/DECISIONS.md) · schémas : [`docs/diagrams/`](docs/diagrams/) · traces des scénarios : [`docs/traces/`](docs/traces/).

## Fonctionnalités

| Fonctionnalité | Où |
|---|---|
| Recherche par mots-clés ou en langage naturel : hybride BM25 + dense (RRF), BM25 seul ou dense seul | page *Recherche & lecture* · `GET /api/v1/cases/search` |
| Lecture d'une décision par zone (exposé, moyens, motivations, dispositif), avec ses métadonnées et sa provenance | idem · `GET /api/v1/cases/{id}` |
| Résumé faits / procédure / décision, chaque phrase citée | onglet *Résumé* · `POST /api/v1/cases/{id}/summary` |
| Question-réponse sur l'affaire (RAG statique, point de comparaison de l'agent), avec les passages affichés | onglet *Questions* · `POST /api/v1/rag/ask` |
| **Agentic RAG** : l'agent choisit `search_cases` ou `read_case`, ou bien répond ; la réponse passe par le vérificateur, qui la relance ou l'arrête | page *Agent* · `POST /api/v1/runs` |
| Trace DECISION / TOOL / OBSERVATION / CHECK / FINAL (+ ERROR, HUMAN), en direct | page *Agent* |
| **Vue conversation** : questions successives en bulles, mémoire de session affichée dans chaque question, graphe de la boucle avec le nœud en cours surligné, récapitulatif du parcours sous chaque réponse (« chercher → lire → vérifier ✗ → vérifier ✓ ») | page *Agent* |
| **Extensions** : mémoire de session, multi-agents, validation humaine, observabilité | voir ci-dessous |

### Outils de l'agent

- `search_cases(query, k)` : interroge l'index réel et regroupe les résultats par décision. Renvoie les métadonnées et le meilleur passage de chaque décision, avec un alias citable `[Pn]`.
- `read_case(case_id, focus?)` : lit une décision (exposé, motivations, dispositif) ou les passages qui traitent d'un point précis.

Le modèle *propose* un appel ; le code vérifie que l'outil est autorisé, valide les arguments avec pydantic, puis l'exécute. Une erreur est renvoyée au modèle sans rien exécuter.

### Vérificateur

1. **Règles** :
   - R1 : chaque affirmation est citée ;
   - R2 : la citation désigne un passage réellement montré pendant le run ;
   - R3 : les dates, articles et montants figurent dans le passage cité.
2. **LLM juge**, à température 0 et en JSON contraint : pour chaque affirmation, `supports`, `contradicts` ou `not_enough_info`, et la réponse traite-t-elle la question ?
3. **Statut** :
   - `sufficient` : la réponse est rendue ;
   - `insufficient` : l'agent relance avec le retour du vérificateur, puis s'abstient ou rend une réponse partielle limitée aux affirmations vérifiées ;
   - `contradictory` : une validation humaine est demandée.

Un juge en panne ou une sortie invalide ne valident jamais rien.

### Extensions

| Extension | Mise en œuvre |
|---|---|
| Mémoire | Checkpointer SQLite par session : affaire en cours et 3 derniers échanges. Expire après 2 h, est purgée au changement d'affaire, réinitialisable. Distincte de l'index. |
| Multi-agents | Mode `multi` : superviseur (LLM + garde-fous), chercheur (outils, contexte isolé) et vérificateur. Dossier de preuves partagé. |
| Human-in-the-loop | Le run est **suspendu** pour prolonger le budget d'itérations ou diffuser une réponse contredite. L'export du dossier attend aussi une confirmation. Délai de 5 min ; sans réponse, l'action est annulée. |
| Observabilité | Appels LLM, tokens, appels par outil, recherches, itérations, latences totale et par étape, statut, erreurs. Page *Observabilité* et `GET /api/v1/metrics`. Coût : non applicable (modèle local). |

## Prérequis

- [uv](https://docs.astral.sh/uv/) 
- [Ollama](https://ollama.com/) ≥ 0.30
- Environ 12 Go de disque : modèles 7,3 Go, parquet 1,7 Go, index.

## Installation et lancement

Toutes les commandes se lancent depuis la racine du dépôt.

```bash
make install        # uv sync : dépendances verrouillées (uv.lock)
make models         # ollama pull qwen3.5:9b && ollama pull qwen3-embedding:0.6b
make index          # télécharge le corpus (révision figée) et construit l'index (~1 h, voir ci-dessous)
make api            # terminal 1 : API → http://127.0.0.1:8000/docs
make ui             # terminal 2 : interface → http://localhost:8501
```

La configuration par défaut fonctionne telle quelle. Pour la modifier, copier `.env.example` en `.env` (`OLLAMA_MODEL`, `AGENT_MAX_ITERATIONS`, `RETRIEVAL_METHOD`, etc.). Aucune clé ni aucun secret n'est nécessaire.

### Corpus et index

- `make index` sélectionne **4 000 décisions** de la Cour de cassation (2022 à 2024, 6 chambres, dont 50 % publiées au Bulletin ; graine 42) et les découpe en environ 27 000 passages.
- Débit d'embedding mesuré sur M5 : environ 8,5 passages/s, d'où à peu près 55 minutes.
- Pour essayer vite : `make index-dev` (300 décisions, environ 5 min), puis `INDEX_NAME=dev-small make api`.
- Pour changer de périmètre : `uv run jurirag-build --n 8000 --year-from 2020 --year-to 2024 --index-name autre`.
- La provenance (révision du dataset, filtres, rejets, durées) est écrite dans `data/index/<nom>/manifest.json`.
- Le dossier `data/` n'est pas versionné : il se reconstruit à l'identique.

### Vérifier l'installation

`GET /health` (ou la page *Système*) indique si Ollama répond, si les modèles sont installés et si l'index existe. En cas de problème, il donne la commande à lancer.

## Tests

```bash
make test           # 81 tests, sans Ollama : outils, vérificateur, boucle, mémoire, HITL, API, graphe de l'UI (LLM scripté)
make test-ollama    # intégration avec le vrai modèle et l'index (Ollama démarré)
make lint           # ruff + mypy --strict
make eval           # évaluation du retrieval (Hit@k, MRR) : BM25 / dense / hybride
make scenarios      # rejoue les 3 scénarios de test et enregistre leurs traces (API démarrée)
```

## Exemples

```bash
# Recherche
curl "http://127.0.0.1:8000/api/v1/cases/search?q=abandon%20de%20poste%20faute%20grave&k=5"

# Run d'agent diffusé en direct (une ligne JSON par événement)
curl -N -X POST http://127.0.0.1:8000/api/v1/runs -H 'content-type: application/json' \
  -d '{"session_id":"demo01","question":"Un abandon de poste peut-il justifier un licenciement pour faute grave ?","mode":"single"}'
```

## Limites connues

- **Sous-corpus** : 4 000 décisions sur 1 058 823. Une question hors de ce périmètre conduit à une abstention, ce qui est voulu, mais pas à une réponse.
- **Modèle de 9B** : la qualité de rédaction et la fiabilité du tool calling sont celles d'un petit modèle local (voir le rapport). Un run prend de quelques dizaines de secondes à quelques minutes.
- **Juge** : le même modèle rédige et juge. Les règles déterministes passent en premier, mais un juge complaisant reste possible.
- **Pas d'API externe** (choix assumé) : la validation humaine porte sur des actions internes sensibles.
- **Évaluation du retrieval** : elle repose sur des pseudo-requêtes construites à partir des sommaires, faute de jeu annoté. Les biais sont décrits dans le rapport.
- **Réponses** : elles sont produites par un modèle à partir d'extraits et ne constituent pas un avis juridique.

## Structure

```
agentic-rag-jurisprudence/
├── services/api/src/jurirag/   domain · application (agent, outils, vérificateur, ports) · infrastructure · interfaces
├── services/api/tests/         unit/ (LLM scripté) · integration/ (API, Ollama réel)
├── services/ui/src/jurirag_ui/ Streamlit : pages, thème « Greffe », client API
├── scripts/                    banc d'essai des modèles, scénarios et comparaison
├── docs/                       analyse, décisions, index des fonctions, validation, schémas, traces, résultats
├── report/                     rapport (pdf) et figures
├── .streamlit/config.toml      thème
├── Makefile · pyproject.toml · uv.lock · .env.example
```
