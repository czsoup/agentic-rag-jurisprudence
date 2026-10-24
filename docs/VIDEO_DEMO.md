# Scénario de la vidéo de démonstration (≈ 7 min)

> Ce document **prépare** l'enregistrement : la vidéo n'a été ni enregistrée ni publiée. Les questions proposées sont celles des scénarios de `docs/results/questions.json`, dont les traces réelles sont dans `docs/traces/`. Les temps d'exécution indiqués sont ceux mesurés lors des runs enregistrés. Ils varient d'un run à l'autre : couper au montage les attentes du modèle.

## Avant d'enregistrer

```bash
ollama ps                      # Ollama démarré
make api                       # terminal 1
make ui                        # terminal 2 → http://localhost:8501
curl -s localhost:8000/health  # "status": "ok"
```

- Réinitialiser la session (page *Agent* → « Réinitialiser la session ») pour partir d'une mémoire vide.
- Faire un run « à blanc » juste avant, pour que le modèle soit déjà chargé en mémoire : le premier appel est plus lent.
- Navigateur en plein écran, zoom à 90 %, et un second onglet ouvert sur `docs/diagrams` (aperçu Mermaid) ou sur le rapport.

## Séquences

| # | Minutage | Actions | Commandes | Ce qui doit être visible | Commentaire oral suggéré |
|---|---|---|---|---|---|
| 1 | 0:00–0:30 | Titre, puis page *Système* | — | Les 4 tampons verts : Ollama, qwen3.5:9b, embeddings, index ; manifeste avec 4 000 décisions et la révision du dataset | « Un assistant de recherche en jurisprudence qui tourne entièrement en local. Le corpus, ce sont 4 000 arrêts de la Cour de cassation, avec une provenance figée. » |
| 2 | 0:30–1:15 | Schéma d'architecture (`01_architecture.mmd`), puis boucle (`03_agent_loop.mmd`) | — | Les 3 services et les couches ; les nœuds decide, act, verify, human_gate | « L'UI ne parle qu'à l'API. Le modèle propose une action ; c'est le code qui l'autorise, l'exécute et décide de s'arrêter. » |
| 3 | 1:15–1:45 | Lancement réel | `make api`, `make ui` | Les deux terminaux, puis la page d'accueil | « Deux commandes. Ollama tourne en natif pour profiter du GPU. » |
| 4 | 1:45–2:45 | *Recherche & lecture* : requête, liste, « Consulter », onglet *Texte*, onglet *Résumé* | — | Liste façon index de recueil, scores, zones de l'arrêt, résumé faits / procédure / décision avec des citations cliquables | « Le socle RAG : recherche hybride BM25 et dense. Le score sert à classer, ce n'est pas une preuve. Chaque phrase du résumé renvoie à son passage. » |
| 5 | 2:45–3:45 | *Agent* : question du **scénario 1**, mode agent unique | — | La trace qui se remplit en direct (DECISION, TOOL, OBSERVATION, CHECK, FINAL), le tampon « Preuves suffisantes », un clic sur [P1] qui ouvre le passage | « Une seule recherche suffit : l'agent ne multiplie pas les étapes. Le vérificateur contrôle chaque affirmation avant que je voie la réponse. » |
| 6 | 3:45–4:45 | Question du **scénario 2** | — | `read_case` dans la trace ; CHECK, éventuellement un premier échec puis la relecture | « Ici, il faut d'abord trouver l'affaire, puis la lire. Quand une affirmation n'est pas prouvée, le vérificateur renvoie l'agent chercher. » |
| 7 | 4:45–5:45 | Question du **scénario 3** | — | Reformulations successives, CHECK insuffisant, panneau « Validation humaine requise », clic sur *Refuser*, abstention motivée | « Le corpus ne contient pas la réponse. L'agent reformule, puis atteint sa limite. Il me demande s'il peut continuer ; je refuse, et il s'abstient au lieu d'inventer. » |
| 8 | 5:45–6:15 | Mémoire et multi-agents | — | Question de suivi (« Et quelle est la solution de cette affaire ? ») sans resélection ; panneau *Mémoire* ; un run en mode multi-agents avec les agents dans la trace | « La session garde l'affaire en cours. En multi-agents, un superviseur délègue au chercheur et au vérificateur. » |
| 9 | 6:15–6:45 | *Observabilité* et export | — | Tableau par mode (appels LLM, latence, statut) ; « Exporter le dossier » avec sa confirmation | « Chaque run est mesuré. Le coût est nul car le modèle est local. L'export attend une confirmation explicite. » |
| 10 | 6:45–7:15 | Comparaison avec le RAG statique | rapport §16 | Tableau de comparaison mesuré | « Le RAG statique est plus rapide sur les questions simples ; l'agent apporte de la valeur quand il faut lire ou relancer. » |
| 11 | 7:15–7:30 | Conclusion | — | Matrice de conformité | « Tout est reproductible avec `make`, et toutes les traces sont dans le dépôt. » |

## Après l'enregistrement

- Vérifier qu'aucune information personnelle n'apparaît à l'écran : chemins du système de fichiers, onglets ouverts.
- La publication (plateforme, visibilité) et le lien à rendre restent à décider.
