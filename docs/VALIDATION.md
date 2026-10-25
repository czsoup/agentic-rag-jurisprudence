# Matrice de validation : exigences → implémentation → preuve

Statuts :
- **Vérifié** : terminé et vérifié par un test ou une trace réelle ;
- **Implémenté** : implémenté mais non vérifié en conditions réelles ;
- **Partiel** ;
- **Non réalisé**.

Les tests unitaires et d'intégration (`make test`, 81 tests) utilisent un LLM scripté. Les tests `make test-ollama` (4) et les traces de `docs/traces/` utilisent le vrai modèle et l'index réel.

## Socle RAG

| Exigence | Statut | Fichiers | Test / preuve | Reste à faire |
|---|---|---|---|---|
| Charger les décisions, périmètre, métadonnées | Vérifié | `infrastructure/corpus.py`, `index_builder.py` | `data/index/main/manifest.json` (3 954 décisions, rejets comptés) | — |
| Découpage | Vérifié | `application/chunking.py` | `unit/test_chunking.py` (5) | — |
| Retrieval lexical, dense, hybride | Vérifié | `infrastructure/indexes.py` | `docs/results/retrieval_dev.md` ; `integration/test_ollama_live.py` | Réévaluer sur l'index principal (`make eval`) |
| Recherche par mots-clés ou en langage naturel, affichage | Vérifié | `routers/cases.py`, `ui/pages/search.py` | AppTest de l'UI (DEC-019) ; `GET /api/v1/cases/search` | — |
| Résumé faits / procédure / décision | Implémenté | `application/rag.py` (`summarize`) | Appelé depuis l'UI ; pas encore de trace enregistrée | Capturer un résumé réel (figure 4) |
| Question-réponse fondée, passages affichés | Vérifié | `application/rag.py` (`ask`), onglet *Questions* | Runs « static » de `docs/traces/comparison_v1_interrompue/` | — |
| Ne pas inventer | Vérifié | `agent/verifier.py` | `unit/test_verifier.py` (17) ; contradiction interceptée en S3a | — |

## Agent

| Exigence | Statut | Fichiers | Test / preuve | Reste à faire |
|---|---|---|---|---|
| A. Retrieval sous forme d'outils, l'agent décide | Vérifié | `agent/tools.py`, `agent/graph.py` | `unit/test_tools.py` (13) ; traces S1–S3b | — |
| B. Boucle avec routage conditionnel | Vérifié | `agent/graph.py` (`builder`, arêtes explicites) | `unit/test_agent_graph.py` (15) ; S2 (relance après CHECK) | — |
| C. Vérification : preuves, cohérence, non-sourcé, relance | Vérifié | `agent/verifier.py`, `route_after_check` | `unit/test_verifier.py` ; S1 (relance), S2 (insufficient puis sufficient), S3a (contradiction) | — |
| D. API externe, distinction des sources | Non réalisé (choix) | provenance `origin` dans les sources | DEC-015 | — |
| E. Progression en direct dans l'interface | Vérifié | `routers/agent.py` (NDJSON), `ui/pages/agent.py`, `ui/livegraph.py` | Flux NDJSON vérifié (`integration/test_api.py`) ; `ui/tests/test_livegraph.py` (9) ; page Agent pilotée par AppTest contre l'API et l'index réels : question du scénario 2 puis question de suivi, mémoire reprise, validation humaine refusée (DEC-024) | Capture dans un navigateur (figure 5) |
| Trace DECISION / TOOL / OBSERVATION / CHECK / FINAL | Vérifié | `domain/trace.py`, `Recorder` | `docs/traces/S*_single.md` | — |
| Deux outils réels | Vérifié | `CaseTools` | `integration/test_ollama_live.py::test_real_index_search_and_read` | — |
| Condition d'arrêt explicite | Vérifié | `budget_gate`, `abstain`, `StopReason` | `test_iteration_limit_is_enforced` ; S3b (5 itérations) | — |
| Citer les passages, ne rien inventer | Vérifié | alias `[Pn]`, règles R1–R3 | `test_fabricated_citation_is_caught_by_rules` ; traces | — |
| Erreurs d'outil visibles et gérées | Vérifié | `ToolExecutor`, événements `ERROR` | `test_invalid_calls_execute_nothing`, `test_ollama_down_stops_cleanly` ; expiration réelle (archive v1) | — |
| Scénario 1 — RAG simple | Vérifié | — | `docs/traces/S1_single_essai1.md` (1 recherche, 3 appels) et `S1_single.md` (variance, réponse partielle) | — |
| Scénario 2 — multi-étapes | Vérifié | — | `docs/traces/S2_single.md` | — |
| Scénario 3 — information insuffisante | Vérifié | — | `docs/traces/S3b_single.md` (5 reformulations, limite, HITL, abstention) ; `S3a_single.md` | — |
| Comparaison avec le RAG statique | Vérifié | `scripts/run_scenarios.py --set comparison` | `docs/results/comparison.md` (24 runs) ; rapport §15 | Répétitions (pass^k) : amélioration possible |
| Documentation : README, schéma, 3 traces, analyse | Vérifié | `README.md`, `docs/diagrams/`, `docs/traces/`, `report/rapport.md` | Rapport §13, §16, §17 | Captures d'écran (§13) |

## Extensions

| Exigence | Statut | Fichiers | Test / preuve | Reste à faire |
|---|---|---|---|---|
| Mémoire | Vérifié (logique) | `AgentGraph.start`, `AgentRunner`, checkpointer SQLite | `test_memory_keeps_the_case_between_questions`, `test_selecting_another_case_purges_memory` | Démonstration réelle (vidéo, séquence 8) |
| Multi-agents | Vérifié | `agent/multi.py` (v2, DEC-023) | `unit/test_multi_agent.py` (5) ; v1 et v2 mesurées (`comparison.md`) | — |
| Human-in-the-loop | Vérifié | `human_gate`, `interrupt`, export | `test_budget_extension_requires_human_approval`, tests d'export ; événements `HUMAN` dans S1, S3a, S3b | — |
| Observabilité | Vérifié | `run_store.py`, `RunMetrics`, `/api/v1/metrics`, page *Observabilité* | `test_run_streams_ndjson_events_then_final_status` ; `data/app.db` | — |

## Qualité

| Contrôle | Résultat |
|---|---|
| `make lint` (ruff + mypy strict) | OK, 40 fichiers |
| `make test` | 81 réussis |
| `make test-ollama` | 4 réussis |
| Secrets | Aucun ; aucune clé utilisée |
