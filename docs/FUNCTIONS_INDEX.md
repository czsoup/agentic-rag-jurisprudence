# Index des fonctions et classes importantes

Chemins relatifs à `services/api/src/jurirag/`, sauf pour l'interface (`services/ui/src/jurirag_ui/`). Colonne « Tests » : fichiers sous `services/api/tests/`.

## Domaine (sans I/O)

| Élément | Fichier | Rôle | Tests |
|---|---|---|---|
| `Case`, `CaseMeta`, `Passage`, `Zone`, `Provenance` | `domain/models.py` | Décision, métadonnées, passage indexé avec offsets et zone, provenance (dataset, révision, URL) | `unit/test_chunking.py` |
| `ToolCall`, `ToolSpec`, `ChatMessage`, `GenerationParams`, `LLMResponse` | `domain/llm.py` | Valeurs échangées avec un LLM, indépendantes d'Ollama | `unit/test_ollama.py` |
| `ClaimCheck`, `VerifierReport`, `VerifierStatus`, `NextAction` | `domain/verification.py` | Résultat structuré du vérificateur | `unit/test_verifier.py` |
| `TraceEvent`, `EventType`, `RunMetrics`, `StopReason` | `domain/trace.py` | Trace opérationnelle et métriques d'un run | `unit/test_agent_graph.py` |
| `LLMError` et ses sous-classes, `CaseNotFoundError`, `IndexNotReadyError` | `domain/errors.py` | Erreurs typées | `unit/test_ollama.py`, `integration/test_api.py` |

## Application (cas d'usage, ne dépend que des ports)

| Élément | Fichier | Rôle | Tests |
|---|---|---|---|
| `LLMPort`, `EmbedderPort`, `RetrieverPort`, `CaseRepository`, `RunStore` | `application/ports.py` | Contrats implémentés par l'infrastructure | doublures dans `conftest.py` |
| `chunk_case`, `chunk_spans` | `application/chunking.py` | Découpage structurel par zone, puis récursif aligné sur les phrases, avec chevauchement | `unit/test_chunking.py` |
| `EvidenceRegistry`, `extract_citations` | `application/evidence.py` | Registre des passages montrés au modèle, alias P1…Pn, extraction des citations | `unit/test_tools.py` |
| `SearchCasesArgs`, `ReadCaseArgs` | `application/agent/tools.py` | Validation des arguments proposés par le modèle | `unit/test_tools.py` |
| `CaseTools.search_cases`, `CaseTools.read_case` | `application/agent/tools.py` | Les deux outils obligatoires, branchés sur l'index réel | `unit/test_tools.py`, `integration/test_ollama_live.py` |
| `ToolExecutor.execute` | `application/agent/tools.py` | Liste blanche, validation, exécution, mesure ; ne lève jamais, renvoie un `ToolResult` | `unit/test_tools.py` |
| `EvidenceVerifier.verify` | `application/agent/verifier.py` | Règles R1–R3, puis LLM juge (fidélité et pertinence), puis statut et action suivante | `unit/test_verifier.py` |
| `split_claims`, `is_abstention`, `supported_subset` | `application/agent/verifier.py` | Affirmations et citations ; abstention ; réponse partielle vérifiée | `unit/test_verifier.py` |
| `AgentGraph.builder` | `application/agent/graph.py` | Graphe LangGraph à agent unique, arêtes déclarées explicitement | `unit/test_agent_graph.py` |
| `AgentGraph.decide` / `act` / `verify` / `route_after_check` | `application/agent/graph.py` | Décision du modèle, exécution des outils, contrôle, routage conditionnel | `unit/test_agent_graph.py` |
| `AgentGraph.budget_gate`, `AgentGraph.human_gate` | `application/agent/graph.py` | Limite d'itérations ; validation humaine bloquante (`interrupt`) | `unit/test_agent_graph.py` |
| `AgentGraph.finalize`, `AgentGraph.abstain` | `application/agent/graph.py` | Réponse avec sources, limites et mise à jour de la mémoire ; abstention motivée | `unit/test_agent_graph.py` |
| `Recorder` | `application/agent/graph.py` | Émission des événements de trace et tenue des métriques | `unit/test_agent_graph.py` |
| `prune_context` | `application/agent/graph.py` | Élagage des vieilles observations (context engineering) | — |
| `MultiAgentGraph` (`supervisor`, `researcher`, `write`) | `application/agent/multi.py` | Mode multi-agents : superviseur, chercheur, vérificateur | `unit/test_multi_agent.py` |
| `AgentRunner.run`, `resume`, `snapshot`, `reset` | `application/agent/runner.py` | Exécution diffusée, persistance, expiration HITL, mémoire de session | `unit/test_agent_graph.py`, `integration/test_api.py` |
| `StaticRAG.ask`, `StaticRAG.summarize` | `application/rag.py` | RAG statique (point de comparaison) ; résumé faits / procédure / décision | `scripts/run_scenarios.py` (réel) |
| `build_queries`, `add_paraphrases`, `evaluate` | `application/retrieval_eval.py` | Évaluation du retrieval : Hit@k, MRR, trois types de requêtes | `jurirag-eval` (réel) |

