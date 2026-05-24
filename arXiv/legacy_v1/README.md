# Legacy v1 — archives

Code historique (notebooks + utilitaires) ayant servi à produire les premiers
artefacts dérivés (`dict_syn.xlsx`, `cim_index_modifie.csv`, modèles
CamemBERT et GLiNER). Conservé pour traçabilité et comparaison avec le
nouveau pipeline `src/recode_icd/`.

**À ne pas modifier.** Les notebooks référencent des chemins `data/...` qui
peuvent évoluer ; ils ne sont pas garantis de tourner tels quels.

## Contenu

| Fichier | Rôle | Réutilisé dans v2 ? |
|---|---|---|
| `icd_exploration.ipynb` | Exploration OFS + ATIH + Orphanet, doublons d'index | Inspiration pour `loaders/ofs.py` |
| `prep_data_icd_models.ipynb` | Fusion Hector + Orphanet + OFS → `dict_syn.xlsx` | Inspiration pour `merge.py` |
| `generation_usable_icd_index_entries.ipynb` | Reformulation Mistral de l'index Hector "B" | Sortie consommée (`cim_index_modifie.csv`) |
| `icd_models.ipynb` | Fine-tuning CamemBERT-bio | Hors scope (training aval) |
| `final_finetuning_different_backbone.ipynb` | Fine-tuning GLiNER ModernBERT | Hors scope (training aval) |
| `prep_data_cepidc.ipynb` | Agrégation causes de décès CEPIDC | Hors scope (données de validation externes) |
| `utils.py` | Extraction JSON depuis sorties LLM, reformatage codes DP/DAS | Hors scope (post-traitement LLM) |
| `config-different-backbone.yaml` | Hyperparamètres GLiNER | Hors scope |

## Trous identifiés par rapport à v2

Le legacy ne contenait **pas** :
- de loader OWL/ANS (le RDF `terminologie-cim-10-2025-01-01.rdf` n'était jamais lu)
- d'extraction des associations dague/astérisque (`DAGSTAR.txt` OFS ni `atih-cim10:hasCausality` ANS)
- de propagation hiérarchique bloc/catégorie → code feuille avec traçabilité
- de synthèse des notes "frères" sur les codes `.8`

Ces 4 morceaux sont la valeur ajoutée du nouveau projet.
