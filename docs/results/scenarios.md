| question | type | mode | statut | vérification | arrêt | passages cités | appels LLM | appels outils | recherches | itérations | tokens | latence (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | simple | single | partial | insufficient | max_iterations | 1 | 7 | 3 | 2 | 5 | 20076 | 104.1 |
| S2 | multi-step | single | answered | sufficient | answered | 3 | 6 | 2 | 1 | 4 | 19033 | 104.4 |
| S3a | insufficient-reformulate | single | abstained | contradictory | human_rejected | 0 | 3 | 1 | 1 | 2 | 6470 | 64.3 |
| S3b | insufficient-absent | single | abstained | None | max_iterations | 0 | 5 | 5 | 5 | 5 | 29774 | 69.6 |
