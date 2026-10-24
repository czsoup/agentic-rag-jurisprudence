# Comparaison v1 — exécution interrompue (2026-10-24)

Première exécution de `scripts/run_scenarios.py --set comparison`, interrompue volontairement.

- **Runs valides** (terminés avant 11 h 45) : C1 et C2 dans les trois modes, C3 en RAG statique.
- **Runs invalides** : C3 en agent unique et en multi-agents, C4 en agent unique. Le Mac est passé en veille à 11 h 45, puis est resté sur batterie avec des cycles veille / réveil partiel (journal `pmset -g log`). Les appels au modèle ont dépassé le délai de 180 s. Ce ne sont pas des erreurs du système mesuré, mais ces runs ne sont pas exploitables.
- **Mode multi-agents** : version v1. L'échec de `C2_multi` (17 appels LLM, abstention alors que le chercheur avait trouvé la réponse) a motivé DEC-023 (multi-agents v2).

Les chiffres présentés dans le rapport proviennent de la seconde exécution complète, décrite dans `docs/results/comparison.md`.
