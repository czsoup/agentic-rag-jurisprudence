# Trace — Indemnité de congé payé d'un enseignant (multi)

**Question** : Dans l'arrêt du 13 septembre 2023 sur l'indemnité de congé payé d'un enseignant rémunéré pour des corrections de copies, quelle cour d'appel avait été censurée et pourquoi ?

**Pourquoi cette question** : Chambre sociale, 13 septembre 2023, n° 22-10.529, cassation d'un arrêt de la cour d'appel d'Aix-en-Provence ; le motif est dans le sommaire, la juridiction dans l'introduction et l'exposé.

**Comportement attendu** : lecture de l'affaire nécessaire

Run `807b9c76278b` · statut `partial` · vérification `insufficient` · arrêt `max_iterations`

Appels LLM : 17 · outils : {'search_cases': 2, 'read_case': 4} · recherches : 2 · itérations : 5 · tokens : 49412 · latence : 253.4 s

> Validation humaine : réponse fournie par le script de scénario (`--hitl reject`).

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | superviseur | Délégation au chercheur — Le dossier est vide ; il faut trouver les preuves dans le corpus. | 5.7 s |
| 2 | DECISION | chercheur | Recherche dans le corpus (« arrêt 13 septembre 2023 indemnité congé payé enseignant corrections copies »). | 9.4 s |
| 3 | TOOL | agent | `search_cases({"query": "arrêt 13 septembre 2023 indemnité congé payé enseignant corrections copies", "k": 5})` |  |
| 4 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 5 | DECISION | chercheur | Lecture détaillée de la décision 65015d56ee1a2205e6581652. | 13.7 s |
| 6 | TOOL | agent | `read_case({"case_id": "65015d56ee1a2205e6581652"})` |  |
| 7 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 8 | OBSERVATION | chercheur | Compte rendu du chercheur : 13 passage(s) au dossier. Décision pertinente : case_id=65015d56ee1a2205e6581652 (alias [P9], [P13]). La cour d'appel d'Aix-en-Provence a été censurée car elle avait exclu du calcul de l'indemnité de congé payé les rémunérations versées pour des corrections de copie |  |
| 9 | DECISION | superviseur | Rédaction de la synthèse — La Cour d'appel d'Aix-en-Provence a été censurée car elle avait exclu du calcul de l'indemnité de congé payé les rémunérations versées pour des corrections de copies et soutenances, alors que ces sommes constituent une rémunération totale perçue en contrepartie du travail. | 10.3 s |
| 10 | DECISION | superviseur | Synthèse rédigée à partir de 10 passage(s) : soumise au vérificateur. | 16.4 s |
| 11 | CHECK | vérificateur | Preuves insufficient — 4/5 affirmation(s) soutenue(s) ; 1 en échec sur les règles (citation absente, inventée ou incomplète). | 19.9 s |
| 12 | DECISION | superviseur | Délégation au chercheur — Le chercheur doit trouver la citation textuelle confirmant que la cour d'appel d'Aix-en-Provence a été censurée pour avoir exclu les rémunérations liées aux corrections de copies du calcul de l'indemnité de congé payé. | 12.2 s |
| 13 | DECISION | chercheur | Recherche dans le corpus (« 13 septembre 2023 indemnité de congé payé enseignant corrections de copies cour d'appel censurée »). | 10.7 s |
| 14 | TOOL | agent | `search_cases({"query": "13 septembre 2023 indemnité de congé payé enseignant corrections de copies cour d'appel censurée", "k": 5})` |  |
| 15 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 16 | DECISION | chercheur | Lecture détaillée de la décision 65015d56ee1a2205e6581652. | 17.4 s |
| 17 | TOOL | agent | `read_case({"case_id": "65015d56ee1a2205e6581652", "focus": "motifs de la censure et nom de la cour d'appel"})` |  |
| 18 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 19 | OBSERVATION | chercheur | Compte rendu du chercheur : 18 passage(s) au dossier. Décision pertinente : case_id=65015d56ee1a2205e6581652 (alias [P9] et [P13]). La cour d'appel d'Aix-en-Provence a été censurée car elle avait exclu les rémunérations pour corrections de copies du calcul de l'indemnité de congé payé, alors q |  |
| 20 | DECISION | superviseur | Délégation au chercheur — Le dossier manque du nom exact de la cour d'appel censurée et de la citation juridique complète justifiant cette censure concernant les corrections de copies. | 11.9 s |
| 21 | DECISION | chercheur | Lecture détaillée de la décision 65015d56ee1a2205e6581652. | 13.2 s |
| 22 | TOOL | agent | `read_case({"case_id": "65015d56ee1a2205e6581652", "focus": "censure cour d'appel motif"})` |  |
| 23 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 24 | OBSERVATION | chercheur | Compte rendu du chercheur : 18 passage(s) au dossier. Décision pertinente : case_id=65015d56ee1a2205e6581652 (Cour de cassation, Chambre sociale, 13 septembre 2023, n° 22-10.529). La cour d'appel censurée est la cour d'appel d'Aix-en-Provence [P13]. Elle a été censurée car elle n'a pas intégré |  |
| 25 | DECISION | superviseur | Délégation au chercheur — Le dossier contient des indices sur le motif (rémunération corrections de copies non intégrée) mais manque de la mention explicite du nom de la cour d'appel censurée dans les extraits fournis pour valider pleinement l'affirmation. | 11.9 s |
| 26 | DECISION | chercheur | Lecture détaillée de la décision 65015d56ee1a2205e6581652. | 8.3 s |
| 27 | TOOL | agent | `read_case({"case_id": "65015d56ee1a2205e6581652"})` |  |
| 28 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 | 0.0 s |
| 29 | OBSERVATION | chercheur | Compte rendu du chercheur : 18 passage(s) au dossier. Décision pertinente : case_id=65015d56ee1a2205e6581652, alias [P9] qui mentionne la cour d'appel d'Aix-en-Provence censurée pour avoir exclu la rémunération des corrections de copies du calcul de l'indemnité de congé payé alors que cette ré |  |
| 30 | HUMAN | agent | Validation humaine demandée : prolonger le budget. |  |
| 31 | HUMAN | agent | Décision humaine : refusée. |  |
| 32 | FINAL | agent | Réponse partielle — 2 passage(s) cité(s). |  |

## Réponse finale

Cette juridiction avait limité le rappel d'indemnité de congé payé en excluant les sommes versées pour la correction des copies et les soutenances LP du calcul [P9]. La Cour a jugé que cette rémunération est versée en contrepartie ou à l'occasion du travail et doit donc être intégrée au calcul selon les articles L. 3141-22 et L. 3141-24 du code du travail [P9]. Par conséquent, la cour d'appel a violé ces textes en statuant ainsi [P9]. La cassation n'a concerné que la limitation de la condamnation au paiement des rappels pour les années 2015/2016 à 2016/2018 [P13].

## Passages cités

- **[P9]** Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 — Motivations (`65015d56ee1a2205e6581652#motivations-1`)
  > Réponse de la Cour Vu les articles L. 3141-22 du code du travail, dans sa rédaction issue de l'ordonnance n° 2007-329 du 12 mars 2007 et L. 3141-24 du même code, dans sa rédaction issue de la loi n° 2016-1088 du 8 août 2016 : 7. Selon ces textes, la rémunération à prendre en considération pour le calcul de l'indemnité de congé payé est la rémunération totale du salarié, incluant les primes et indemnités versées en complément du salaire si elles sont versées en contrepartie ou à l'occasion du travail. 8. Pour limiter à certaines sommes la condamnation de l'employeur au paiement de rappels d'indemnité de congé payé, l'arrêt retient que la correction de copies et « soutenances LP » ne doivent p
- **[P13]** Cour de cassation · Chambre sociale · 2023-09-13 · n° 22-10.529 — Dispositif (`65015d56ee1a2205e6581652#dispositif-0`)
  > PAR CES MOTIFS, et sans qu'il y ait lieu de statuer sur l'autre grief, la Cour : REJETTE le pourvoi n° Z 22-10.529 ; CASSE ET ANNULE, mais seulement en ce qu'il limite à 6 042,77 euros bruts, 7 088 euros bruts et 6 939,50 euros bruts la condamnation de l'Institut national des formations notariales au paiement de rappels d'indemnité de congé payé pour les années 2015/2016 à 2016/2018 et rejette les autres demandes au titre des indemnités de congé payé, l'arrêt rendu le 26 novembre 2021, entre les parties, par la cour d'appel d'Aix-en-Provence ; Remet, sur ces points, l'affaire et les parties dans l'état où elles se trouvaient avant cet arrêt et les renvoie devant la cour d'appel d'Aix-en-Prov

## Limites

- Réponse partielle : seules les affirmations vérifiées sont conservées.
- Non établi : La Cour de cassation a censuré la cour d'appel d'Aix-en-Provence dans l'arrêt du 13 septembre 2023 [P6][P13].
- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
