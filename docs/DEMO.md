# Recording the Launch Demo

Goal: a ≤15-second asciinema clip that shows the full loop — pipe → extraction →
structured fix. This is the single biggest lever on star conversion, so it's
worth re-taking a few times.

## Tools

```bash
brew install asciinema agg        # or: sudo apt install asciinema && cargo install --git https://github.com/asciinema/agg
uv pip install whybroke           # or install from source
whybroke auth                     # use openai + gpt-4o-mini — fastest response time for the demo
```

## Recording

```bash
asciinema rec -i 1 -t "WhyBroke: pipe any Python error" demo.cast
# run the demo (see script below)
# hit Ctrl-D to stop
agg demo.cast docs/demo.gif --theme monokai --font-size 16 --speed 1.2
```

## Script (read this, perform it — don't narrate)

Keep the terminal prompt short (`$ ` or `➜ `). Use a dark theme.

```bash
# Clear screen, set the stage
clear

# Show the buggy script briefly (optional — keep under 2 seconds)
bat --style=plain scripts/demo_bugs/01_fastapi_async.py | head -20

# Run it. It fails. Pipe the failure into whybroke.
python scripts/demo_bugs/01_fastapi_async.py 2>&1 | whybroke

# Let the panels render fully. Pause 2 seconds on the fix.

# (optional) Show the history feature to prove durability
whybroke history
```

## Choosing the demo bug

We ship three scripts in `scripts/demo_bugs/`. Pick the one where the LLM
response is consistently high-confidence (≥ 90) and the diff is short:

| # | Script | Why it demos well |
|---|---|---|
| 01 | FastAPI async/sync mismatch | One-line fix, 95+ confidence, relatable to web devs |
| 02 | pandas `KeyError` on missing column | Pandas users are a huge audience; diff is a column-name fix |
| 03 | `asyncio` gather with bare coroutine list | Subtle, educational, shows the tool's reasoning chops |

**For the launch GIF, use `01_fastapi_async.py`.** Highest confidence, fastest LLM response.

## Recording checklist

- [ ] Terminal width set to **100 cols** (matches Rich's default non-tty width; keeps rendering consistent).
- [ ] Terminal height set to **32 rows**.
- [ ] Font size ≥ 16pt in `agg` so it's legible at GitHub's display size.
- [ ] Re-record if the spinner stalls or the LLM takes > 8 seconds — retake with a warmer prompt cache.
- [ ] Clip the GIF to the moment `whybroke` finishes rendering. Don't show the trailing shell prompt.
- [ ] Optimize: `gifsicle -O3 --lossy=80 docs/demo.gif -o docs/demo.gif` to keep it under 1 MB for README loading.

## If asciinema is overkill

Plan B: [vhs](https://github.com/charmbracelet/vhs). Scriptable, produces GIFs directly. Example tape:

```vhs
# docs/demo.tape
Output docs/demo.gif
Set FontSize 16
Set Width 1000
Set Height 600
Set Theme "Monokai"
Type "python scripts/demo_bugs/01_fastapi_async.py 2>&1 | whybroke"
Sleep 500ms
Enter
Sleep 10s
```

Then: `vhs docs/demo.tape`.
