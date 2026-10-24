# Trace — Hors corpus (IA) (multi)

**Question** : Un employeur peut-il licencier un salarié sur la seule base d'une évaluation produite par un algorithme d'intelligence artificielle ?

**Pourquoi cette question** : = S3b

**Comportement attendu** : abstention

Run `d05025065f36` · statut `abstained` · vérification `insufficient` · arrêt `max_iterations`

Appels LLM : 17 · outils : {'search_cases': 6, 'read_case': 1} · recherches : 6 · itérations : 5 · tokens : 48642 · latence : 208.1 s

> Validation humaine : réponse fournie par le script de scénario (`--hitl reject`).

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | superviseur | Délégation au chercheur — Le dossier est vide ; il faut trouver des preuves juridiques pour répondre à la question. | 6.3 s |
| 2 | DECISION | chercheur | Recherche dans le corpus (« licenciement algorithme intelligence artificielle évaluation automatique »). | 12.0 s |
| 3 | TOOL | agent | `search_cases({"query": "licenciement algorithme intelligence artificielle évaluation automatique", "k": 5})` |  |
| 4 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-04-13 · n° 21-19.925 | 0.0 s |
| 5 | DECISION | chercheur | Recherche dans le corpus (« licenciement IA algorithme décision automatisée transparence preuve causalité »). | 15.3 s |
| 6 | TOOL | agent | `search_cases({"query": "licenciement IA algorithme décision automatisée transparence preuve causalité", "k": 5})` |  |
| 7 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-02-01 · n° 21-24.271 | 0.0 s |
| 8 | OBSERVATION | chercheur | Compte rendu du chercheur : 10 passage(s) au dossier. Aucune décision de la Cour de cassation ou de juridictions inférieures citées dans le corpus ne traite spécifiquement de la validité juridique d'un licenciement fondé sur une évaluation produite par un algorithme d'intelligence artificielle |  |
| 9 | DECISION | superviseur | Rédaction de la synthèse — dossier constitué : la suffisance des preuves est soumise au vérificateur | 8.5 s |
| 10 | DECISION | superviseur | Synthèse rédigée à partir de 10 passage(s) : soumise au vérificateur. | 12.8 s |
| 11 | CHECK | vérificateur | Preuves insufficient — 0/2 affirmation(s) soutenue(s) ; 2 en échec sur les règles (citation absente, inventée ou incomplète). | 0.0 s |
| 12 | DECISION | superviseur | Délégation au chercheur — Le corpus actuel ne contient aucune décision traitant explicitement du licenciement basé sur une évaluation par IA ; il faut élargir la recherche aux termes techniques spécifiques pour confirmer l'absence totale de jurisprudence ou trouver un précédent inédit. | 11.0 s |
| 13 | DECISION | chercheur | Recherche dans le corpus (« intelligence artificielle algorithme automatique licenciement évaluation décision »). | 9.0 s |
| 14 | TOOL | agent | `search_cases({"query": "intelligence artificielle algorithme automatique licenciement évaluation décision", "k": 5})` |  |
| 15 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2022-09-21 · n° 19-12.568 | 0.0 s |
| 16 | OBSERVATION | chercheur | Compte rendu du chercheur : 13 passage(s) au dossier. Aucune décision de la Cour de cassation (Chambre sociale) ne contient les mots-clés 'intelligence artificielle', 'algorithme', 'automatique' ou 'IA' associés aux notions de 'licenciement', 'évaluation' ou 'décision'. Les résultats retournés |  |
| 17 | DECISION | superviseur | Délégation au chercheur — Le corpus actuel ne contient aucune décision traitant explicitement du lien entre IA/algorithme et licenciement ; il faut élargir ou approfondir la recherche pour trouver des passages pertinents ou confirmer l'absence totale de jurisprudence sur ce sujet spécifique. | 11.0 s |
| 18 | DECISION | chercheur | Recherche dans le corpus (« intelligence artificielle algorithme licenciement évaluation décision automatisée transparence »). | 10.1 s |
| 19 | TOOL | agent | `search_cases({"query": "intelligence artificielle algorithme licenciement évaluation décision automatisée transparence", "k": 5})` |  |
| 20 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-02-01 · n° 21-24.271 | 0.0 s |
| 21 | DECISION | chercheur | Recherche dans le corpus (« licenciement algorithme évaluation performance salarié »). | 16.0 s |
| 22 | TOOL | agent | `search_cases({"query": "licenciement algorithme évaluation performance salarié", "k": 5})` |  |
| 23 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2022-02-16 · n° 20-16.171 | 0.0 s |
| 24 | OBSERVATION | chercheur | Compte rendu du chercheur : 21 passage(s) au dossier. Aucune décision de la Chambre sociale de la Cour de cassation postérieure à 2018 ne contient les termes 'intelligence artificielle', 'algorithme' ou 'IA' associés aux mots-clés 'licenciement', 'évaluation', 'décision automatisée' ou 'transp |  |
| 25 | DECISION | superviseur | Délégation au chercheur — Le chercheur doit élargir sa recherche au-delà des résultats négatifs actuels pour confirmer l'absence totale de jurisprudence spécifique sur ce sujet dans la base de données disponible. | 11.6 s |
| 26 | DECISION | chercheur | Recherche dans le corpus (« intelligence artificielle algorithme licenciement évaluation transparence »). | 9.5 s |
| 27 | TOOL | agent | `search_cases({"query": "intelligence artificielle algorithme licenciement évaluation transparence", "k": 5})` |  |
| 28 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-02-01 · n° 21-24.271 | 0.0 s |
| 29 | DECISION | chercheur | Lecture détaillée de la décision 63da1185b78bc005de6ccd13. | 26.3 s |
| 30 | TOOL | agent | `read_case({"case_id": "63da1185b78bc005de6ccd13"})` |  |
| 31 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-02-01 · n° 21-24.271 | 0.0 s |
| 32 | OBSERVATION | chercheur | Compte rendu du chercheur : 32 passage(s) au dossier. Aucune décision pertinente n'a été trouvée dans le corpus local postérieure à 2018 traitant spécifiquement de la validité d'un licenciement basé sur une évaluation automatique ou l'obligation de transparence envers un algorithme d'intellige |  |
| 33 | HUMAN | agent | Validation humaine demandée : prolonger le budget. |  |
| 34 | HUMAN | agent | Décision humaine : refusée. |  |
| 35 | FINAL | agent | Abstention — le budget d'itérations est épuisé sans preuve suffisante. |  |

## Réponse finale

Je ne peux pas répondre de manière fiable à partir du corpus : le budget d'itérations est épuisé sans preuve suffisante.

## Limites

- Non établi : Aucun texte ne mentionne l'utilisation d'algorithmes d'intelligence artificielle pour évaluer les salariés ou justifier un licenciement.
- Non établi : Les décisions citées traitent uniquement d'évaluations annuelles formelles, de harcèlement moral, de lanceurs d'alerte ou d'inaptitude physique sans faire référence à des outils automatisés.
