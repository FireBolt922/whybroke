from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(language: str | None) -> str:
    name = language if language else "generic"
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        path = _PROMPTS_DIR / "generic.txt"
    return path.read_text(encoding="utf-8")
