# WhyBroke Roadmap

Anything that lands here is explicitly **not** part of V1. This file is the
pressure valve for scope creep during the 1–2 week V1 build — if an idea
looks appealing mid-build, it goes here, not into the code.

## V2 — JavaScript / TypeScript

- Add `whybroke/parsers/javascript.py` returning `list[Frame]`.
- Add `whybroke/extractors/tree_sitter.py` (generic, grammar-driven).
- Add `tree-sitter` + `tree-sitter-javascript` + `tree-sitter-typescript` as deps.
- Extend `detect.py` dispatch with JS signatures.
- Add `prompts/javascript.txt`.
- Launch: "WhyBroke now speaks JavaScript."

## V2.5 — Local model support (Ollama)

- Auto-detect running Ollama instance.
- Offer as a provider in `whybroke auth`.
- Launch frame: "WhyBroke runs fully local now — nothing leaves your machine."

## V3+ — Vote-winner language (Go / Rust / Ruby / …)

- Determined by README GitHub-reaction leaderboard.
- Reuse tree-sitter extractor from V2.

## V4+ — Framework presets

- Tuned preprocessors / prompts for: Next.js, FastAPI, Django, Rails.
- Each ships as its own launch beat.

## Considered and rejected for V1

- Full-stack trace stitching (frontend ↔ backend correlation).
- SaaS dashboards / hosted free tier.
- Git integration / automatic PR creation.
- Vector DB / RAG.
- Multi-agent orchestration.
- IDE plugins.
- Windows-specific code paths (V1 leaves Windows untested).
- Telemetry / analytics (reconsider post-V2).
