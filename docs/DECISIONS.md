# Journal des décisions techniques

Chaque décision indique ce qui a été **réellement testé ou mesuré**, les options écartées et les principes de conception sur lesquels elle s'appuie.

---

### DEC-001 — Modèle de génération : qwen3.5:9b, comparé à qwen3:8b

- **Date** : 2026-10-23 · **Statut** : acceptée (banc de comparaison : voir DEC-016)
- **Problème** : choisir un LLM local capable d'appeler des outils de façon fiable, sur la machine disponible.
- **Contexte et contraintes** : Apple M5, 10 cœurs, 32 Go de mémoire unifiée, 734 Go libres, Ollama 0.35.1. Un run d'agent enchaîne 3 à 8 appels LLM : la vitesse par appel compte autant que la qualité.
- **Exigence** : LLM exécuté localement, sans aucune API de LLM externe ; tool calling pour la boucle.
- **Principes** : function calling, apprentissage de l'usage d'outils ; température selon la tâche ; modèles à raisonnement.
- **Options envisagées** (tailles relevées sur ollama.com le 2026-10-23) : qwen3:8b (5,2 Go, déjà installé) ; qwen3.5:9b (6,6 Go, Q4_K_M, tools + thinking, contexte 256K) ; qwen3.5:27b (17 Go, dense) ; qwen3.6:35b-a3b (23–24 Go, MoE ≈ 3B actifs).
- **Décision** : qwen3.5:9b en principal, qwen3:8b en comparaison.
- **Justification** : les modèles de 27 à 35B occupent l'essentiel de la mémoire utilisable par le GPU sur 32 Go, alors qu'il faut aussi charger le modèle d'embedding et faire tourner l'OS. Le 27B dense est en outre environ 3× plus lent par appel, pour un agent qui en fait plusieurs. Le 9B est la plus récente génération de Qwen tenant confortablement en mémoire. `ollama show` confirme les capacités `tools` et `thinking`, désactivable.
- **Paramètres** : température 0,1 pour décider et rédiger, 0 pour le juge ; `seed` 42 ; `top_p` 0,9 ; `num_ctx` 16 384 ; raisonnement activé pour les seules décisions de l'agent (DEC-016) ; `keep_alive` 30 min.
- **Fichiers** : `config.py`, `infrastructure/ollama.py`, `.env.example`.
- **Tests réalisés** : un premier run réel de bout en bout avec qwen3.5:9b (question « abandon de poste ») : 6 appels LLM, `search_cases` puis `read_case`, une vérification en échec puis une réussite, 102 s, ralenti par une évaluation qui tournait en parallèle. Banc comparatif : DEC-016.
- **Alternatives rejetées** : un modèle lourd téléchargé « pour voir » (coût disque et mémoire sans gain démontré) ; une API externe (interdite).

### DEC-002 — Base de départ : un projet précédent

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Problème** : ne pas repartir de zéro pour la plomberie (client LLM, API, configuration) et se concentrer sur le RAG et l'agent.
- **Décision** : nouveau projet qui reprend et adapte une application précédente d'extraction d'information avec un LLM local : le client Ollama et ses erreurs typées, la configuration pydantic-settings, la journalisation, la structure FastAPI et la règle « l'interface ne parle jamais au modèle ».
- **Fichiers** : `infrastructure/ollama.py`, `config.py`, `logging_config.py`, `interfaces/http/app.py`.

