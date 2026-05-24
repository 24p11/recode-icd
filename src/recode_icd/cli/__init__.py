import typer

from recode_icd.cli.build import build_app

app = typer.Typer(help="recode-icd — fusion CIM-10 OFS ⊕ OWL/ANS")
app.add_typer(build_app, name="build")


@app.callback()
def main() -> None:
    """CLI principale de recode-icd."""
