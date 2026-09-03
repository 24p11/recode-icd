#!/usr/bin/env bash
# Extraction du texte des articles du guide méthodologique MCO.
#
# Régénère `data/guide_mco/extraits_bruts/`. Les fichiers produits sont
# COMMITTÉS : ils figent les citations et les rendent vérifiables
# indépendamment de la version de poppler installée.
#
# `-layout` est load-bearing, pas décoratif : la contre-lecture
# indépendante des lignes candidates se fera contre une extraction
# `pdftotext -layout`, donc mêmes découpes de lignes et citations
# alignées. Changer d'option décale les citations.
#
# Les bornes sont des pages PDF. Le guide a un décalage constant de 8
# entre page PDF et page imprimée (PDF 86 = imprimée 78). Chaque article
# est extrait en PAGES ENTIÈRES : la dernière page peut donc déborder sur
# l'article suivant, ce qui est voulu — une citation reste localisable
# par son numéro de page imprimée.

set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PDF="$RACINE/data/guide_mco/guide_methodo_mco_2026_version_provisoire.pdf"
SORTIE="$RACINE/data/guide_mco/extraits_bruts"

mkdir -p "$SORTIE"

# nom_fichier:première_page_pdf:dernière_page_pdf:titre de l'article
ARTICLES=(
  "avc:86:89:ACCIDENTS VASCULAIRES CÉRÉBRAUX (imprimées 78-81)"
  "anemie_posthemorragique_d62:89:90:ANÉMIE POSTHÉMORRAGIQUE AIGÜE APRÈS UNE INTERVENTION (imprimées 81-82)"
  "chapitre_xxi:101:111:EMPLOI DES CODES DU CHAPITRE XXI DE LA CIM-10 (imprimées 93-103)"
  "malnutrition_denutrition:117:122:MALNUTRITION, DÉNUTRITION (imprimées 109-114)"
  # -- chantier B (file : data/guide_mco/extraction/file_chantier_B.md) --
  "accouchement_impromptu:89:89:ACCOUCHEMENT IMPROMPTU OU À DOMICILE (imprimée 81)"
  "antecedents:90:91:ANTÉCÉDENTS (imprimées 82-83)"
  "atherosclerose_gangrene:91:91:ATHEROSCLEROSE AVEC GANGRENE (imprimée 83)"
  "carences_vitaminiques:91:91:CARENCES VITAMINIQUES (imprimée 83)"
  "chutes_a_repetition:91:91:CHUTES A REPETITION (imprimée 83)"
  "codes_oms_usage_urgent:92:92:CODES OMS RÉSERVÉS A UN USAGE URGENT (imprimée 84)"
  "complications_actes:92:96:COMPLICATIONS DES ACTES MÉDICAUX ET CHIRURGICAUX (imprimées 84-88)"
)

VERSION_POPPLER="$(pdftotext -v 2>&1 | head -1)"

for entree in "${ARTICLES[@]}"; do
  IFS=':' read -r nom premiere derniere titre <<<"$entree"
  cible="$SORTIE/$nom.txt"
  {
    echo "# Guide méthodologique MCO 2026 (version provisoire) — $titre"
    echo "#"
    echo "# Source  : data/guide_mco/guide_methodo_mco_2026_version_provisoire.pdf"
    echo "# Chapitre du guide : V (Consignes de codage avec la 10e révision de la CIM)"
    echo "# Pages PDF : $premiere-$derniere  (imprimées : $((premiere - 8))-$((derniere - 8)))"
    echo "#"
    echo "# Commande exacte :"
    echo "#   pdftotext -layout -f $premiere -l $derniere \\"
    echo "#     data/guide_mco/guide_methodo_mco_2026_version_provisoire.pdf <sortie>"
    echo "# Outil : $VERSION_POPPLER"
    echo "#"
    echo "# Régénérer : scripts/extraire_guide_mco.sh"
    echo "# ---------------------------------------------------------------------"
    echo
    pdftotext -layout -f "$premiere" -l "$derniere" "$PDF" -
  } >"$cible"
  echo "Écrit : $cible"
done