## Infrastructure (adapters)

| Élément | Fichier | Rôle | Tests |
|---|---|---|---|
| `OllamaClient.chat` | `infrastructure/ollama.py` | `/api/chat` avec outils, `think`, `format` JSON, tokens ; erreurs typées | `unit/test_ollama.py`, `integration/test_ollama_live.py` |
| `OllamaEmbedder.embed` | `infrastructure/ollama.py` | `/api/embed` | `unit/test_ollama.py` |
| `select_rows`, `iter_cases`, `to_case`, `normalize_text` | `infrastructure/corpus.py` | Sélection reproductible, lecture en flux du parquet, nettoyage, provenance | index réels (`manifest.json`) |
| `BM25Index`, `DenseIndex`, `rrf`, `HybridRetriever` | `infrastructure/indexes.py` | BM25 français, dense exact, fusion RRF ; recherche globale et dans une seule décision | `integration/test_ollama_live.py`, `jurirag-eval` |
| `build_index` | `infrastructure/index_builder.py` | Job d'indexation hors ligne et manifeste | `make index` |
| `SqliteCaseStore` | `infrastructure/case_store.py` | Décisions et passages (lecture seule côté API) | `integration/test_ollama_live.py` |
| `SqliteRunStore` | `infrastructure/run_store.py` | Runs, événements, validations d'export | `integration/test_api.py` |

## Interfaces

| Élément | Fichier | Rôle |
|---|---|---|
| `create_app`, `main` | `interfaces/http/app.py` | Application FastAPI et gestion des erreurs (503, 504, 502, 404) |
| `build_container` | `interfaces/http/container.py` | Composition root de l'API |
| `health` | `interfaces/http/routers/system.py` | Ollama, modèles, index, paramètres, avec les commandes à lancer en cas de problème |
| `start_run`, `resume_run`, `get_session`, `reset_session` | `interfaces/http/routers/agent.py` | Runs diffusés en NDJSON, reprise HITL, mémoire |
| `request_export`, `decide_approval` | `interfaces/http/routers/agent.py` | Export soumis à validation humaine |
| `search_cases`, `get_case`, `summarize_case`, `ask_static` | `interfaces/http/routers/cases.py` | Parcours RAG : recherche, lecture, résumé, question |
| `build`, `evaluate` | `interfaces/cli.py` | `jurirag-build`, `jurirag-eval` |

## Interface Streamlit

| Élément | Fichier | Rôle |
|---|---|---|
| `run_agent`, `resume`, `_stream` | `api.py` | Lecture ligne à ligne du flux NDJSON |
| `trace_html`, `answer_html`, `passage_html`, `stamp`, `figures_html` | `theme.py` | Composants de la direction « Greffe » ; tout texte est échappé |
| `pages/search.render` | `pages/search.py` | Recherche → affaire → texte par zone → résumé → questions |
| `graph_svg`, `visits`, `path_steps`, `path_html` | `livegraph.py` | Graphe de la boucle (nœud en cours surligné, arêtes parcourues, visites comptées) et récapitulatif du parcours, déduits du champ `node` des événements |
| `pages/agent.render` | `pages/agent.py` | Conversation en bulles, graphe et trace en direct, parcours, validation humaine, réponse vérifiée, mémoire, export |
| `pages/observability.render` | `pages/observability.py` | Métriques par mode, relecture d'une trace |
| `pages/system.render` | `pages/system.py` | État du système et provenance de l'index |
