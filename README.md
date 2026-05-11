# 💥 WhyBroke

**Stop copy-pasting stack traces. Fix Python bugs in 8 seconds.**

[![CI](https://github.com/FireBolt922/whybroke/actions/workflows/ci.yml/badge.svg)](https://github.com/FireBolt922/whybroke/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/FireBolt922/whybroke/branch/main/graph/badge.svg)](https://codecov.io/gh/FireBolt922/whybroke)
[![PyPI](https://img.shields.io/pypi/v/whybroke.svg)](https://pypi.org/project/whybroke/)
[![Python](https://img.shields.io/pypi/pyversions/whybroke.svg)](https://pypi.org/project/whybroke/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

WhyBroke is a terminal-native CLI that reads your broken output, finds the
exact failing function on your disk via Python's `ast` module, and prints a
copy-pasteable fix. No dashboards. No SaaS. Just a Unix pipe that actually
understands your code.

<!-- TODO: Replace with demo.gif after recording with asciinema -->
![demo](https://raw.githubusercontent.com/FireBolt922/whybroke/main/docs/demo.gif)

---

## 🚀 Quickstart

```bash
uv pip install whybroke    # or: pip install whybroke
whybroke auth              # stored locally at ~/.whybroke/credentials.json
python my_buggy_script.py 2>&1 | whybroke
node  my_buggy_script.js 2>&1 | whybroke
```

That's it. Pipe anything — Python or JavaScript/TypeScript. **Want it free?** Pick `zai` at the auth prompt — `glm-4.7-flash` is fully free, no card required.

## 🧠 Why not just paste into ChatGPT?

When you paste an error into ChatGPT, the conversation goes:

> _"Can you share the contents of `api.py`?"_

WhyBroke automates that away:

1. **AST context extraction** — parses the traceback, finds the local file, walks the AST, and pulls the exact failing function. Not a ±10 line guess.
2. **Noise reduction** — strips the 500 lines of framework boilerplate before the trace.
3. **Structured output** — the LLM returns a confidence score, evidence lines, and a unified diff. No conversational fluff.
4. **Time travel** — every debug session is saved locally. Run `whybroke view 12` to re-read yesterday's fix for free.

## ⚙️ Commands

| Command | What it does |
|---|---|
| `whybroke auth` | Set up your provider API key (stored at `~/.whybroke/credentials.json`) |
| `<cmd> 2>&1 \| whybroke` | Pipe a trace. Default behaviour. |
| `whybroke --file trace.txt` | Analyze a saved traceback file |
| `whybroke --model gpt-4o` | Override the default model for your provider |
| `whybroke history` | Rich table of your last 10 debug sessions |
| `whybroke view 42` | Re-render session 42 from local cache (no API call) |
| `whybroke --note "flaky in CI"` | Attach a short note while analyzing (shown in `history` and `view`) |
| `whybroke note 42 "fixed by pinning numpy"` | Add, update, or clear (pass `""`) the note on a past session |
| `whybroke clear` | Delete all saved debug sessions (prompts; use `-y` to skip) |
| `whybroke logout` | Remove stored API credentials from `~/.whybroke/credentials.json` |

## 🤖 Providers

BYOK (bring your own key). Supported at V1:

| Provider | Default model | Notes |
|---|---|---|
| `openai` | `gpt-4o-mini` | JSON-mode enforced |
| `anthropic` | `claude-sonnet-4-5` | — |
| `gemini` | `gemini-2.5-flash` | Via `google-genai` SDK |
| `grok` | `grok-4-fast` | xAI — OpenAI-compatible endpoint (`api.x.ai/v1`) |
| `openrouter` | `openrouter/free` | **Free tier** — OpenRouter's meta-router picks a live free model (Gemma 4, Nemotron 3, etc.) and whybroke auto-falls back on rate-limit / 404 / bad JSON. See [docs/free-models.md](docs/free-models.md). |
| `zai` | `glm-4.7-flash` | **Free tier** — Z.ai's GLM-4.7 family direct from `api.z.ai`. Get a key at [z.ai](https://z.ai). GLM-4.7 is a strong agentic-coding model. |
| `nvidia` | `z-ai/glm4.7` | **Free credits** — NVIDIA NIM hosted catalog (`integrate.api.nvidia.com`). Also unlocks Nemotron, Llama-4, Qwen3, DeepSeek-R1. Get a key at [build.nvidia.com](https://build.nvidia.com). |
| `litellm` | *(set with `--model`)* | Universal router — works with Ollama, Bedrock, Groq, etc. Use `--model ollama/llama3` for fully local. |

## 🗣️ Language Support

| Language | Status |
|---|---|
| Python | ✅ Deep (AST extraction) |
| JavaScript / TypeScript | ✅ Deep (tree-sitter extraction) |
| Go | 🗳️ [Vote with 👍](https://github.com/FireBolt922/whybroke/issues/2) |
| Rust | 🗳️ [Vote with 👍](https://github.com/FireBolt922/whybroke/issues/3) |
| Ruby | 🗳️ [Vote with 👍](https://github.com/FireBolt922/whybroke/issues/4) |

Pipe **any** trace — languages without deep support fall back to LLM-only analysis so the pipe always works. V2's scope is determined by the leaderboard above.

## 🔒 Privacy

V1 sends the stack trace and extracted source to whichever provider you configured. Nothing is logged anywhere else. If you don't want your code leaving your machine, use the `litellm` provider with an Ollama model:

```bash
whybroke auth  # choose "litellm"
python my_script.py 2>&1 | whybroke --model ollama/llama3
```

## 🛠️ Contributing

V1's codebase is deliberately boring. The seams for language expansion live in three places:

- [`whybroke/detect.py`](whybroke/detect.py) — add a regex signature to `_SIGNATURES`
- [`whybroke/parsers/`](whybroke/parsers/) — add `{language}.py` returning `list[Frame]`
- [`whybroke/extractors/`](whybroke/extractors/) — V2+ uses a shared tree-sitter extractor
- [`whybroke/prompts/`](whybroke/prompts/) — add `{language}.txt`

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for what's next.

## 🧩 Install as an Agent Skill

WhyBroke is available as an [Agent Skill](https://skills.sh/) — drop it into any skills-aware AI assistant (Claude Code, Cursor, and others) and it'll trigger automatically when you hit a traceback.

```bash
npx skills add FireBolt922/whybroke
```

The skill works in two modes:

- **With the CLI installed and authenticated** — invokes `whybroke --file <trace>` and returns a unified diff.
- **Without it** — falls back to in-skill root-cause analysis (walks the traceback, reads the failing file, explains the root cause, proposes a fix). You'll see a one-time nudge to `pip install whybroke && whybroke auth` for the richer experience.

Skill source: [skills/whybroke/](skills/whybroke/).

## 💻 Platform support

Tested on macOS and Linux. Windows is untested in V1 and may need adjustments to credential-file permissions or path handling — PRs welcome.

## 📄 License

MIT — see [LICENSE](LICENSE).
