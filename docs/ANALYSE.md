# Analyse du besoin — Agentic RAG sur la jurisprudence

Rédigée le 2026-10-23, avant tout développement. Ce document fixe le cahier des charges, les contraintes, les ambiguïtés et les risques. Les **choix d'implémentation** sont signalés comme tels et détaillés dans `docs/DECISIONS.md`.

## 1. Objectif

Construire un assistant de recherche en jurisprudence sur le corpus `antoinejeannot/jurisprudence` : recherche d'affaires, sélection, résumé et question-réponse fondée sur le texte. Puis transformer ce RAG en **système agentique** : le retrieval devient un outil que l'agent appelle quand il le juge utile, une vérification des preuves précède la réponse, et l'exécution est rendue observable.

Concrètement :
- réutiliser le système RAG comme outil ;
- mettre en place une boucle agentique avec routage conditionnel ;
- ajouter au moins un mécanisme de vérification avant la réponse finale ;
- rendre l'exécution observable : étapes, outils, arguments, observations et décision suivante.

Question directrice, qui sert de critère d'évaluation : *le système prend-il de meilleures décisions grâce à l'agent, ou a-t-il simplement ajouté des appels LLM autour du même RAG ?*

## 2. Cahier des charges

### 2.1 Socle RAG

| ID | Exigence |
|---|---|
| R1 | Charger les décisions, choisir un périmètre, conserver les métadonnées utiles |
| R2 | Définir une stratégie de découpage ; implémenter un retrieval lexical, dense ou hybride |
| R3 | Rechercher par mots-clés ou requête en langage naturel ; afficher les affaires les plus pertinentes |
| R4 | Résumer l'affaire sélectionnée : faits, procédure, décision, lorsque ces informations sont disponibles |
| R5 | Question-réponse sur l'affaire sélectionnée, fondée sur le texte, avec les passages utilisés affichés |
| R6 | Tester sur plusieurs requêtes et plusieurs affaires ; identifier les limites |
| R7 | Utilisable depuis l'interface : recherche → sélection → résumé → questions/réponses |
| R8 | Ne pas inventer d'informations absentes de l'affaire |
| R9 | Architecture Interface / Backend-API / Index-Retrieval / LLM local |

### 2.2 Agent

| ID | Exigence |
|---|---|
| A | Retrieval exposé en outils ; l'agent décide quand rechercher et quelle affaire lire, sans recevoir automatiquement les mêmes passages |
| B | Agent qui choisit entre rechercher, lire une affaire, source externe, vérifier, répondre ; logique de boucle explicite (LangGraph ou Python) |
| C | Vérifier au minimum : présence de preuves, cohérence réponse/passages, absence d'information non sourcée ; en cas d'échec, relancer une recherche ou reformuler |
| D | API externe optionnelle ; si présente, distinguer clairement sources du corpus et sources externes |
| E | Progression visible en direct ou quasi-direct : étape courante, outil, arguments, résultat résumé, décision suivante, condition d'arrêt |
| TRACE | Trace opérationnelle DECISION / TOOL / OBSERVATION / CHECK / FINAL, sans long Chain-of-Thought |
| G1 | Réutiliser le corpus et l'index du socle RAG, ou expliquer toute modification |
| G2 | Au moins 2 outils réels : `search_cases(query, k)` et `read_case(case_id)` |
| G3 | Condition d'arrêt explicite : réponse finale, nombre maximal d'étapes (par exemple 5) ou erreur contrôlée |
| G4 | Citer les passages utilisés, ne pas inventer d'éléments absents des sources |
| G5 | Erreurs d'outil visibles et gérées proprement |
| T1 | Scénario 1 : RAG simple, une seule recherche, sans étapes inutiles |
| T2 | Scénario 2 : trouver une affaire puis lire ses passages |
| T3 | Scénario 3 : premier retrieval insuffisant → relance, reformulation (ou API externe) |
| CMP | Comparaison avec le RAG statique : un exemple où l'agent apporte de la valeur, un où le RAG simple est préférable |

État partagé minimal : query, messages, documents retrouvés, sources externes, nombre d'itérations, statut de vérification, réponse finale.

### 2.3 Extensions

| Extension | Objectif |
|---|---|
| Mémoire | Conserver l'affaire sélectionnée et le contexte utile entre deux questions |
| Multi-agents | Séparer un agent chercheur et un agent vérificateur ; un superviseur décide quand les appeler |
| Human-in-the-loop | Demander une validation avant une action sensible |
| Observabilité | Afficher le nombre d'appels LLM, les outils utilisés, la latence et éventuellement le coût |

## 3. Contraintes techniques

