# Trace — Formulation profane (non-concurrence) (single)

**Question** : Après mon départ négocié avec mon patron, il veut m'interdire de travailler chez un concurrent alors qu'il ne m'a rien dit avant la fin de mon contrat : en a-t-il le droit ?

**Pourquoi cette question** : = S3a

**Comportement attendu** : reformulation utile

Run `f76a52e4230e` · statut `abstained` · vérification `contradictory` · arrêt `human_rejected`

Appels LLM : 3 · outils : {'search_cases': 1} · recherches : 1 · itérations : 2 · tokens : 6470 · latence : 64.1 s

> Validation humaine : réponse fournie par le script de scénario (`--hitl reject`).

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | agent | Aucune preuve collectée : recherche documentaire nécessaire (« clause de non-concurrence contrepartie financière information préalable départ négocié »). | 10.1 s |
| 2 | TOOL | agent | `search_cases({"query": "clause de non-concurrence contrepartie financière information préalable départ négocié", "k": 5})` |  |
| 3 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2022-01-26 · n° 20-15.755 | 0.0 s |
| 4 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 33.2 s |
| 5 | CHECK | vérificateur | Preuves contradictory — 1 affirmation(s) contredite(s) par les passages cités. | 20.6 s |
| 6 | HUMAN | vérificateur | Validation humaine demandée : sources contradictoires. |  |
| 7 | HUMAN | agent | Décision humaine : refusée. |  |
| 8 | FINAL | agent | Abstention — la diffusion a été refusée par l'utilisateur. |  |

## Réponse finale

Je ne peux pas répondre de manière fiable à partir du corpus : la diffusion a été refusée par l'utilisateur.

## Limites

- Non établi : Non, votre employeur n'a pas le droit de vous interdire de travailler chez un concurrent sans avoir informé le salarié avant la fin du contrat.
- Non établi : Une information tardive, comme après votre départ, ne suffit pas pour libérer le salarié de son obligation [P2].
