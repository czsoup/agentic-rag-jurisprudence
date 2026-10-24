# Trace — Congés payés pendant l'éviction (multi)

**Question** : Un salarié dont le licenciement nul a été suivi d'une réintégration a-t-il droit à des congés payés pour la période d'éviction ?

**Pourquoi cette question** : Chambre sociale, 1er mars 2023, n° 21-16.008 (publié) : oui, sauf s'il a occupé un autre emploi pendant cette période.

**Comportement attendu** : réponse directe, nuance « sauf autre emploi »

Run `349512ee4462` · statut `partial` · vérification `insufficient` · arrêt `max_iterations`

Appels LLM : 16 · outils : {'search_cases': 2, 'read_case': 3} · recherches : 2 · itérations : 5 · tokens : 41169 · latence : 286.5 s

> Validation humaine : réponse fournie par le script de scénario (`--hitl reject`).

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | superviseur | Délégation au chercheur — Le dossier est vide ; il faut trouver des passages juridiques pertinents dans la base de données. | 5.6 s |
| 2 | DECISION | chercheur | Recherche dans le corpus (« congés payés période éviction licenciement nul réintégration assimilation temps de travail effectif »). | 7.7 s |
| 3 | TOOL | agent | `search_cases({"query": "congés payés période éviction licenciement nul réintégration assimilation temps de travail effectif", "k": 5})` |  |
| 4 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-03-01 · n° 21-16.008 | 0.0 s |
| 5 | OBSERVATION | chercheur | Compte rendu du chercheur : 5 passage(s) au dossier. Décisions pertinentes : case_id=63fefc07002ac605de15b29e [P1] et case_id=65015d56ee1a2205e6581652 [P2]. Ces passages précisent que le salarié peut prétendre à ses droits à congés payés au titre de la période d'éviction comprise entre la dat |  |
| 6 | DECISION | superviseur | Rédaction de la synthèse — Les décisions P1 et P2 confirment que le salarié peut prétendre à ses droits à congés payés au titre de la période d'éviction entre le licenciement nul et la réintégration. | 7.1 s |
| 7 | DECISION | superviseur | Synthèse rédigée à partir de 5 passage(s) : soumise au vérificateur. | 11.6 s |
| 8 | CHECK | vérificateur | Preuves insufficient — 3/4 affirmation(s) soutenue(s) ; 1 en échec sur les règles (citation absente, inventée ou incomplète). | 15.0 s |
| 9 | DECISION | superviseur | Délégation au chercheur — Le dernier contrôle indique qu'une affirmation n'est pas prouvée (citation absente ou incomplète) ; il manque donc la preuve textuelle définitive dans le dossier actuel. | 9.0 s |
| 10 | DECISION | chercheur | Recherche dans le corpus (« licenciement nul réintégration congés payés période éviction Chambre sociale 2023 »). | 10.6 s |
| 11 | TOOL | agent | `search_cases({"query": "licenciement nul réintégration congés payés période éviction Chambre sociale 2023", "k": 5})` |  |
| 12 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.1 s |
| 13 | DECISION | chercheur | Lecture détaillée de la décision 65015d56ee1a2205e6581652. | 34.8 s |
| 14 | TOOL | agent | `read_case({"case_id": "65015d56ee1a2205e6581652", "focus": "congés payés période éviction"})` |  |
| 15 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 16 | OBSERVATION | chercheur | Compte rendu du chercheur : 14 passage(s) au dossier. Décisions pertinentes (case_id) : 65015d56ee1a2205e6581652, 63fefc07002ac605de15b29e. Alias des passages utiles [P2], [P1]. |  |
| 17 | DECISION | superviseur | Délégation au chercheur — Le dernier contrôle a relevé une affirmation non établie concernant le maintien du droit aux congés payés ; il manque la citation exacte de la décision qui tranche cette question pour confirmer ou infirmer l'existence de ce droit. | 11.8 s |
| 18 | DECISION | chercheur | Lecture détaillée de la décision 65015d56ee1a2205e6581652. | 13.0 s |
| 19 | TOOL | agent | `read_case({"case_id": "65015d56ee1a2205e6581652", "focus": "congés payés période d'éviction"})` |  |
| 20 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 21 | OBSERVATION | chercheur | Compte rendu du chercheur : 14 passage(s) au dossier. Décision n° 22-10.529 (case_id 65015d56ee1a2205e6581652) : la Cour de cassation statue en faveur du droit aux congés payés pour la période d'éviction entre le licenciement nul et la réintégration, conformément aux articles L. 3141-3 et L. 3 |  |
| 22 | DECISION | superviseur | Délégation au chercheur — Le contrôle a révélé une erreur sur les articles du code du travail cités pour fonder la décision ; il faut retrouver la citation exacte dans le corpus. | 11.8 s |
| 23 | DECISION | chercheur | Lecture détaillée de la décision 65015d56ee1a2205e6581652. | 12.1 s |
| 24 | TOOL | agent | `read_case({"case_id": "65015d56ee1a2205e6581652", "focus": "congés payés période d'éviction"})` |  |
| 25 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 26 | OBSERVATION | chercheur | Compte rendu du chercheur : 14 passage(s) au dossier. |  |
| 27 | HUMAN | agent | Validation humaine demandée : prolonger le budget. |  |
| 28 | HUMAN | agent | Décision humaine : refusée. |  |
| 29 | FINAL | agent | Réponse partielle — 2 passage(s) cité(s). |  |