- **LLM local** : génération, juge et embeddings tournent localement (Ollama). Aucune API de LLM externe n'est utilisée comme moteur. Le modèle doit appeler des outils de façon fiable, d'où un modèle de taille moyenne (voir DEC-001).
- **Séparation des couches** : le frontend n'interroge jamais directement le modèle ; tout passe par le backend.
- **Paramètres de génération contrôlés et explicités** pour toute comparaison, appliqué ici à la comparaison RAG statique / agent.
- **Machine** : Apple M5, 10 cœurs, 32 Go de mémoire unifiée, 734 Go libres, macOS 26.6, Ollama 0.35.1. Pas de GPU dédié : Metal sur mémoire unifiée.
- **Corpus** (vérifié le 2026-10-23 via l'API Hugging Face) : version v2025.03.20, licence **Etalab 2.0**, trois fichiers parquet :

| Split | Décisions | Fichier parquet |
|---|---:|---:|
| cour_de_cassation | 553 075 | 1,72 Go |
| cour_d_appel | 363 509 | 3,34 Go |
| tribunal_judiciaire | 142 239 | 0,78 Go |

Colonnes utiles : `id`, `jurisdiction`, `chamber`, `formation`, `type`, `decision_date`, `number`, `numbers`, `ecli`, `solution`, `publication`, `themes`, `summary`, `visa`, `contested`, `text`, `zones`. Le champ **`zones`** contient des offsets (`introduction`, `expose`, `moyens`, `motivations`, `dispositif`, `annexes`) dans `text` : il permet un découpage structurel et un résumé faits/procédure/décision ancré dans la structure réelle de l'arrêt. Il est **parfois absent** (observé à `null` sur une décision de 1860), ce qui impose un filtrage ou un découpage de repli.

## 4. Principes de conception

| Principe | Usage dans le projet |
|---|---|
| Températures selon la tâche (0–0,2 extraction/JSON ; 0,2–0,4 factuel) | Paramètres du routeur, du rédacteur et du juge |
| Séparer instructions et données | Passages entre délimiteurs `<doc>` ; le contenu d'un outil n'est jamais une instruction |
| Contraindre le format de sortie | Sorties JSON contraintes et validées par pydantic |
| Hallucination de références | Contrôle des citations fabriquées |
| Indexation hors ligne / interrogation en ligne | Job d'indexation séparé de l'API |
| Prompt augmenté, « je ne sais pas », citations [n] | Prompt du RAG statique et du rédacteur |
| BM25 (IDF, saturation k₁, normalisation b) | Index lexical ; robustesse sur les numéros d'articles et de pourvois |
| Modèles d'embedding récents (Qwen3-Embedding, BGE-M3) | Candidats pour le dense |
| Sparse et dense complémentaires ; fusion RRF | Recherche hybride évaluée |
| Taille des chunks : 300–800 tokens, chevauchement 10–20 % | Paramètres de départ, à mesurer |
| Découpage structurel | Découpage par zone de l'arrêt |
| Métadonnées par chunk (filtrer, citer) | Provenance de chaque passage |
| Recherche exacte vs ANN | Recherche exacte : volume compatible |
| Construire le contexte : dédupliquer, ordonner, budgéter, isoler | Assemblage des passages |
| Grounding au niveau de chaque affirmation | Vérificateur par affirmation |
| Contexte suffisant et abstention guidée | Statut `insufficient` → abstention |
| Sources contradictoires : signaler le conflit | Statut `contradictory` |
| Corrective RAG : juger avant d'utiliser | Vérification de la pertinence des passages |
| Multi-hop : chercher puis relire avec la nouvelle information | Scénario 2 |
| RAG agentique : la recherche devient un outil | Cœur du projet |
| Recall@k, Precision@k, MRR, nDCG | Évaluation du retrieval |
| Fidélité et LLM-juge, pièges du juge | Évaluation et vérificateur |
| Points de défaillance d'un RAG | Analyse des échecs |
| Injection de prompt indirecte via le corpus | Les passages sont traités comme des données |
| LLM seul / RAG / agent | Comparaison statique / agentique |
| Chatbot, workflow ou agent | Justifier le surcoût de l'agent |
| Boucle agentique et conditions d'arrêt | Boucle et motifs d'arrêt |
| Erreurs qui se composent | Limiter le nombre d'étapes |
| Function calling : le LLM demande, le code exécute | Outils validés côté backend |
| Schéma JSON d'outil, description = prompt | Contrats des outils |
| Concevoir de bons outils (erreurs utiles, réponses concises) | Observations compactes et erreurs explicites |
| Moindre privilège, validation humaine, résultats d'outils non fiables | Liste blanche et HITL |
| ReAct | Boucle décision → outil → observation |
| Évaluateur – optimiseur ; « commencer simple » | Vérificateur qui renvoie vers la recherche |
| Budgets, validation humaine, traçabilité, sorties structurées, vérifications externes | Garde-fous de la boucle |
| Context engineering | Élagage des observations, état structuré |
| Types de mémoire ; court terme | Mémoire de session |
| Harness : séparer décisions et comptabilité | L'état est tenu par le code, pas par le LLM |
| Pourquoi plusieurs agents, architectures, échecs | Mode multi-agents et ses limites |
| Un agent ou plusieurs | Justification générateur + vérificateur |
| LangGraph : état, nœuds, arêtes, checkpointer, interrupt, superviseur, stream | Implémentation |
| Évaluer résultat, trajectoire, fiabilité | Métriques de comparaison |
| Menaces sur les agents | Sécurité des outils |

## 5. Critères de réussite

1. Chaîne complète utilisable depuis l'interface : recherche → affaire → résumé → question → réponse citée.
2. L'agent ne fait pas toujours le même chemin : scénario 1 en une recherche, scénario 2 avec `read_case`, scénario 3 avec relance ou abstention. La trace le montre.
3. Toute affirmation de la réponse finale renvoie à un passage réellement récupéré ; aucune citation fabriquée.
4. Le vérificateur peut échouer et son échec change le comportement (relance, puis abstention).
5. La boucle s'arrête toujours (limite effective, testée).
6. Les erreurs (Ollama arrêté, modèle absent, timeout, arguments invalides, identifiant inconnu) sont visibles et n'entraînent aucune action non validée.
7. La comparaison avec le RAG statique s'appuie sur des chiffres mesurés et reste honnête sur les cas où le statique est préférable.

## 6. Ambiguïtés et arbitrages

| Ambiguïté | Arbitrage | Statut |
|---|---|---|
| Base technique de départ | Reprise d'une application précédente (FastAPI + Streamlit + Ollama) pour la plomberie | Retenu, DEC-002 |
| Taille du modèle local | Modèle de 9B plutôt qu'un petit modèle d'environ 1B, justifié par le tool calling | Retenu, DEC-001 |
| « Sous-ensemble cohérent » du corpus | Cour de cassation, décisions récentes avec `zones`, taille réglable | Proposé, à mesurer |
| Validation humaine « avant une action externe sensible » sans API externe | Validation sur des actions internes réellement sensibles (prolonger le budget, diffuser une réponse contestée, exporter le dossier) | Écart assumé et documenté |
| Vérification « au minimum » : rien n'impose un LLM juge | Règles déterministes + LLM juge par affirmation, chacun évalué | Choix d'implémentation |
| Pas de jeu annoté pour le retrieval | Pseudo-requêtes construites à partir du sommaire et des thèmes officiels | Biais documenté |

## 7. Risques techniques

| Risque | Effet | Parade |
|---|---|---|
| Tool calling instable sur un 9B | Arguments invalides, outil inexistant, texte au lieu d'un appel | Validation pydantic, message d'erreur renvoyé au modèle, repli contrôlé, compteur d'erreurs |
| Thinking activé par défaut sur Qwen | Latence élevée, fuite de `<think>` | `think=false` par défaut pour le routage ; effet mesuré ; le raisonnement n'est jamais affiché |
| Latence d'un agent multi-appels | Démo lente | Peu d'outils, observations compactes, `num_ctx` maîtrisé, budget d'itérations |
| Volume du corpus (1 M décisions) | Indexation trop longue | Sous-ensemble réglable ; vitesse d'embedding mesurée avant de fixer N |
| `zones` absentes ou incohérentes | Découpage faux | Filtrage ou découpage récursif de repli, compteur de documents rejetés |
| LLM-juge complaisant | Validation à tort | Règles déterministes en premier ; un « incertain » n'est jamais promu en succès ; juge évalué sur des cas construits |
| Requêtes répétées par l'agent | Boucle inutile | Détection des requêtes déjà jouées, budget strict |
| Contamination de la mémoire entre sessions | Fuite de contexte | Mémoire indexée par `thread_id`, TTL, réinitialisation, tests |
| Biais des pseudo-requêtes | Évaluation du retrieval optimiste | Limite signalée ; quelques requêtes rédigées à la main en complément |

## 8. Plan de réalisation

| Phase | Contenu |
|---|---|
| A | Analyse du besoin (ce document) |
| B | Environnement, modèles Ollama, banc de tool calling, DEC-001 |
| C | Corpus (téléchargement, filtrage, normalisation, provenance) et index (chunking, BM25, dense, hybride) |
| D | Évaluation du retrieval, RAG statique, résumé, tests |
| E | Outils `search_cases` / `read_case`, boucle LangGraph |
| F | Vérificateur, relance et abstention, trace en direct, gestion d'erreurs |
| G | Interface Streamlit, direction « Greffe » |
| H | Mémoire, multi-agents, human-in-the-loop, observabilité |
| I | Trois scénarios sur le corpus réel, traces, comparaison statique / agent |
| J | Décisions, schémas, rapport, README |
| K | Revue finale, matrice de validation |
