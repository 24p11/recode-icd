# Candidates — INSUFFISANCE RÉNALE FONCTIONNELLE

> **Fichier GÉNÉRÉ.** Source unique :
> `candidates_recommendations.csv` et
> `candidates_recommendation_codes.csv` du même répertoire.
> Régénérer : `uv run python scripts/rendre_candidates_guide_mco.py`.
> Ne pas éditer à la main — les rôles ne doivent exister qu'à un seul
> endroit (cf. l'incident ORPHANET du chantier `chapter_policy`).
>
> Texte source : `data/guide_mco/extraits/insuffisance_renale_fonctionnelle.md`
> (guide chap. V, pp. imprimées 105-106). Les `L…` y renvoient.

**1 consignes, 4 associations**.

---

## Consignes nouvelles

### GM2026-V-IRF-01 — `condition_emploi`

**Situation** : Insuffisance rénale fonctionnelle — R39.2, N17 réservée à l'atteinte organique

**Texte** : L'insuffisance rénale fonctionnelle (altération habituellement passagère et curable de la fonction rénale par diminution de la perfusion — hypovolémie, hypotension, cause iatrogène — sans atteinte organique du rein ni obstacle des voies excrétrices, dite prérénale ou extrarénale) se code R39.2 Urémie extrarénale, conformément à la note d'exclusion du groupe N17-N19. L'absence de lésion du parenchyme invalide la consigne antérieure de la coder N17.8. La catégorie N17 est réservée aux insuffisances rénales aigües avec atteinte organique du tissu rénal ; en cas de cause incertaine, on emploie N17.9.

**Condition** : —

**Citation** (`insuffisance_renale_fonctionnelle.md` L10-12) :
« l’insuffisance rénale fonctionnelle doit donc être codée R39.2 Urémie extrarénale. L’absence de lésion du parenchyme rénal invalide la consigne jusqu’ici donnée de la coder N17.8 Autres insuffisances rénales aigües. La catégorie N17 doit être réservée au codage des insuffisances rénales aigües avec atteinte organique du tissu rénal. En cas d’insuffisance rénale aigüe dont la cause, extrarénale ou par atteinte organique, est incertaine, on emploie le code N17.9. »

| code_expr | role | centralite | portee | condition |
|---|---|---|---|---|
| `N17` | `regi` | sujet | chaque | atteinte organique du tissu rénal |
| `N17.8` | `interdit` | sujet | chaque | insuffisance rénale fonctionnelle — consigne antérieure invalidée |
| `N17.9` | `regi` | sujet | chaque | cause extrarénale ou organique incertaine |
| `R39.2` | `regi` | sujet | chaque | insuffisance rénale fonctionnelle (prérénale/extrarénale) |

