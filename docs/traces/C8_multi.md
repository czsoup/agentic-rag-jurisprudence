# Trace — Renonciation à la non-concurrence (termes juridiques) (multi)

**Question** : En cas de rupture conventionnelle, jusqu'à quand l'employeur peut-il renoncer à la clause de non-concurrence ?

**Pourquoi cette question** : Même arrêt que C6, formulé en termes juridiques : isole l'effet de la formulation.

**Comportement attendu** : réponse directe

Run `6180060ee3e0` · statut `answered` · vérification `sufficient` · arrêt `answered`

Appels LLM : 7 · outils : {'search_cases': 1, 'read_case': 2} · recherches : 1 · itérations : 2 · tokens : 21202 · latence : 105.6 s

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | superviseur | Délégation au chercheur — Le dossier est vide ; il faut trouver des passages juridiques pour répondre. | 5.2 s |
| 2 | DECISION | chercheur | Recherche dans le corpus (« rupture conventionnelle clause non-concurrence renonciation délai postérieur validité »). | 8.2 s |
| 3 | TOOL | agent | `search_cases({"query": "rupture conventionnelle clause non-concurrence renonciation délai postérieur validité", "k": 5})` |  |
| 4 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755 | 0.0 s |
| 5 | DECISION | chercheur | Lecture détaillée de la décision 61f0f2387743e3330ccf075f. | 36.8 s |
| 6 | DECISION | chercheur | Lecture détaillée de la décision 6684e95fa0de54ff609f7aab. | 36.8 s |
| 7 | TOOL | agent | `read_case({"case_id": "61f0f2387743e3330ccf075f", "focus": "renonciation clause non-concurrence délai rupture conventionnelle"})` |  |
| 8 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755 | 0.0 s |
| 9 | TOOL | agent | `read_case({"case_id": "6684e95fa0de54ff609f7aab", "focus": "renonciation clause non-concurrence délai rupture conventionnelle"})` |  |
| 10 | OBSERVATION | agent | 7 passage(s) lus dans Cour de cassation · Chambre sociale · 2024-07-03 · n° 22-17.452 | 0.0 s |
| 11 | OBSERVATION | chercheur | Compte rendu du chercheur : 18 passage(s) au dossier. Décisions pertinentes : case_id=61f0f2387743e3330ccf075f [P9, P1] et case_id=6684e95fa0de54ff609f7aab [P2]. |  |
| 12 | DECISION | superviseur | Rédaction de la synthèse — Les décisions analysées établissent que le délai de renonciation s'étend jusqu'au jour où le salarié quitte l'entreprise, indépendamment des stipulations contractuelles ou de l'absence de préavis. | 9.2 s |
| 13 | DECISION | superviseur | Synthèse rédigée à partir de 10 passage(s) : soumise au vérificateur. | 13.8 s |
| 14 | CHECK | vérificateur | Preuves sufficient — 4 affirmation(s), toutes soutenues par les passages cités. | 19.6 s |
| 15 | FINAL | agent | Réponse vérifiée — 1 passage(s) cité(s). |  |

## Réponse finale

En matière de rupture conventionnelle, l'employeur qui entend renoncer à l'exécution de la clause de non-concurrence doit le faire au plus tard à la date de rupture fixée par la convention [P9]. Cette obligation s'impose nonobstant toutes stipulations ou dispositions contraires contenues dans le contrat ou les accords applicables [P9]. La Cour justifie cette solution par le fait que le salarié ne peut être laissé dans l'incertitude quant à l'étendue de sa liberté de travailler après son départ effectif [P9]. Cette règle s'applique également lorsque la rupture résulte d'une adhésion au contrat de sécurisation professionnelle, où le délai limite est la date du départ effectif de l'intéressé [P9].

## Passages cités

- **[P9]** Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755 — Motivations (`61f0f2387743e3330ccf075f#motivations-1`)
  > (Soc., 13 mars 2013, pourvoi n° 11-21.150, Bull. 2013, V, n° 72). Elle en déduit que l'employeur qui dispense le salarié de l'exécution de son préavis doit, s'il entend renoncer à l'exécution de la clause de non-concurrence, le faire au plus tard à la date du départ effectif de l'intéressé de l'entreprise, nonobstant stipulations ou dispositions contraires (Soc., 21 janvier 2015, pourvoi n° 13-24.471, Bull. 2015, V, n° 3). Elle décide de même qu'en cas de rupture du contrat de travail résultant de l'adhésion du salarié au contrat de sécurisation professionnelle, l'employeur doit, s'il entend renoncer à l'exécution de la clause de non-concurrence, le faire au plus tard à la date du départ eff

## Limites

- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
