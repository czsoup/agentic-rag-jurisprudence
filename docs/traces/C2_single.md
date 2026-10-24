# Trace — Congés payés pendant l'éviction (single)

**Question** : Un salarié dont le licenciement nul a été suivi d'une réintégration a-t-il droit à des congés payés pour la période d'éviction ?

**Pourquoi cette question** : Chambre sociale, 1er mars 2023, n° 21-16.008 (publié) : oui, sauf s'il a occupé un autre emploi pendant cette période.

**Comportement attendu** : réponse directe, nuance « sauf autre emploi »

Run `61183e2e10ce` · statut `answered` · vérification `sufficient` · arrêt `answered`

Appels LLM : 3 · outils : {'search_cases': 1} · recherches : 1 · itérations : 2 · tokens : 7326 · latence : 57.9 s

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | agent | Aucune preuve collectée : recherche documentaire nécessaire (« licenciement nul réintégration congés payés période éviction »). | 10.2 s |
| 2 | TOOL | agent | `search_cases({"query": "licenciement nul réintégration congés payés période éviction", "k": 5})` |  |
| 3 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 4 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 30.5 s |
| 5 | CHECK | vérificateur | Preuves sufficient — 4 affirmation(s), toutes soutenues par les passages cités. | 17.1 s |
| 6 | FINAL | agent | Réponse vérifiée — 2 passage(s) cité(s). |  |

## Réponse finale

Le salarié dont le licenciement est annulé peut prétendre à ses droits à congés payés pour la période d'éviction [P1]. Cette possibilité s'applique en application des articles L. 3141-3 et L. 3141-9 du code du travail [P2]. La Cour précise que ce droit existe sauf si le salarié a occupé un autre emploi durant cette période [P2]. Le licenciement nul ouvre donc droit à une indemnité correspondant au préjudice subi, y compris les congés payés [P2].

## Passages cités

- **[P1]** Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 — Moyens (`65015d56ee1a2205e6581652#moyens-4`)
  > Et sur le troisième moyen du pourvoi n° B 22-11.106 Enoncé du moyen 23. La salariée fait grief à l'arrêt de la débouter de sa demande en paiement d'une indemnité de congé payé pour les périodes de référence courant du 1er juin 2018 à la date de sa réintégration effective, alors « que le salarié peut prétendre à ses droits à congés payés au titre de la période d'éviction comprise entre la date du licenciement nul et celle de la réintégration dans son emploi en application des dispositions des articles L. 3141-3 et L. 3141-9 du code du travail ; qu'en retenant, pour rejeter la demande en paiement des indemnités pour la période de référence courant du 1er juin 2018 à la date de sa réintégration
- **[P2]** Cour de cassation · Chambre sociale · 2023-03-01 · n° 21-16.008 — Motivations (`63fefc07002ac605de15b29e#motivations-1`)
  > Réponse de la Cour Vu les articles L. 1132-1 et L. 1132-4, dans sa rédaction antérieure à la loi n° 2022-401 du 21 mars 2022, du code du travail : 8. Il résulte de ces textes que tout licenciement prononcé à l'égard d'un salarié en raison de son état de santé est nul et que le salarié qui demande sa réintégration a droit au paiement d'une somme correspondant à la réparation de la totalité du préjudice subi au cours de la période qui s'est écoulée entre son licenciement et sa réintégration, dans la limite du montant des salaires dont il a été privé. 9. Le salarié peut prétendre à ses droits à congés payés au titre de la période d'éviction comprise entre la date du licenciement nul et celle de

## Limites

- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
