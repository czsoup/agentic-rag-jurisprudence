# Trace — Indemnité spécifique de rupture conventionnelle (single)

**Question** : L'indemnité spécifique de rupture conventionnelle peut-elle être inférieure à l'indemnité conventionnelle de licenciement ?

**Pourquoi cette question** : Chambre sociale, 10 janvier 2024, n° 22-19.165 (publié).

**Comportement attendu** : réponse directe

Run `a4d701aeccfa` · statut `partial` · vérification `insufficient` · arrêt `max_iterations`

Appels LLM : 7 · outils : {'search_cases': 2, 'read_case': 1} · recherches : 2 · itérations : 5 · tokens : 23943 · latence : 122.4 s

> Validation humaine : réponse fournie par le script de scénario (`--hitl reject`).

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | agent | Aucune preuve collectée : recherche documentaire nécessaire (« indemnité rupture conventionnelle inférieure indemnité licenciement conventionnelle »). | 8.0 s |
| 2 | TOOL | agent | `search_cases({"query": "indemnité rupture conventionnelle inférieure indemnité licenciement conventionnelle", "k": 5})` |  |
| 3 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.1 s |
| 4 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 21.8 s |
| 5 | CHECK | vérificateur | Preuves insufficient — 2/4 affirmation(s) soutenue(s) ; 2 en échec sur les règles (citation absente, inventée ou incomplète). | 14.1 s |
| 6 | DECISION | agent | Décision repérée (Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165) : lecture détaillée de ses passages. | 10.3 s |
| 7 | TOOL | agent | `read_case({"case_id": "659e41095537980008846f77", "focus": "indemnité rupture conventionnelle indemnité licenciement"})` |  |
| 8 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.0 s |
| 9 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 36.0 s |
| 10 | CHECK | vérificateur | Preuves insufficient — 2/4 affirmation(s) soutenue(s) ; 1 en échec sur les règles (citation absente, inventée ou incomplète) ; 1 non établie(s) par le juge. | 15.7 s |
| 11 | DECISION | agent | Vérification insuffisante : nouvelle recherche reformulée (« indemnité rupture conventionnelle inférieure indemnité licenciement article L. 1237-13 »). | 16.3 s |
| 12 | TOOL | agent | `search_cases({"query": "indemnité rupture conventionnelle inférieure indemnité licenciement article L. 1237-13", "k": 5})` |  |
| 13 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.0 s |
| 14 | HUMAN | agent | Validation humaine demandée : prolonger le budget. |  |
| 15 | HUMAN | agent | Décision humaine : refusée. |  |
| 16 | FINAL | agent | Réponse partielle — 1 passage(s) cité(s). |  |

## Réponse finale

Non, l'indemnité spécifique de rupture conventionnelle ne peut pas être inférieure à l'indemnité conventionnelle de licenciement lorsque celle-ci est supérieure à l'indemnité légale de licenciement [P1]. Cette règle découle de l'avenant du 18 mai 2009 à l'accord national interprofessionnel du 11 janvier 2008 [P1].

## Passages cités

- **[P1]** Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 — Motivations (`659e41095537980008846f77#motivations-1`)
  > Réponse de la Cour 6. Selon l'avenant du 18 mai 2009 à l'accord national interprofessionnel du 11 janvier 2008, l'indemnité spécifique de rupture conventionnelle prévue par l'article L. 1237-13 du code du travail ne peut pas être d'un montant inférieur à celui de l'indemnité conventionnelle de licenciement, lorsque celle-ci est supérieure à l'indemnité légale de licenciement. 7. L'article 14-3 de l'avenant n° 3 du 16 juin 1955 à la convention collective nationale des industries chimiques et connexes du 30 décembre 1952, relatif aux ingénieurs et cadres, prévoit que la base de calcul de l'indemnité de licenciement est la rémunération totale mensuelle gagnée par le cadre pendant le mois précéd

## Limites

- Réponse partielle : seules les affirmations vérifiées sont conservées.
- Non établi : L'article L. 1237-13 du code du travail prévoit cette condition minimale pour l'indemnité spécifique de rupture conventionnelle [P1].
- Non établi : La Cour de cassation a confirmé ce principe dans un arrêt publié au Bulletin en janvier 2024 [P1].
- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
