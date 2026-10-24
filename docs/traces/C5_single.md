# Trace — Indemnité de congé payé d'un enseignant (single)

**Question** : Dans l'arrêt du 13 septembre 2023 sur l'indemnité de congé payé d'un enseignant rémunéré pour des corrections de copies, quelle cour d'appel avait été censurée et pourquoi ?

**Pourquoi cette question** : Chambre sociale, 13 septembre 2023, n° 22-10.529, cassation d'un arrêt de la cour d'appel d'Aix-en-Provence ; le motif est dans le sommaire, la juridiction dans l'introduction et l'exposé.

**Comportement attendu** : lecture de l'affaire nécessaire

Run `78722aad858c` · statut `partial` · vérification `insufficient` · arrêt `max_iterations`

Appels LLM : 7 · outils : {'search_cases': 2, 'read_case': 1} · recherches : 2 · itérations : 5 · tokens : 33187 · latence : 187.7 s

> Validation humaine : réponse fournie par le script de scénario (`--hitl reject`).

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | agent | Aucune preuve collectée : recherche documentaire nécessaire (« 13 septembre 2023 indemnité congé payé enseignant corrections copies cour d'appel censurée »). | 8.5 s |
| 2 | TOOL | agent | `search_cases({"query": "13 septembre 2023 indemnité congé payé enseignant corrections copies cour d'appel censurée", "k": 5})` |  |
| 3 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 4 | DECISION | agent | Décision repérée (Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529) : lecture détaillée de ses passages. | 13.6 s |
| 5 | TOOL | agent | `read_case({"case_id": "65015d56ee1a2205e6581652"})` |  |
| 6 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 7 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 38.0 s |
| 8 | CHECK | vérificateur | Preuves insufficient — 5/6 affirmation(s) soutenue(s) ; 1 en échec sur les règles (citation absente, inventée ou incomplète). | 25.9 s |
| 9 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 41.2 s |
| 10 | CHECK | vérificateur | Preuves insufficient — 5/6 affirmation(s) soutenue(s) ; 1 en échec sur les règles (citation absente, inventée ou incomplète). | 21.2 s |
| 11 | DECISION | agent | Vérification insuffisante : nouvelle recherche reformulée (« 13 septembre 2023 enseignant corrections copies indemnité congé payé Aix-en-Provence cassation partielle »). | 39.2 s |
| 12 | TOOL | agent | `search_cases({"query": "13 septembre 2023 enseignant corrections copies indemnité congé payé Aix-en-Provence cassation partielle", "k": 5})` |  |
| 13 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 14 | HUMAN | agent | Validation humaine demandée : prolonger le budget. |  |
| 15 | HUMAN | agent | Décision humaine : refusée. |  |
| 16 | FINAL | agent | Réponse partielle — 2 passage(s) cité(s). |  |

## Réponse finale

Elle avait limité à certaines sommes la condamnation de l'Institut national des formations notariales au paiement de rappels d'indemnité de congé payé pour les années 2015/2016 à 2016/2018 [P13]. La cour d'appel avait retenu que la correction de copies et les soutenances LP ne devaient pas être intégrées dans le calcul de l'indemnité de congé payé [P9]. Or, selon la Cour de cassation, cette rémunération est versée en contrepartie ou à l'occasion du travail et doit donc être incluse dans le calcul [P9]. La cour d'appel a ainsi violé les articles L. 3141-22 et L. 3141-24 du code du travail [P9]. La Cour de cassation a annulé l'arrêt en ce qu'il limitait la condamnation de l'employeur [P13] et renvoyé l'affaire devant la cour d'appel d'Aix-en-Provence autrement composée [P13].

## Passages cités

- **[P13]** Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 — Dispositif (`65015d56ee1a2205e6581652#dispositif-0`)
  > PAR CES MOTIFS, et sans qu'il y ait lieu de statuer sur l'autre grief, la Cour : REJETTE le pourvoi n° Z 22-10.529 ; CASSE ET ANNULE, mais seulement en ce qu'il limite à 6 042,77 euros bruts, 7 088 euros bruts et 6 939,50 euros bruts la condamnation de l'Institut national des formations notariales au paiement de rappels d'indemnité de congé payé pour les années 2015/2016 à 2016/2018 et rejette les autres demandes au titre des indemnités de congé payé, l'arrêt rendu le 26 novembre 2021, entre les parties, par la cour d'appel d'Aix-en-Provence ; Remet, sur ces points, l'affaire et les parties dans l'état où elles se trouvaient avant cet arrêt et les renvoie devant la cour d'appel d'Aix-en-Prov
- **[P9]** Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 — Motivations (`65015d56ee1a2205e6581652#motivations-1`)
  > Réponse de la Cour Vu les articles L. 3141-22 du code du travail, dans sa rédaction issue de l'ordonnance n° 2007-329 du 12 mars 2007 et L. 3141-24 du même code, dans sa rédaction issue de la loi n° 2016-1088 du 8 août 2016 : 7. Selon ces textes, la rémunération à prendre en considération pour le calcul de l'indemnité de congé payé est la rémunération totale du salarié, incluant les primes et indemnités versées en complément du salaire si elles sont versées en contrepartie ou à l'occasion du travail. 8. Pour limiter à certaines sommes la condamnation de l'employeur au paiement de rappels d'indemnité de congé payé, l'arrêt retient que la correction de copies et « soutenances LP » ne doivent p

## Limites

- Réponse partielle : seules les affirmations vérifiées sont conservées.
- Non établi : La cour d'appel d'Aix-en-Provence a été censurée par la Cour de cassation dans son arrêt du 13 septembre 2023 [P13].
- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
