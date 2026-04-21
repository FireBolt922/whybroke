import json
import os
import stat
from pathlib import Path

CONFIG_DIR = Path.home() / ".whybroke"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"

SUPPORTED_PROVIDERS = (
    "openai",
    "anthropic",
    "gemini",
    "grok",
    "openrouter",
    "litellm",
)


class ConfigError(Exception):
    pass


def load_credentials() -> dict:
    if not CREDENTIALS_PATH.exists():
        raise ConfigError(
            "No credentials found. Run `whybroke auth` to set up your API key."
        )
    return json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))


def save_credentials(provider: str, api_key: str) -> None:
    if provider not in SUPPORTED_PROVIDERS:
        raise ConfigError(
            f"Unsupported provider '{provider}'. Choose from: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"provider": provider, "api_key": api_key}
    CREDENTIALS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    try:
        os.chmod(CREDENTIALS_PATH, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def delete_credentials() -> bool:
    if not CREDENTIALS_PATH.exists():
        return False
    CREDENTIALS_PATH.unlink()
    return True
