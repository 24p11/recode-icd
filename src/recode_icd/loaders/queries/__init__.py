from importlib.resources import files


def load_query(name: str) -> str:
    return files(__package__).joinpath(f"{name}.rq").read_text(encoding="utf-8")