### DEC-003 — Architecture : clean architecture et 3 services

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Problème** : une architecture professionnelle et défendable, sans microservices inutiles.
- **Principes** : « commencer simple, mesurer » ; indexation hors ligne / interrogation en ligne.
- **Options** : monolithe modulaire ; clean architecture et 3 services ; microservices (recherche, agent, vérificateur, mémoire séparés, avec une base vectorielle dédiée).
- **Décision** : trois services lancés séparément (UI Streamlit, API FastAPI, Ollama natif) et un job d'indexation hors ligne. Dans l'API, quatre couches : `domain` → `application` (cas d'usage, agent, **ports** `Protocol`) → `infrastructure` (adapters) → `interfaces` (HTTP, CLI). Une seule composition root (`bootstrap.py`, `interfaces/http/container.py`).
- **Justification** : la règle de dépendance rend l'agent testable sans Ollama ni index : 70 tests utilisent des doublures (LLM scripté, retriever en mémoire). Les microservices ajouteraient du réseau et des déploiements sans besoin réel ici.
- **Compromis** : Ollama reste natif. Sous macOS, Docker n'a pas accès au GPU Metal, ce qui rendrait le modèle très lent. Des Dockerfiles ne sont pas fournis tant que Docker n'est pas installé et que leur fonctionnement n'a pas été vérifié.

### DEC-004 — Corpus : un sous-ensemble cohérent de la Cour de cassation

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Problème** : 1 058 823 décisions au total, trop pour indexer en dense sur cette machine.
- **Vérifications faites** (API Hugging Face et lecture du parquet) : révision `8019db1…` (v2025.03.20), licence Etalab 2.0, trois fichiers parquet. Le champ `zones` est présent sur environ 99 % des décisions depuis 2016 (par ex. 17 115 sur 17 231 en 2023), absent en 1860. Les offsets de fin de zone dépassent parfois d'un caractère la longueur du texte (observé : 18 503 pour 18 502). Les titres de `visa` contiennent du HTML (liens Légifrance).
- **Contrainte** : indexer l'ensemble du corpus ou un sous-ensemble cohérent.
- **Décision** : split `cour_de_cassation`, années 2022 à 2024, 6 chambres (sociale, 3 civiles, commerciale, criminelle). Sont exclues : les ordonnances du premier président, et les solutions « Déchéance », « Désistement » et « Non-lieu à statuer », qui sont des décisions de procédure sans motivation au fond. On exige des zones `motivations` ou `dispositif`. Échantillon : 4 000 décisions (graine 42), dont 50 % publiées au Bulletin. Celles-ci portent un sommaire, utile à l'évaluation (DEC-008).
- **Traitement** : bornage des offsets de zone ; HTML retiré des visas ; texte normalisé zone par zone, en espaces seulement (casse, ponctuation et références intactes) ; offsets recalculés ; déduplication par `id` ; rejets comptés. Le manifeste `data/index/<nom>/manifest.json` consigne la révision, les filtres, les comptes et les durées.
- **Mesures (index de dev, 1 500 tirées)** : 37 705 candidates sur 2022–2024 ; rejets : 12 811 hors chambres retenues, 494 décisions de procédure, 313 sans zonage utilisable, 4 doublons.
- **Lecture du parquet** : un seul row group de 1,7 Go. Une lecture filtrée incluant `text` a dépassé 5 minutes. D'où deux passes : colonnes légères pour sélectionner, puis `iter_batches` sur les seules lignes retenues.
- **Modifier le périmètre** : `uv run jurirag-build --n 8000 --year-from 2020 --year-to 2024 --index-name autre`.

### DEC-005 — Découpage : structurel par zone, puis récursif

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Principes** : taille, chevauchement, découpage structurel, métadonnées.
- **Décision** : un passage n'enjambe jamais deux zones (exposé, moyens, motivations, dispositif, introduction). Dans une zone, fenêtres alignées sur les phrases d'environ 450 tokens, avec 15 % de chevauchement. Le nombre de tokens est estimé à 1,3 par mot. Les **annexes sont exclues** de l'index principal : elles reproduisent le moyen des parties, ce qui double les « moyens », et un argument de partie ne dit pas ce que juge la Cour. Identifiant `{case_id}#{zone}-{n}`, offsets conservés.
- **Mesure (index de dev, annexes incluses)** : 12 585 passages pour 1 496 décisions, longueur moyenne de 822 (dispositif) à 1 804 caractères (annexes). Index principal : 27 249 passages pour 4 000 décisions, sans annexes.
- **Tests** : `tests/unit/test_chunking.py` : fenêtres sur fin de phrase, chevauchement, phrase sans ponctuation, zones jamais mélangées, offsets exacts, repli sans zonage.

### DEC-006 — Modèle d'embeddings : qwen3-embedding:0.6b, distinct du générateur

- **Date** : 2026-10-23 · **Statut** : acceptée ; la comparaison avec BGE-M3 reste à faire (DEC-017)
- **Principes** : modèles Qwen3-Embedding et BGE-M3 ; le même modèle pour les passages et la requête.
- **Décision** : `qwen3-embedding:0.6b` via Ollama, en dimension 1 024. Requête préfixée par l'instruction attendue par ce modèle, documents sans préfixe. Le modèle d'embedding de l'index est lu dans le manifeste pour encoder les requêtes avec le même.
- **Mesure et correction** : un premier banc annonçait 77 passages/s, mais il répétait le même texte et Ollama réutilisait son cache de prompt (`cached n_tokens` dans le journal du serveur). Débit réel mesuré pendant l'indexation : **8,4 passages/s** (12 585 passages en 1 490 s). C'est ce qui a conduit à réduire l'index principal de 8 000 à 4 000 décisions.

### DEC-007 — Retrieval : hybride BM25 + dense, fusion RRF

- **Date** : 2026-10-23 · **Statut** : acceptée, sur mesure
- **Principes** : BM25, force sur les références exactes, complémentarité, RRF, recherche exacte suffisante à ce volume.
- **Implémentation** : bm25s (k1 = 1,5, b = 0,75), stopwords français et racinisation Snowball. Le motif de tokens garde « 2312-18 » ou « 21-23 » en un seul token. Dense : produit scalaire exact sur vecteurs normalisés (numpy, en mémoire mappée). RRF avec k = 60 sur 50 candidats par liste.
- **Mesure** (`jurirag-eval`, index de dev de 1 496 décisions, 150 arrêts publiés, 3 types de requêtes, détail dans `docs/results/retrieval_dev.md`) :

| Méthode | Requêtes | Hit@1 | Hit@5 | Hit@10 | MRR@10 |
|---|---|---|---|---|---|
| BM25 | sommaire | 0,887 | 0,987 | 1,000 | **0,931** |
| Dense | sommaire | 0,647 | 0,847 | 0,867 | 0,732 |
| Hybride | sommaire | 0,767 | 0,927 | 0,993 | 0,836 |
| BM25 | thèmes | 0,447 | 0,693 | 0,820 | 0,556 |
| Dense | thèmes | 0,433 | 0,740 | 0,793 | 0,550 |
| Hybride | thèmes | 0,453 | 0,760 | 0,867 | **0,587** |
| BM25 | question | 0,820 | 0,960 | 0,987 | 0,878 |
| Dense | question | 0,807 | 0,927 | 0,967 | 0,856 |
| Hybride | question | 0,853 | 0,993 | 1,000 | **0,911** |

- **Confirmation sur l'index principal** (3 954 décisions, sans annexes, `docs/results/retrieval_main.md`), MRR@10 :

| Méthode | Sommaire | Thèmes | Question |
|---|---|---|---|
| BM25 | **0,904** | 0,477 | 0,837 |
| Dense | 0,672 | 0,491 | 0,840 |
| Hybride | 0,797 | **0,509** | **0,860** |

  Le classement est le même, l'écart plus faible.
- **Décision** : hybride par défaut (`RETRIEVAL_METHOD=hybrid`). BM25 et dense restent sélectionnables dans l'interface.
- **Justification** : BM25 ne gagne que sur les requêtes « sommaire », qui reprennent presque mot pour mot la motivation (biais lexical connu). Sur les questions reformulées, les plus proches d'un usage réel, et sur les mots-clés, l'hybride est le meilleur.
- **Limites** : une seule décision attendue par requête, alors que d'autres peuvent être pertinentes sans être comptées. Les questions sont générées par le même modèle local. Seul le classement relatif des méthodes a du sens. Latence mesurée : environ 1 ms en BM25, environ 35 ms en dense et hybride, ce dernier chiffre étant dominé par l'embedding de la requête.

### DEC-008 — Protocole d'évaluation du retrieval

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Principes** : Recall@k, MRR, jeu d'évaluation construit maison.
- **Décision** : aucun jeu annoté n'existe pour ce corpus. On utilise trois types de pseudo-requêtes tirées de 150 arrêts publiés :
  - « sommaire » : les 30 premiers mots ;
  - « thèmes » : les 4 premiers mots-clés du titrage ;
  - « question » : le sommaire reformulé par qwen3.5:9b, avec la consigne de ne pas recopier ses expressions.

  Les questions générées sont figées dans `docs/results/retrieval_questions_dev.json` pour que l'évaluation soit reproductible. Un échantillon a été relu : questions plausibles et en français courant.

### DEC-009 — Contrats des outils et validation côté code

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Exigence** : au moins 2 outils réels ; erreurs visibles et gérées.
- **Principes** : le LLM demande, le code exécute ; schéma JSON, peu d'outils, erreurs utiles, réponses concises, moindre privilège.
- **Décision** : `search_cases(query, k)` regroupe les passages par décision et renvoie, pour chacune, ses métadonnées et son meilleur passage. `read_case(case_id, focus?)` renvoie au plus 8 passages, dans l'ordre exposé → motivations → dispositif, ou classés par rapport au `focus`. Les arguments sont validés par pydantic : longueur de la requête, `k` entre 1 et 10, `case_id` sur un motif strict. Liste blanche des outils. Les erreurs sont renvoyées au modèle comme observation, sans rien exécuter, et marquées non récupérables si l'outil est indisponible.
- **Alias de citation** : chaque passage montré reçoit un alias court P1, P2…, stable pendant tout le run. Le modèle cite `[P3]`, le code fait la correspondance avec `passage_id`. Une citation absente du registre est donc inventée par construction.
- **Tests** : `test_tools.py` (13 cas : outil inconnu, arguments invalides ou mal formés, identifiant inconnu, service indisponible, alias stables).

### DEC-010 — Orchestration : LangGraph, avec arêtes explicites

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Exigence** : une logique de boucle explicite et lisible, que ce soit en LangGraph ou en Python pur.
- **Principes** : état, nœuds, arêtes, checkpointer, `interrupt`, superviseur, `stream`.
- **Options** : boucle Python maison ; `create_agent` (ReAct prêt à l'emploi) ; graphe LangGraph explicite.
- **Décision** : `StateGraph` explicite. Chaque nœud renvoie un `Command(goto=…)`, et les destinations sont déclarées dans `builder()` : c'est la carte exacte du graphe. Ce que LangGraph apporte ici : le checkpointer (mémoire de session et reprise), `interrupt()` (validation humaine bloquante) et `stream_mode="custom"` (trace en direct). `create_agent` est écarté, car il masquerait le vérificateur et les conditions d'arrêt qu'on veut montrer.
- **Version** : langgraph 1.2.16. Constat : les annotations `Literal[...]` des nœuds hérités servent à valider les arêtes, d'où l'usage de `destinations=`.

### DEC-011 — Boucle agentique et conditions d'arrêt

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Principes** : boucle et arrêt sur objectif, budgets, besoin d'un humain, erreurs qui se composent, traçabilité, élagage des résultats d'outils, le harness tient l'état.
- **Décision** :
  - limite de 5 itérations (`AGENT_MAX_ITERATIONS`), une itération étant un appel de décision ;
  - au plus 2 outils par tour ;
  - une requête déjà jouée (mêmes mots, dans n'importe quel ordre) est refusée sans être exécutée ;
  - élagage des vieilles observations au-delà d'environ 40 000 caractères, les passages restant citables ;
  - arrêts :
    - réponse vérifiée ;
    - abstention motivée, après au moins une tentative d'outil ;
    - limite atteinte, avec réponse partielle vérifiée ou abstention ;
    - erreur non récupérable ;
    - refus ou expiration humaine.

  La justification de chaque `DECISION` est générée par le code à partir de l'action et de l'état. Le texte du modèle n'y est ajouté que s'il est court, et le raisonnement interne n'est jamais affiché.
- **Tests** : `test_agent_graph.py` (15 cas, dont le garde-fou DEC-021 : les 3 scénarios avec un LLM scripté, la limite effective, la requête répétée, Ollama arrêté, un appel mal formé, la mémoire, la validation humaine).

### DEC-012 — Vérificateur : règles déterministes puis LLM juge

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Exigence** : vérifier la présence des preuves, la cohérence et l'absence d'information non sourcée ; relancer en cas d'échec.
- **Principes** : une citation par affirmation, vérification automatique, contexte suffisant et abstention, conflits, fidélité et pertinence de la réponse, fidélité et pièges du LLM-juge ; références inventées.
- **Décision** :
  - **R1** : une citation pour chaque phrase factuelle. Les énoncés de limite (« la décision ne précise pas… ») en sont dispensés.
  - **R2** : la citation doit exister dans le registre du run.
  - **R3** : les dates, numéros d'articles et de pourvois, montants et années présents dans la phrase doivent figurer dans le passage cité (« 1er mars » vaut « 1 mars », « L. 1234-5 » vaut « L1234-5 »).
  - **Juge** : un seul appel à température 0, sortie JSON contrainte, avec `supports`, `contradicts` ou `not_enough_info` par affirmation, plus `addresses_question`.
  - **Agrégat** :
    - `contradictory` si au moins une affirmation est contredite ;
    - `sufficient` si tout est soutenu **et** pertinent ;
    - `insufficient` sinon, avec l'action recommandée : `read_case` si une décision a été trouvée mais jamais lue, sinon `search_again`.
- **Aucun seuil numérique** : les scores de similarité ne participent jamais à la validation.
- **Ajout du contrôle de pertinence** : il vient du premier run réel. La réponse était fidèle aux passages mais traitait la mise à pied plutôt que l'abandon de poste. La fidélité seule ne suffisait pas.
- **Le vérificateur peut échouer** : un juge indisponible, un JSON invalide, une affirmation sans verdict ou un champ de pertinence absent ne valident rien.
- **Tests** : `test_verifier.py` (17 cas).
- **Limite** : le juge est le même modèle que le rédacteur. Un second appel n'est pas une preuve de fiabilité, d'où les règles R1 à R3 en premier.

### DEC-013 — Mémoire de session

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Principes** : mémoire de travail et court terme, checkpointer et `thread_id`, empoisonnement de la mémoire.
- **Décision** :
  - **Persistance** : checkpointer SQLite (`data/checkpoints.db`), avec `thread_id` égal à l'identifiant de session, aléatoire et généré par l'interface.
  - **Contenu** : l'affaire en cours et les 3 derniers échanges (question et réponse tronquée à 500 caractères), présentés au modèle comme du contexte à ne jamais citer comme preuve.
  - **Expiration** : 2 h d'inactivité.
  - **Changement d'affaire** : il purge la mémoire liée à l'affaire précédente.
  - **Réinitialisation** : `DELETE /sessions/{id}`.
  - **Séparation** : la mémoire est distincte de l'index documentaire, et les preuves sont réinitialisées à chaque run.
- **Tests** : conservation de l'affaire, isolation entre sessions, réinitialisation, changement d'affaire.

### DEC-014 — Multi-agents

- **Date** : 2026-10-23 · **Statut** : acceptée ; comparaison chiffrée : voir DEC-018
- **Principes** : quand plusieurs agents se justifient, architectures, modes d'échec, rôle du superviseur.
- **Décision** :
  - **superviseur** : un LLM avec sortie JSON (`researcher`, `write` ou `stop`, plus une consigne pour le chercheur), encadré par des garde-fous du code :
    - pas de rédaction sur un dossier vide ;
    - pas de nouvelle rédaction sans passage nouveau ;
    - pas d'arrêt sans recherche préalable ;
  - **chercheur** : au plus 3 tours d'outils par délégation, avec un contexte isolé ; il renvoie un compte rendu ;
  - **rédaction** : la synthèse est faite par le superviseur, sur le dossier partagé ;
  - **vérificateur** : le même `EvidenceVerifier` que l'agent unique ;
  - **partage** : le registre de preuves et l'historique des requêtes sont communs, donc aucune recherche n'est refaite.
- **Risque assumé** : la recommandation usuelle est de commencer avec un seul agent. Le mode multi est une extension expérimentale, et son coût est mesuré.

### DEC-015 — Human-in-the-loop sans API externe

- **Date** : 2026-10-23 · **Statut** : acceptée (pas d'API externe)
- **Exigence** : demander une validation humaine avant une action externe sensible.
- **Écart assumé** : faute d'API externe, la validation porte sur trois actions réellement sensibles :
  - prolonger le budget d'itérations ;
  - diffuser une réponse contredite par ses sources ;
  - exporter le dossier hors de l'application, seule action qui écrit sur disque.

  Les recherches locales ne demandent pas de confirmation.
- **Mécanisme** :
  - `interrupt()` suspend réellement le run ;
  - l'API renvoie `awaiting_approval` ;
  - au-delà de 5 min (`HITL_TIMEOUT_S`), toute réponse compte comme une expiration et l'action est annulée ;
  - une nouvelle question alors qu'une validation est en attente clôt celle-ci comme expirée ;
  - l'export passe par une demande enregistrée en base : rien n'est écrit avant la confirmation, et une décision ne peut pas être rejouée (409).

  Chaque décision est tracée par un événement `HUMAN`.
- **Tests** : prolongation acceptée ou refusée, expiration à l'arrivée d'une nouvelle question, contradiction puis diffusion approuvée, export confirmé, refusé ou expiré.

### DEC-016 — Banc d'essai des modèles : qwen3.5:9b avec raisonnement pour les décisions

- **Date** : 2026-10-24 · **Statut** : acceptée, sur mesure
- **Problème** : vérifier que le modèle choisit le bon outil, fournit des arguments valides, répond quand les preuves suffisent et s'abstient quand il n'y en a pas.
- **Méthode** (`scripts/bench_models.py`) : 4 sondes qui reproduisent des situations réelles de la boucle, avec le même prompt système, les mêmes outils et les mêmes paramètres que l'application ; 3 répétitions (graines 42 à 44).
  1. Question sans preuve : il faut chercher.
  2. Résultat de recherche dont l'extrait ne contient pas l'information demandée : il faut lire l'affaire.
  3. Passages suffisants : il faut répondre avec des citations, sans outil.
  4. Deux recherches vides : il faut s'abstenir ou reformuler.

  Le contenu brut de chaque réponse est conservé dans `docs/results/bench_models*.json`.
- **Résultats mesurés** (version finale du prompt, détecteur d'abstention corrigé) :

| Configuration | 1. chercher | 2. lire | 3. répondre | 4. s'abstenir | Total | Latence médiane |
|---|---|---|---|---|---|---|
| qwen3.5:9b, think=false | 3/3 | 0/3 | 3/3 | 3/3 | 9/12 | 2,4 s |
| qwen3:8b, think=false | 3/3 | 0/3 | 3/3 | 3/3 | 9/12 | 1,7 s |
| **qwen3.5:9b, think=true** | 3/3 | **3/3** | 3/3 | 3/3 | **12/12** | 3,4 s |

- **Échecs observés** : sans raisonnement, les deux modèles répondent « la décision… ne précise pas les dates d'absence et de licenciement dans l'extrait fourni [P1] » au lieu d'appeler `read_case`. qwen3.5:9b ajoute même « il faudrait consulter la décision complète ». La réponse est honnête mais incomplète.
- **Corrections en cours de banc**, consignées dans `docs/results/bench_history/` :
  - **Prompt** : une consigne ajoutée (« n'écris jamais qu'une information manque tant que tu n'as pas lu la décision ») a fait chuter qwen3.5:9b sans raisonnement à 0/3 sur la sonde 1. Il répondait sans chercher, avec une citation `[P1]` inexistante. Consigne retirée.
  - **Détecteur d'abstention** : il ignorait des formules correctes (« ne semble pas être abordée », « n'est donc pas disponible »), ce qui donnait un faux 0/3 à qwen3:8b sur la sonde 4. Il est désormais défini ainsi : aucune citation et au moins un énoncé de limite.
- **Décision** : qwen3.5:9b avec `think=true` pour les **décisions** de l'agent (`THINK_DECIDE`, agent unique et chercheur), `think=false` pour le juge, la rédaction statique, le résumé et la synthèse multi-agents.
- **Justification** : c'est la seule configuration qui lit l'affaire d'elle-même. Elle coûte environ 1 s de plus par décision en médiane, et 6,6 s sur la sonde 1. Le raisonnement n'est jamais affiché : `message.thinking` est ignoré par l'adapter. qwen3:8b est plus rapide mais n'apporte rien sur les décisions.
- **Limite** : 12 essais par configuration, c'est peu. Ce banc compare des comportements, pas une fiabilité statistique (pass^k).

### DEC-021 — Garde-fou « lire avant de conclure à une absence d'information »

- **Date** : 2026-10-24 · **Statut** : acceptée
- **Problème** : l'échec de la sonde 2 (DEC-016) est un vrai risque. L'agent s'arrêterait sur « l'extrait ne précise pas », alors que la décision trouvée contient l'information.
- **Décision** : avant d'appeler le juge, si la réponse candidate ne fait que constater des absences d'information, si une décision trouvée n'a pas été lue et s'il reste du budget, le code émet un `CHECK` (`guard=read_before_concluding`) et demande à l'agent `read_case(case_id=…)`. Aucun appel au juge n'est fait dans ce cas.
- **Mode multi** : garde-fou désactivé, c'est le superviseur qui arbitre.
- **Tests** : `test_premature_abstention_forces_reading_the_found_case`, qui rejoue la sortie réelle observée au banc.

### DEC-017 — Comparaison des modèles d'embedding (BGE-M3)

- **Statut** : non réalisée à ce stade. Elle demande de télécharger bge-m3 (environ 1,2 Go) et de ré-embedder un index, soit environ 25 min par index de 1 500 décisions au débit mesuré.

### DEC-018 — Comparaison RAG statique / agent unique / multi-agents

- **Date** : 2026-10-24 · **Statut** : réalisée (`scripts/run_scenarios.py --set comparison`, de 16 h 17 à 17 h 03, sur secteur, sans mise en veille ; v1 interrompue archivée dans `docs/traces/comparison_v1_interrompue/`)
- **Protocole** : 8 questions (`docs/results/questions.json`) × 3 modes, même modèle, mêmes paramètres, validation humaine toujours refusée par le script.
- **Résultats mesurés** (`docs/results/comparison.md`) :

| Mode | Vérifiées | Partielles | Abstentions | Non vérifiées affichées | LLM moy. | Latence médiane |
|---|---|---|---|---|---|---|
| Statique | 3 | — | 2 (dans le texte) | 7 | 1,9 | 32 s |
| Agent unique | 3 | 3 | 2 | 0 | 5,5 | 104 s |
| Multi-agents v2 | 3 | 4 | 1 | 0 | 13,0 | 231 s |

- **Lecture** :
  - autant de réponses entièrement vérifiées dans les trois modes ;
  - l'agent ne présente jamais d'affirmation non établie, et apporte de la valeur sur les questions multi-étapes (C4) ;
  - sur les questions simples (C3), le RAG statique est préférable ;
  - le multi-agents ne rapporte rien sur ce corpus.
- **Conséquence proposée** (non implémentée) : un routage, avec le RAG statique d'abord et l'agent si le vérificateur échoue.

### DEC-019 — Interface : Streamlit, direction « Greffe »

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Exigence** : progression visible en direct ; une seule interface pour la recherche et l'agent.
- **Décision** : Streamlit. Thème défini dans `.streamlit/config.toml` (palette papier, encre et sang-de-bœuf ; Newsreader, IBM Plex Sans et IBM Plex Mono), plus des composants HTML échappés :
  - liste d'index façon recueil ;
  - passages présentés comme des notes en marge ;
  - citations `[Pn]` cliquables qui ouvrent le passage ;
  - tampon de vérification ;
  - trace tenue comme un registre.

  La trace se construit au fil du flux NDJSON (`api.run_agent`).
- **Tests** : `streamlit.testing.AppTest` contre l'API réelle (index de dev). Le parcours recherche → ouverture d'une affaire → onglets se rend sans exception, ainsi que les pages Agent, Observabilité et Système. Ce test a révélé un vrai bug, corrigé : la clé d'état `search` entrait en collision avec la clé du formulaire.

### DEC-020 — Observabilité

- **Date** : 2026-10-23 · **Statut** : acceptée
- **Décision** :
  - chaque événement et chaque run sont enregistrés en SQLite (`data/app.db`) ;
  - métriques réelles par run :
    - appels LLM et tokens, tels que renvoyés par Ollama (`prompt_eval_count`, `eval_count`) ;
    - appels par outil et nombre de recherches ;
    - itérations ;
    - latences du LLM, des outils et totale, ainsi que par étape ;
    - statut du vérificateur, motif d'arrêt et erreurs ;
  - agrégats par mode : `GET /api/v1/metrics` ;
  - **coût** : « non applicable (modèle local) ». Aucun chiffre n'est inventé.

### DEC-022 — Flux NDJSON robuste aux séparateurs Unicode

- **Date** : 2026-10-24 · **Statut** : acceptée
- **Problème observé** : le premier run du scénario 2 a planté côté client (`JSONDecodeError: Unterminated string`). Certains textes du corpus contiennent U+2028, U+2029 ou U+0085. `json.dumps(ensure_ascii=False)` les laisse passer tels quels, et `httpx.iter_lines()`, tout comme `str.splitlines`, les prend pour des fins de ligne. Une ligne NDJSON se retrouvait ainsi coupée en deux. Le run interrompu, `013b5452fbe6`, est resté sans métriques dans `data/app.db`.
- **Décision** : le serveur échappe ces trois caractères (`ndjson_line`, sortie JSON toujours valide). Les clients, c'est-à-dire l'UI et le script de scénarios, ne découpent le flux que sur `\n`.
- **Test** : `test_ndjson_lines_survive_unicode_line_separators`.

### DEC-023 — Multi-agents v2 : le vérificateur arbitre la suffisance

- **Date** : 2026-10-24 · **Statut** : acceptée
- **Problème observé** (comparaison v1, question C2, `docs/traces/C2_multi.md`) : 5 délégations au chercheur, 17 appels LLM, 284 s, puis abstention. Pendant ce temps, l'agent unique répondait correctement en 3 appels. Le chercheur signalait à chaque compte rendu que la réponse se trouvait dans [P1]. Mais le superviseur ne voyait que 160 caractères par passage et relançait la recherche.

  C'est un échec classique des systèmes multi-agents : « perte d'information entre agents », « ignorer l'avis d'un autre agent ».
- **Décision** :
  1. **Dossier plus riche** : le superviseur reçoit le compte rendu du chercheur, et les passages que celui-ci signale passent en tête avec 500 caractères d'extrait.
  2. **Arbitrage par le vérificateur** : une fois un dossier constitué, une nouvelle délégation sans aucun contrôle préalable est convertie en rédaction. Le vérificateur juge alors la suffisance des preuves, et c'est son rapport qui peut relancer le chercheur.
- **Test** : `test_supervisor_cannot_keep_delegating_once_a_dossier_exists`.
- **Mesure** : le mode multi est relancé sur les 8 questions avec la v2 (DEC-018). Les deux versions sont conservées dans `docs/results/`.
