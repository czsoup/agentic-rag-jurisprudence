# Trace — Renonciation à la non-concurrence (termes juridiques) (single)

**Question** : En cas de rupture conventionnelle, jusqu'à quand l'employeur peut-il renoncer à la clause de non-concurrence ?

**Pourquoi cette question** : Même arrêt que C6, formulé en termes juridiques : isole l'effet de la formulation.

**Comportement attendu** : réponse directe

Run `1cea87f5ae2a` · statut `answered` · vérification `sufficient` · arrêt `answered`

Appels LLM : 6 · outils : {'search_cases': 1, 'read_case': 1} · recherches : 1 · itérations : 4 · tokens : 22696 · latence : 120.5 s

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | agent | Aucune preuve collectée : recherche documentaire nécessaire (« rupture conventionnelle clause non-concurrence renonciation délai employeur »). | 7.4 s |
| 2 | TOOL | agent | `search_cases({"query": "rupture conventionnelle clause non-concurrence renonciation délai employeur", "k": 5})` |  |
| 3 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755 | 0.0 s |
| 4 | DECISION | agent | Décision repérée (Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755) : lecture détaillée de ses passages. | 29.9 s |
| 5 | TOOL | agent | `read_case({"case_id": "61f0f2387743e3330ccf075f", "focus": "délai de renonciation clause non-concurrence rupture conventionnelle"})` |  |
| 6 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755 | 0.0 s |
| 7 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 28.1 s |
| 8 | CHECK | vérificateur | Preuves insufficient — 2/4 affirmation(s) soutenue(s) ; 2 non établie(s) par le juge. | 19.5 s |
| 9 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 21.3 s |
| 10 | CHECK | vérificateur | Preuves sufficient — 3 affirmation(s), toutes soutenues par les passages cités. | 14.3 s |
| 11 | FINAL | agent | Réponse vérifiée — 2 passage(s) cité(s). |  |

## Réponse finale

En cas de rupture conventionnelle, l'employeur doit renoncer à la clause de non-concurrence au plus tard à la date de rupture fixée par la convention [P9]. Cette obligation s'impose nonobstant toute stipulation contractuelle contraire [P9]. La Cour précise que cette date de rupture est celle qui ne peut intervenir avant le lendemain du jour de l'homologation administrative [P8].

## Passages cités

- **[P9]** Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755 — Motivations (`61f0f2387743e3330ccf075f#motivations-1`)
  > (Soc., 13 mars 2013, pourvoi n° 11-21.150, Bull. 2013, V, n° 72). Elle en déduit que l'employeur qui dispense le salarié de l'exécution de son préavis doit, s'il entend renoncer à l'exécution de la clause de non-concurrence, le faire au plus tard à la date du départ effectif de l'intéressé de l'entreprise, nonobstant stipulations ou dispositions contraires (Soc., 21 janvier 2015, pourvoi n° 13-24.471, Bull. 2015, V, n° 3). Elle décide de même qu'en cas de rupture du contrat de travail résultant de l'adhésion du salarié au contrat de sécurisation professionnelle, l'employeur doit, s'il entend renoncer à l'exécution de la clause de non-concurrence, le faire au plus tard à la date du départ eff
- **[P8]** Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755 — Motivations (`61f0f2387743e3330ccf075f#motivations-0`)
  > 5. En application de l'article 1014, alinéa 2, du code de procédure civile, il n'y a pas lieu de statuer par une décision spécialement motivée sur ce moyen qui n'est manifestement pas de nature à entraîner la cassation. Mais sur le moyen relevé d'office 6. Après avis donné aux parties, conformément à l'article 1015 du code de procédure civile, il est fait application de l'article 620, alinéa 2, du même code. Vu l'article L. 1237-13 du code du travail et l'article 1134 du code civil dans sa rédaction antérieure à l'ordonnance n° 2016-131 du 10 février 2016 : 7. La Cour de cassation juge qu'aux termes de l'article L. 1237-13 du code du travail, la convention de rupture conclue entre un employe

## Limites

- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
