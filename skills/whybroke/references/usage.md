# whybroke skill — usage reference

## CLI subcommands (Mode A)

| Command | Purpose |
|---|---|
| `whybroke auth` | **User runs this in their terminal.** Interactive provider + API key setup. |
| `whybroke --file <path>` | Analyze a saved traceback. This is what the skill invokes in Mode A. |
| `<cmd> 2>&1 \| whybroke` | Unix-pipe invocation. The skill prefers `--file` since it's deterministic. |
| `whybroke --model <name>` | Override the default model. |
| `whybroke history` | Last 10 sessions in a Rich table. |
| `whybroke view <id>` | Re-render a past session (no API call, free). |
| `whybroke note <id> "text"` | Attach a note to a past session. |

## Providers (set via `whybroke auth`)

`openai`, `anthropic`, `gemini`, `grok`, `openrouter` (has a free tier), `litellm` (universal router — use with `ollama/llama3` for fully local / offline).

## Language coverage

| Language | Mode A behavior | Mode B behavior |
|---|---|---|
| Python | AST extraction + LLM diff | Inline root-cause analysis (this skill) |
| JavaScript / TypeScript | LLM-only fallback inside CLI | Inline root-cause analysis |
| Go / Rust / Ruby | LLM-only fallback inside CLI | Inline root-cause analysis |

## Test fixtures (in the whybroke repo's `examples/` directory)

Each script intentionally raises a specific exception. Use them to verify the skill triggers correctly:

- `01_type_error.py` — `TypeError` (string + int).
- `02_key_error.py` — `KeyError` (missing dict key).
- `03_await_on_sync.py` — `TypeError` (await on non-coroutine).
- `04_zero_division.py` — `ZeroDivisionError`.
- `05_attribute_error.py` — `AttributeError`.

Invoke an example with `python examples/02_key_error.py` from the whybroke repo root and let the skill handle the traceback.

## Config paths

- `~/.whybroke/credentials.json` — provider + API key. Absence ⇒ Mode B.
- `~/.whybroke/sessions.db` — SQLite session cache used by `history` / `view`.
