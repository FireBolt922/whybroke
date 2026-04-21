---
name: whybroke
description: Diagnose a failing Python program and return a root-cause fix. Use when the user hits a Python exception, stack trace, or traceback — especially in Django, FastAPI, Flask, or plain scripts — and asks "why did this break?", "what's wrong?", "fix this error", or pastes a traceback. Also handles non-Python stack traces (JavaScript/TypeScript, Go, Rust, Ruby) as best-effort LLM analysis without AST extraction.
---

# whybroke

Find the **root cause** of a broken program — not the symptom — and return a minimal fix.

Python gets deep analysis (AST-level function extraction via the `whybroke` CLI when available). Other languages get LLM-only root-cause analysis.

## When to activate

Trigger on any of:
- A traceback or stack trace in the conversation (pasted, in selection, or in recent command output).
- User says "why did this break", "why is this failing", "what's wrong with this error", "fix this exception", "debug this".
- A failing test output with an exception.

Do **not** activate for:
- Syntax errors the user hasn't run yet (let the linter handle it).
- Questions about code style or refactoring.

## Operating modes

Run `scripts/preflight.sh` first. It prints one of:

- `mode=A` — `whybroke` CLI is installed and authenticated. Use the CLI.
- `mode=B reason=not_installed` — CLI missing. Use in-skill analysis. Mention install once.
- `mode=B reason=not_authenticated` — CLI present but `~/.whybroke/credentials.json` missing. Use in-skill analysis. Mention `whybroke auth` once.

**Never run `whybroke auth` yourself.** It's an interactive terminal flow that writes a credential file. The user must run it in their own terminal.

### Mode A: CLI path

1. Write the traceback to a temp file: `/tmp/whybroke-trace-$$.txt`.
2. Run: `whybroke --file /tmp/whybroke-trace-$$.txt`.
3. The CLI returns a Rich-rendered panel with: exception type, confidence score, evidence lines, and a unified diff.
4. Show the diff to the user. Offer to apply it to the relevant file.
5. Optionally suggest `whybroke history` / `whybroke view <id>` for past-session replay (free, no API call).

### Mode B: In-skill analysis (fallback)

Do the analysis yourself using this protocol:

1. **Identify** the exception type and message from the last lines of the traceback.
2. **Locate the deepest user-code frame.** Walk frames bottom-up; skip anything under `site-packages/`, `dist-packages/`, the Python stdlib, or `node_modules/`. The first frame inside the user's project is the one that matters.
3. **Read ±20 lines** around that frame's line number in the actual source file. Use the Read tool.
4. **State the root cause in one sentence** — the *why*, not the *what*.
   - Bad: "TypeError: object NoneType can't be used in 'await' expression"
   - Good: "`get_user()` returns `None` when the user isn't found, but the caller awaits it as if it were a coroutine."
5. **Propose a minimal fix** as an edit or code block. Don't refactor; change only what's needed to resolve the root cause.
6. **Flag uncertainty** if the traceback points outside user code (e.g., a library bug) or if the failing function isn't available on disk.

## One-time install nudge (Mode B only)

If the user doesn't have whybroke installed/authed, say **once per conversation**:

> For auto-generated unified diffs and replayable session history, run this in your terminal:
> ```bash
> pip install whybroke && whybroke auth
> ```
> I'll keep analyzing this one inline.

Do not repeat this on subsequent errors in the same session.

## References

- [references/usage.md](references/usage.md) — examples, CLI subcommands, test fixtures.
