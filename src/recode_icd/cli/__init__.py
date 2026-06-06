import typer

from recode_icd.cli.build import build_app
from recode_icd.cli.cards import cards_app

app = typer.Typer(help="recode-icd — fusion CIM-10 OFS ⊕ OWL/ANS")
app.add_typer(build_app, name="build")
app.add_typer(cards_app, name="cards")


@app.callback()
def main() -> None:
    """CLI principale de recode-icd."""
