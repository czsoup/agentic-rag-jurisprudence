# Trace — Scénario 2 — recherche multi-étapes (single)

**Question** : Dans l'affaire où une rupture conventionnelle a été annulée pour un vice du consentement de l'employeur, que reprochait-on au salarié, quelle cour d'appel avait statué, et quels effets la Cour de cassation attache-t-elle à la rupture ?

**Pourquoi cette question** : Arrêt de la chambre sociale du 19 juin 2024 (n° 23-10.817, rejet, cour d'appel de Toulouse). Le passage le mieux classé (motivations ou sommaire) donne l'effet (une démission), mais le reproche fait au salarié (réticence dolosive sur un projet d'entreprise concurrente) et la juridiction d'appel se trouvent dans l'exposé et les moyens : il faut trouver l'affaire, puis la lire.

**Comportement attendu** : search_cases puis read_case sur 23-10.817 ; réponse citant l'exposé et les motivations.

Run `7e68c5e94a39` · statut `answered` · vérification `sufficient` · arrêt `answered`

Appels LLM : 6 · outils : {'search_cases': 1, 'read_case': 1} · recherches : 1 · itérations : 4 · tokens : 19033 · latence : 104.4 s

## Trace d'exécution

| # | type | agent | résumé | latence |
|---|---|---|---|---|
| 1 | DECISION | agent | Aucune preuve collectée : recherche documentaire nécessaire (« rupture conventionnelle annulée vice consentement employeur reproche salarié »). | 8.1 s |
| 2 | TOOL | agent | `search_cases({"query": "rupture conventionnelle annulée vice consentement employeur reproche salarié", "k": 5})` |  |
| 3 | OBSERVATION | agent | 5 décision(s) ; meilleure : Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 | 0.0 s |
| 4 | DECISION | agent | Décision repérée (Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817) : lecture détaillée de ses passages. | 19.9 s |
| 5 | TOOL | agent | `read_case({"case_id": "66728101f7ab5c00087309e1", "focus": "rupture conventionnelle vice consentement reproche salarié cour d'appel effets"})` |  |
| 6 | OBSERVATION | agent | 8 passage(s) lus dans Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 | 0.0 s |
| 7 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 29.6 s |
| 8 | CHECK | vérificateur | Preuves insufficient — 2/3 affirmation(s) soutenue(s) ; 1 non établie(s) par le juge. | 14.9 s |
| 9 | DECISION | agent | Passages jugés suffisants par l'agent : réponse candidate soumise au vérificateur. | 19.8 s |
| 10 | CHECK | vérificateur | Preuves sufficient — 3 affirmation(s), toutes soutenues par les passages cités. | 11.9 s |
| 11 | FINAL | agent | Réponse vérifiée — 3 passage(s) cité(s). |  |

## Réponse finale

Le salarié a été reproché d'avoir volontairement dissimulé des éléments dont il connaissait le caractère déterminant pour l'employeur afin d'obtenir son consentement à la rupture conventionnelle [P1]. La cour d'appel de Toulouse a annulé la rupture et condamné le salarié [P6]. La Cour de cassation confirme que, lorsque la nullité est imputable au salarié pour dol, la rupture produit les effets d'une démission [P11].

## Passages cités

- **[P1]** Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 — Motivations (`66728101f7ab5c00087309e1#motivations-0`)
  > Réponse de la Cour 4. Selon l'article 1137 du code civil, dans sa rédaction issue de la loi n° 2018-287 du 20 avril 2018, constitue un dol la dissimulation intentionnelle par l'un des contractants d'une information dont il sait le caractère déterminant pour l'autre partie. 5. La cour d'appel a relevé que l'employeur s'est déterminé au regard du seul souhait de reconversion professionnelle dans le management invoqué par le salarié. 6. Par une interprétation souveraine, exclusive de dénaturation, de la portée des éléments de preuve produits, la cour d'appel a constaté que le salarié avait volontairement dissimulé des éléments dont il connaissait le caractère déterminant pour l'employeur afin d
- **[P6]** Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 — Introduction (`66728101f7ab5c00087309e1#introduction-0`)
  > SOC. CZ COUR DE CASSATION ______________________ Audience publique du 19 juin 2024 Rejet M. SOMMER, président Arrêt n° 644 FS-B Pourvoi n° G 23-10.817 R É P U B L I Q U E F R A N Ç A I S E _________________________ AU NOM DU PEUPLE FRANÇAIS _________________________ ARRÊT DE LA COUR DE CASSATION, CHAMBRE SOCIALE, DU 19 JUIN 2024 M. [W] [P], domicilié [Adresse 1], a formé le pourvoi n° G 23-10.817 contre l'arrêt rendu le 18 novembre 2022 par la cour d'appel de Toulouse (4e chambre, section 1), dans le litige l'opposant à la société Alientech France, société par actions simplifiée, dont le siège est [Adresse 2], défenderesse à la cassation. Le demandeur invoque, à l'appui de son pourvoi, deux 
- **[P11]** Cour de cassation · Chambre sociale · 2024-06-19 · n° 23-10.817 — Motivations (`66728101f7ab5c00087309e1#motivations-1`)
  > Réponse de la Cour 10. Lorsque le contrat de travail est rompu en exécution d'une convention de rupture ensuite annulée en raison d'un vice du consentement de l'employeur, la rupture produit les effets d'une démission. 11. Ayant retenu que la dissimulation intentionnelle du salarié caractérisait un dol et que la convention de rupture était nulle, la cour d'appel a exactement décidé que la nullité produisait les effets d'une démission. 12. Le moyen n'est donc pas fondé.

## Limites

- Réponse produite par un modèle local à partir d'extraits : à confirmer sur la décision intégrale avant tout usage juridique.
