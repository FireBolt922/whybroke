# Launch Copy

Drafts for the V1 launch. Post sequence:

1. **09:00 ET** — Show HN
2. **09:30 ET** — Twitter thread
3. **10:00 ET** — r/Python (reuse Reddit-angle copy below)
4. **All day** — respond to every comment within 30 minutes. This is the multiplier.

---

## Show HN

**Title (pick one, max 80 chars):**

- `Show HN: WhyBroke – pipe any Python error, get the fix in 8 seconds`
- `Show HN: WhyBroke – a Unix pipe for debugging Python`
- `Show HN: WhyBroke – terminal-native AI debugger that reads your local code`

Recommended: option 1. It's concrete, time-bound, and leads with the verb.

**First comment (self-reply, posted immediately after submission):**

> Hi HN — author here.
>
> I built this because I was tired of the paste-into-ChatGPT loop. Every time
> I hit a stack trace, I'd copy it, paste it, then ChatGPT would ask "can you
> show me api.py?" — so I'd go copy the file, paste again, repeat.
>
> WhyBroke does that loop automatically. When you pipe a Python error in, it:
>
> 1. Strips the 500 lines of framework noise
> 2. Parses the traceback, finds the last local file, walks its AST, and
>    extracts the *exact* failing function (not a ±10 line guess)
> 3. Sends that to the LLM with a JSON-enforced prompt
> 4. Saves the result to a local SQLite DB so `whybroke view 12` replays
>    yesterday's fix for free
>
> V1 is Python-only for the AST path, but it **also** accepts any trace
> (Node, Go, Rust) as a generic fallback — the pipe always works. The
> README has a GitHub 👍 vote for which language gets deep support next.
>
> Stack: Typer + Rich + stdlib `ast` + stdlib `sqlite3`. 8 files of real
> code, pure-Python install, BYOK (OpenAI, Anthropic, Gemini, or anything
> LiteLLM supports — including a local Ollama model). Source under MIT.
>
> Happy to answer anything. Please be brutal with feedback.

---

## Twitter / X thread (5 tweets)

**Tweet 1 — the hook (pin the demo GIF here):**

> Stop pasting stack traces into ChatGPT.
>
> WhyBroke is a Unix pipe that reads your broken terminal output, walks your
> code's AST to pull the exact failing function, and prints the fix. Locally.
>
> `python app.py 2>&1 | whybroke`
>
> [GIF attached]

**Tweet 2 — why it's different:**

> The move is AST extraction, not vibes.
>
> Most "AI debugger" tools paste your trace into a chat. WhyBroke parses the
> traceback, opens the file mentioned on the last frame, and uses Python's
> built-in `ast` to pull the *exact* enclosing function. The LLM sees code,
> not guesses.

**Tweet 3 — the drawer you didn't know you needed:**

> Every debug session is saved locally.
>
> `whybroke history` — see your last 10 fixes.
> `whybroke view 12` — re-read yesterday's fix. Zero API cost.
>
> The tool is boring in the best way: stdlib sqlite3, no ORM, 8 files of real code.

**Tweet 4 — provider flex:**

> BYOK. Choose your backend:
>
> - `openai` → gpt-4o-mini
> - `anthropic` → Claude Sonnet 4.5
> - `gemini` → 2.5 Flash
> - `litellm` → anything, including `ollama/llama3` for fully local
>
> Nothing leaves your machine if you don't want it to.

**Tweet 5 — roadmap + CTA:**

> V1 ships Python deep, JS/TS next. Vote on the README for what gets
> AST support in V2 — JS, Go, Rust, Ruby.
>
> MIT-licensed. `pip install whybroke`.
>
> https://github.com/FireBolt922/whybroke

---

## r/Python post

**Title:** `WhyBroke: a terminal-native AI debugger that uses Python's ast module to extract the exact failing function`

**Body:**

> Hey r/Python,
>
> I wanted a debugger that didn't make me paste things into a web chat. So
> I built one that lives in the shell.
>
> When you pipe a stack trace in, WhyBroke walks the last frame's file with
> `ast.walk` and pulls the enclosing `FunctionDef` / `AsyncFunctionDef` /
> `ClassDef` — the whole body, not a ±10 line slice. That structured context
> goes to the LLM with a JSON-enforced prompt, and the output lands as a
> Rich-formatted panel with a unified diff.
>
> Two things I think are interesting from a Python perspective:
>
> 1. **No ORM.** Session history is stdlib `sqlite3`. The whole storage layer
>    is ~40 lines.
> 2. **Innermost-wins extraction.** If a target line is inside a method
>    inside a class, both the class def and the method def match. I pick the
>    one with the smaller source span, so the prompt gets the method body,
>    not the entire class. It makes the diffs noticeably tighter.
>
> Source: https://github.com/FireBolt922/whybroke
>
> Feedback welcome — especially on edge cases in the AST extraction.

---

## r/LocalLLaMA post (optional, save for V2.5 Ollama launch)

**Title:** `WhyBroke now supports Ollama — AI debugger that never leaves your laptop`

(Keep this in pocket for the V2.5 beat, not V1.)

---

## Metrics to watch first 48h

| Metric | Why |
|---|---|
| Stars/hour curve | Primary north-star metric |
| HN rank | 60-minute window for front-page entry |
| PyPI install count | Proxy for real trial, not just stars |
| GitHub issue #1 (JS vote) reactions | Informs V2 start decision |
| Reddit comment sentiment | Catches quality complaints early |
| Rate-limit errors in error logs | Watch for "LLM quality" blowback (if any) |

## First 48h playbook

- **Respond within 30 min** to every HN comment for the first 6 hours.
- **Thank-and-triage** for bugs. Don't over-explain. File an issue, promise a fix.
- **Pin** the 4 language-vote issues before posting. They only work if they already exist.
- **Do not** engage with "why not Sentry" takes beyond one polite reply — they're a noise sink.
- If a blocker bug surfaces in the first hour, **pull the post**, fix, repost tomorrow. Better than leaving a broken first impression.
