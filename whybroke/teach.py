from __future__ import annotations

import sys

from rich.console import Console, Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text


def should_show_lesson(override: bool | None = None) -> bool:
    """Return True when the lesson block should be shown.

    Explicit --learn / --no-learn flags take precedence.
    Default: on when stdout is an interactive TTY, off when piped (CI, scripts).
    """
    if override is not None:
        return override
    return sys.stdout.isatty()


def render_lesson(lesson: dict, console: Console) -> None:
    """Render the Pattern Lesson block from the LLM-generated lesson dict."""
    if not lesson or not isinstance(lesson, dict):
        return

    pattern_name = lesson.get("pattern_name", "").strip()
    broken = lesson.get("broken_snippet", "").strip()
    why = lesson.get("why_it_bites", "").strip()
    fix = lesson.get("fix_snippet", "").strip()

    if not (pattern_name and broken and fix):
        return

    parts: list = []
    if why:
        parts.append(Text(f"Why: {why}", style="italic"))
        parts.append(Text(""))

    parts.append(Text("Bug pattern:", style="bold red"))
    parts.append(Syntax(broken, "python", theme="ansi_dark", line_numbers=False))
    parts.append(Text(""))
    parts.append(Text("Canonical fix:", style="bold green"))
    parts.append(Syntax(fix, "python", theme="ansi_dark", line_numbers=False))
    parts.append(Text(""))
    parts.append(Text("Illustrative pattern — not a runnable test.", style="dim"))

    console.print(
        Panel(
            Group(*parts),
            title=f"[bold blue]📚 Pattern Lesson[/bold blue] — {pattern_name}",
            border_style="blue",
        )
    )
