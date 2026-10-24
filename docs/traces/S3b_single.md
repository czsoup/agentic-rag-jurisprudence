# Trace — Scénario 3b — information absente du corpus (single)

**Question** : Un employeur peut-il licencier un salarié sur la seule base d'une évaluation produite par un algorithme d'intelligence artificielle ?

**Pourquoi cette question** : Aucun passage de l'index ne contient « intelligence artificielle » ni « algorithme » (vérifié par requête SQL sur les 27 249 passages), alors que l'index contient de nombreuses décisions de licenciement, donc des quasi-réponses trompeuses.

**Comportement attendu** : Recherches reformulées, vérification insuffisante, limite d'itérations, demande de prolongation (refusée par le script), puis abstention motivée, sans affirmation non sourcée.

Run `523decbef152` · statut `abstained` · vérification `None` · arrêt `max_iterations`

Appels LLM : 5 · outils : {'search_cases': 5} · recherches : 5 · itérations : 5 · tokens : 29774 · latence : 69.6 s

> Validation humaine : réponse fournie par le script de scénario (`--hitl reject`).

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | agent | Aucune preuve collectée : recherche documentaire nécessaire (« licenciement intelligence artificielle algorithme évaluation salarié »). | 9.5 s |
| 2 | TOOL | agent | `search_cases({"query": "licenciement intelligence artificielle algorithme évaluation salarié", "k": 5})` |  |
| 3 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2022-02-16 · n° 20-14.969 | 0.0 s |
| 4 | DECISION | agent | Résultats précédents insuffisants : requête reformulée (« intelligence artificielle algorithme licenciement cause réelle sérieuse »). | 13.5 s |
| 5 | TOOL | agent | `search_cases({"query": "intelligence artificielle algorithme licenciement cause réelle sérieuse", "k": 5})` |  |
| 6 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-10-18 · n° 22-18.852 | 0.0 s |
| 7 | DECISION | agent | Résultats précédents insuffisants : requête reformulée (« évaluation automatisée système algorithmique licenciement salarié »). | 14.3 s |
| 8 | TOOL | agent | `search_cases({"query": "évaluation automatisée système algorithmique licenciement salarié", "k": 5})` |  |
| 9 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-03-08 · n° 21-20.797 | 0.0 s |
| 10 | DECISION | agent | Résultats précédents insuffisants : requête reformulée (« notation automatique outil numérique évaluation salarié licenciement »). | 14.9 s |
| 11 | TOOL | agent | `search_cases({"query": "notation automatique outil numérique évaluation salarié licenciement", "k": 5})` |  |
| 12 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2022-10-19 · n° 21-15.533 | 0.0 s |
| 13 | DECISION | agent | Résultats précédents insuffisants : requête reformulée (« système automatisé outil numérique évaluation salarié licenciement cause réelle sérieuse »). | 17.1 s |
| 14 | TOOL | agent | `search_cases({"query": "système automatisé outil numérique évaluation salarié licenciement cause réelle sérieuse", "k": 5})` |  |
| 15 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-06-12 · n° 23-13.522 | 0.0 s |
| 16 | HUMAN | agent | Validation humaine demandée : prolonger le budget. |  |
| 17 | HUMAN | agent | Décision humaine : refusée. |  |
| 18 | FINAL | agent | Abstention — le budget d'itérations est épuisé sans preuve suffisante. |  |

## Réponse finale

Je ne peux pas répondre de manière fiable à partir du corpus : le budget d'itérations est épuisé sans preuve suffisante.
