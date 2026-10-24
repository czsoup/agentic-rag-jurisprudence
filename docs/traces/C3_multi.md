# Trace — Indemnité spécifique de rupture conventionnelle (multi)

**Question** : L'indemnité spécifique de rupture conventionnelle peut-elle être inférieure à l'indemnité conventionnelle de licenciement ?

**Pourquoi cette question** : Chambre sociale, 10 janvier 2024, n° 22-19.165 (publié).

**Comportement attendu** : réponse directe

Run `717c2733c634` · statut `partial` · vérification `insufficient` · arrêt `max_iterations`

Appels LLM : 16 · outils : {'search_cases': 4, 'read_case': 2} · recherches : 4 · itérations : 5 · tokens : 36734 · latence : 267.9 s

> Validation humaine : réponse fournie par le script de scénario (`--hitl reject`).

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | superviseur | Délégation au chercheur — Le dossier est vide ; il faut trouver des passages juridiques prouvant la relation entre ces deux indemnités. | 5.9 s |
| 2 | DECISION | chercheur | Recherche dans le corpus (« rupture conventionnelle indemnité spécifique L1237-5 inférieure indemnité licenciement conventionnel »). | 9.8 s |
| 3 | TOOL | agent | `search_cases({"query": "rupture conventionnelle indemnité spécifique L1237-5 inférieure indemnité licenciement conventionnel", "k": 5})` |  |
| 4 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.0 s |
| 5 | OBSERVATION | chercheur | Compte rendu du chercheur : 5 passage(s) au dossier. Décisions pertinentes : 659e41095537980008846f77 [P1], 66728100f7ab5c00087309df [P5]. |  |
| 6 | DECISION | superviseur | Rédaction de la synthèse — Les extraits P1 et P5 confirment que l'indemnité spécifique de rupture conventionnelle ne peut pas être inférieure à l'indemnité conventionnelle de licenciement lorsque celle-ci est supérieure à l'indemnité légale. | 5.4 s |
| 7 | DECISION | superviseur | Synthèse rédigée à partir de 5 passage(s) : soumise au vérificateur. | 10.8 s |
| 8 | CHECK | vérificateur | Preuves insufficient — 1/4 affirmation(s) soutenue(s) ; 2 en échec sur les règles (citation absente, inventée ou incomplète) ; 1 non établie(s) par le juge. | 11.7 s |
| 9 | DECISION | superviseur | Délégation au chercheur — Il manque une preuve concernant les indemnités de départ à la retraite (articles 22.3 et 22.4) mentionnée dans le dernier contrôle comme non établie. | 10.9 s |
| 10 | DECISION | chercheur | Recherche dans le corpus (« indemnité spécifique rupture conventionnelle inférieure indemnité conventionnelle licenciement »). | 15.1 s |
| 11 | TOOL | agent | `search_cases({"query": "indemnité spécifique rupture conventionnelle inférieure indemnité conventionnelle licenciement", "k": 5})` |  |
| 12 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.0 s |
| 13 | OBSERVATION | chercheur | Compte rendu du chercheur : 6 passage(s) au dossier. Décisions pertinentes : case_id=659e41095537980008846f77 [P1]. L'indemnité spécifique de rupture conventionnelle ne peut pas être inférieure à l'indemnité conventionnelle de licenciement lorsque celle-ci est supérieure à l'indemnité légale. |  |
| 14 | DECISION | superviseur | Délégation au chercheur — Le dossier actuel manque de preuves directes sur le fond du droit (article L. 1237-13) et nécessite des décisions confirmant l'invalidité des clauses inférieures au seuil conventionnel supérieur au légal. | 11.4 s |
| 15 | DECISION | chercheur | Recherche dans le corpus (« article L. 1237-13 code du travail indemnité spécifique rupture conventionnelle inférieure à l'indemnité conventionnelle de licenciement alinéa 2 avenant 18 mai 2009 »). | 12.0 s |
| 16 | TOOL | agent | `search_cases({"query": "article L. 1237-13 code du travail indemnité spécifique rupture conventionnelle inférieure à l'indemnité conventionnelle de licenciement alinéa 2 avenant 18 mai 2009", "k": 5})` |  |
| 17 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.1 s |
| 18 | DECISION | chercheur | Lecture détaillée de la décision 659e41095537980008846f77. | 36.7 s |
| 19 | DECISION | chercheur | Lecture détaillée de la décision 66728100f7ab5c00087309df. | 36.7 s |
| 20 | TOOL | agent | `read_case({"case_id": "659e41095537980008846f77", "focus": "article L. 1237-13 indemnité spécifique rupture conventionnelle inférieure à l'indemnité conventionnelle de licenciement"})` |  |
| 21 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.0 s |
| 22 | TOOL | agent | `read_case({"case_id": "66728100f7ab5c00087309df", "focus": "article L. 1237-13 indemnité spécifique rupture conventionnelle inférieure à l'indemnité conventionnelle de licenciement"})` |  |
| 23 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2024-06-19 · n° 22-23.143 | 0.0 s |
| 24 | OBSERVATION | chercheur | Compte rendu du chercheur : 21 passage(s) au dossier. Décisions pertinentes (case_id) : 659e41095537980008846f77 [P1], 66728100f7ab5c00087309df [P5]. |  |
| 25 | DECISION | superviseur | Délégation au chercheur — Le dossier actuel ne permet pas de répondre définitivement car les passages existants confirment la règle d'infériorité interdite mais n'établissent pas explicitement l'existence ou la validité d'une indemnité inférieure dans un cas où l'indemnité conventionnelle est supérieure. | 12.6 s |
| 26 | DECISION | chercheur | Recherche dans le corpus (« indemnité rupture conventionnelle inférieure indemnité conventionnelle licenciement seuil L. 1237-13 C. trav. »). | 11.1 s |
| 27 | TOOL | agent | `search_cases({"query": "indemnité rupture conventionnelle inférieure indemnité conventionnelle licenciement seuil L. 1237-13 C. trav.", "k": 5})` |  |
| 28 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-01-10 · n° 22-19.165 | 0.0 s |
| 29 | OBSERVATION | chercheur | Compte rendu du chercheur : 21 passage(s) au dossier. Décisions pertinentes : 659e41095537980008846f77 [P1], 66728100f7ab5c00087309df [P5]. La Cour de cassation confirme que l'indemnité spécifique de rupture conventionnelle ne peut pas être inférieure à l'indemnité conventionnelle de licenciem |  |
| 30 | HUMAN | agent | Validation humaine demandée : prolonger le budget. |  |
| 31 | HUMAN | agent | Décision humaine : refusée. |  |
| 32 | FINAL | agent | Réponse partielle — 1 passage(s) cité(s). |  |

## Réponse finale

La convention de rupture définit donc le montant de cette indemnité spécifique, qui doit respecter ce plancher conventionnel ou légal selon le cas [P5].

## Passages cités

- **[P5]** Cour de cassation · Chambre sociale · 2024-06-19 · n° 22-23.143 — Motivations (`66728100f7ab5c00087309df#motivations-0`)
  > Réponse de la Cour 7. Selon l'article L. 1237-12 du code du travail, les parties au contrat conviennent du principe d'une rupture conventionnelle lors d'un ou plusieurs entretiens. 8. Aux termes de l'article L. 1237-13 du même code, la convention de rupture définit les conditions de celle-ci, notamment le montant de l'indemnité spécifique de rupture conventionnelle qui ne peut pas être inférieur à celui de l'indemnité prévue à l'article L. 1234-9. Elle fixe la date de rupture du contrat de travail, qui ne peut intervenir avant le lendemain du jour de l'homologation. A compter de la date de sa signature par les deux parties, chacune d'entre elles dispose d'un délai de quinze jours calendaires

## Limites

- Réponse partielle : seules les affirmations vérifiées sont conservées.
- Non établi : Non, selon le passage P1, l'indemnité spécifique de rupture conventionnelle ne peut pas être d'un montant inférieur à celui de l'indemnité conventionnelle de licenciement lorsque celle-ci est supérieure à l'indemnité légale.
- Non établi : Cette règle s'applique également aux indemnités de départ à la retraite prévues par les articles 22.3 et 22.4, qui ne peuvent pas être inférieures à l'indemnité légale de licenciement [P2].
- Non établi : En conséquence, toute stipulation contractuelle visant à fixer une indemnité inférieure à ces seuils serait contraire aux dispositions légales et conventionnelles applicables.
- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
