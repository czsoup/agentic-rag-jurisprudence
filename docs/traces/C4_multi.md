# Trace — Rupture annulée pour dol du salarié (multi)

**Question** : Dans l'affaire où une rupture conventionnelle a été annulée pour un vice du consentement de l'employeur, que reprochait-on au salarié, quelle cour d'appel avait statué, et quels effets la Cour de cassation attache-t-elle à la rupture ?

**Pourquoi cette question** : = S2

**Comportement attendu** : lecture de l'affaire nécessaire

Run `0c66e3c6f34d` · statut `answered` · vérification `sufficient` · arrêt `answered`

Appels LLM : 7 · outils : {'search_cases': 1, 'read_case': 1} · recherches : 1 · itérations : 2 · tokens : 18054 · latence : 82.8 s

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | superviseur | Délégation au chercheur — Le dossier est vide ; il faut trouver les éléments factuels et juridiques demandés dans le corpus. | 7.1 s |
| 2 | DECISION | chercheur | Recherche dans le corpus (« rupture conventionnelle annulée vice du consentement employeur dolosité mensonge reproche salarié cour d'appel effets nullité »). | 10.1 s |
| 3 | TOOL | agent | `search_cases({"query": "rupture conventionnelle annulée vice du consentement employeur dolosité mensonge reproche salarié cour d'appel effets nullité", "k": 5})` |  |
| 4 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 | 0.0 s |
| 5 | DECISION | chercheur | Lecture détaillée de la décision 66728101f7ab5c00087309e1. | 20.0 s |
| 6 | TOOL | agent | `read_case({"case_id": "66728101f7ab5c00087309e1", "focus": "vice du consentement, reproche salarié, cour d'appel, effets rupture"})` |  |
| 7 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 | 0.0 s |
| 8 | OBSERVATION | chercheur | Compte rendu du chercheur : 12 passage(s) au dossier. Décision pertinente : case_id=66728101f7ab5c00087309e1 (arrêt de la Cour de cassation du 19/06/2024).  Passages utiles : [P1] et [P8] pour le reproche fait au salarié (réticence dolosive par dissimulation volontaire d'informations sur son p |  |
| 9 | DECISION | superviseur | Rédaction de la synthèse — Les passages [P1], [P7] et [P11] répondent intégralement aux trois sous-questions de l'affaire. | 9.1 s |
| 10 | DECISION | superviseur | Synthèse rédigée à partir de 10 passage(s) : soumise au vérificateur. | 12.6 s |
| 11 | CHECK | vérificateur | Preuves sufficient — 3 affirmation(s), toutes soutenues par les passages cités. | 11.5 s |
| 12 | FINAL | agent | Réponse vérifiée — 3 passage(s) cité(s). |  |

## Réponse finale

Dans l'affaire où la rupture conventionnelle a été annulée pour vice du consentement de l'employeur, c'est la cour d'appel de Toulouse qui a statué le 18 novembre 2022 [P7]. La Cour de cassation reproche au salarié d'avoir volontairement dissimulé des éléments dont il connaissait le caractère déterminant pour l'employeur afin d'obtenir son consentement à la rupture, ce qui constitue un dol [P9]. Par conséquent, la Cour de cassation considère que la nullité de cette convention de rupture produit les effets d'une démission [P11].

## Passages cités

- **[P7]** Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 — Exposé du litige (`66728101f7ab5c00087309e1#expose-0`)
  > Faits et procédure 1. Selon l'arrêt attaqué (Toulouse, 18 novembre 2022), M. [P] a été engagé en qualité de technicien commercial par la société Arm Engineering le 31 mai 2010. Son contrat de travail a été transféré à la société Alientech France le 16 mai 2011. Le salarié exerçait en dernier lieu les fonctions de responsable commercial. 2. Le salarié et l'employeur ont signé une convention de rupture le 20 novembre 2018 et la relation de travail a pris fin le 31 décembre suivant.
- **[P9]** Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 — Motivations (`66728101f7ab5c00087309e1#motivations-0`)
  > Réponse de la Cour 4. Selon l'article 1137 du code civil, dans sa rédaction issue de la loi n° 2018-287 du 20 avril 2018, constitue un dol la dissimulation intentionnelle par l'un des contractants d'une information dont il sait le caractère déterminant pour l'autre partie. 5. La cour d'appel a relevé que l'employeur s'est déterminé au regard du seul souhait de reconversion professionnelle dans le management invoqué par le salarié. 6. Par une interprétation souveraine, exclusive de dénaturation, de la portée des éléments de preuve produits, la cour d'appel a constaté que le salarié avait volontairement dissimulé des éléments dont il connaissait le caractère déterminant pour l'employeur afin d
- **[P11]** Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 — Motivations (`66728101f7ab5c00087309e1#motivations-1`)
  > Réponse de la Cour 10. Lorsque le contrat de travail est rompu en exécution d'une convention de rupture ensuite annulée en raison d'un vice du consentement de l'employeur, la rupture produit les effets d'une démission. 11. Ayant retenu que la dissimulation intentionnelle du salarié caractérisait un dol et que la convention de rupture était nulle, la cour d'appel a exactement décidé que la nullité produisait les effets d'une démission. 12. Le moyen n'est donc pas fondé.

## Limites

- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
