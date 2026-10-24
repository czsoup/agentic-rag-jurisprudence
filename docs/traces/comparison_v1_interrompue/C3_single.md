# Trace — Indemnité spécifique de rupture conventionnelle (single)

**Question** : L'indemnité spécifique de rupture conventionnelle peut-elle être inférieure à l'indemnité conventionnelle de licenciement ?

**Pourquoi cette question** : Chambre sociale, 10 janvier 2024, n° 22-19.165 (publié).

**Comportement attendu** : réponse directe

Run `5b505ddfc4fd` · statut `error` · vérification `insufficient` · arrêt `error`

Appels LLM : 6 · outils : {'search_cases': 1, 'read_case': 1} · recherches : 1 · itérations : 4 · tokens : 17449 · latence : 1073.5 s

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | agent | Aucune preuve collectée : recherche documentaire nécessaire (« indemnité rupture conventionnelle inférieure indemnité licenciement conventionnelle »). | 8.0 s |
| 2 | TOOL | agent | `search_cases({"query": "indemnité rupture conventionnelle inférieure indemnité licenciement conventionnelle", "k": 5})` |  |
| 3 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.0 s |
| 4 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 21.9 s |
| 5 | CHECK | vérificateur | Preuves insufficient — 2/4 affirmation(s) soutenue(s) ; 2 en échec sur les règles (citation absente, inventée ou incomplète). | 14.1 s |
| 6 | DECISION | agent | Décision repérée (Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165) : lecture détaillée de ses passages. | 10.3 s |
| 7 | TOOL | agent | `read_case({"case_id": "659e41095537980008846f77", "focus": "indemnité rupture conventionnelle indemnité licenciement"})` |  |
| 8 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.0 s |
| 9 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 36.3 s |
| 10 | CHECK | vérificateur | Preuves insufficient — 2/4 affirmation(s) soutenue(s) ; 1 en échec sur les règles (citation absente, inventée ou incomplète) ; 1 non établie(s) par le juge. | 15.9 s |
| 11 | ERROR | agent | Appel au modèle impossible : Ollama n'a pas répondu à temps (/api/chat) |  |
| 12 | FINAL | agent | Abstention — une erreur non récupérable a interrompu la recherche. |  |

## Réponse finale

Je ne peux pas répondre de manière fiable à partir du corpus : une erreur non récupérable a interrompu la recherche.

## Limites

- Non établi : L'article L. 1237-13 du code du travail prévoit cette condition minimale pour l'indemnité spécifique de rupture conventionnelle [P1].
- Non établi : La Cour de cassation a confirmé ce principe dans un arrêt publié au Bulletin en janvier 2024 [P1].