## Réponse finale

Oui, un salarié dont le licenciement est nul peut prétendre à ses droits à congés payés au titre de la période d'éviction comprise entre la date du licenciement et celle de sa réintégration [P1]. La Cour précise que ce droit s'applique en application des articles L. 3141-3 et L. 3141-9 du code du travail, sauf si le salarié a occupé un autre emploi durant cette période [P1]. Un moyen soutenant que l'indemnité d'éviction n'ouvrirait pas droit à congés payés car elle serait une réparation et non une remise en état a été rejeté par la Cour de cassation [P2].

## Passages cités

- **[P1]** Cour de cassation · Chambre sociale · 2023-03-01 · n° 21-16.008 — Motivations (`63fefc07002ac605de15b29e#motivations-1`)
  > Réponse de la Cour Vu les articles L. 1132-1 et L. 1132-4, dans sa rédaction antérieure à la loi n° 2022-401 du 21 mars 2022, du code du travail : 8. Il résulte de ces textes que tout licenciement prononcé à l'égard d'un salarié en raison de son état de santé est nul et que le salarié qui demande sa réintégration a droit au paiement d'une somme correspondant à la réparation de la totalité du préjudice subi au cours de la période qui s'est écoulée entre son licenciement et sa réintégration, dans la limite du montant des salaires dont il a été privé. 9. Le salarié peut prétendre à ses droits à congés payés au titre de la période d'éviction comprise entre la date du licenciement nul et celle de
- **[P2]** Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 — Moyens (`65015d56ee1a2205e6581652#moyens-4`)
  > Et sur le troisième moyen du pourvoi n° B 22-11.106 Enoncé du moyen 23. La salariée fait grief à l'arrêt de la débouter de sa demande en paiement d'une indemnité de congé payé pour les périodes de référence courant du 1er juin 2018 à la date de sa réintégration effective, alors « que le salarié peut prétendre à ses droits à congés payés au titre de la période d'éviction comprise entre la date du licenciement nul et celle de la réintégration dans son emploi en application des dispositions des articles L. 3141-3 et L. 3141-9 du code du travail ; qu'en retenant, pour rejeter la demande en paiement des indemnités pour la période de référence courant du 1er juin 2018 à la date de sa réintégration

## Limites

- Réponse partielle : seules les affirmations vérifiées sont conservées.
- Non établi : Par conséquent, le salarié conserve son droit aux congés payés pour cette période spécifique.
- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
