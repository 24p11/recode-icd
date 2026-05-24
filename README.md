# recode-icd

Toolkit Python pour exploiter les référentiels électroniques de la CIM-10
(formats OFS suisse et OWL/ANS) en vue d'enrichir des prompts destinés à la
génération de textes médicaux annotés par LLM.

Voir [`CLAUDE.md`](CLAUDE.md) pour la documentation complète : objectifs métier,
politique de fusion OFS ⊕ OWL, conventions, pitfalls.

## Installation

```bash
uv sync
uv run pre-commit install
```

## Commandes courantes

```bash
uv run pytest                            # tous les tests
uv run pytest -m unit                    # unitaires seuls
uv run pytest -m regression              # régression seule
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/recode_icd
```

## État du projet

Phase de bootstrap. Le code legacy v1 (notebooks d'exploration et de
fine-tuning de modèles) est archivé dans
[`arXiv/legacy_v1/`](arXiv/legacy_v1/README.md).
