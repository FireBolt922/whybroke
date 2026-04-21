from datetime import datetime, timezone

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


def _format_local_time(ts: str) -> str:
    """Convert SQLite's UTC CURRENT_TIMESTAMP string to local time for display."""
    if not ts:
        return "—"
    try:
        dt_utc = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return ts
    return dt_utc.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def render_analysis(result: dict, console: Console | None = None) -> None:
    console = console or Console()

    confidence = int(result.get("confidence_score", 0))
    exc_type = result.get("exception_type", "Unknown")
    header = Text.assemble(
        ("🎯 Confidence: ", "bold"),
        (f"{confidence}%", _confidence_style(confidence)),
    )
    console.print(
        Panel(
            Text(f"Exception: {exc_type}"),
            title=header,
            border_style=_confidence_style(confidence),
        )
    )

    evidence = result.get("evidence_lines", []) or []
    if evidence:
        body = "\n".join(f"• {line}" for line in evidence)
        console.print(Panel(body, title="🔎 Evidence", border_style="cyan"))

    root_cause = result.get("root_cause", "")
    if root_cause:
        console.print(
            Panel(Text(root_cause), title="🚨 Root Cause", border_style="red")
        )

    reasoning = result.get("reasoning", "")
    if reasoning:
        console.print(
            Panel(Text(reasoning), title="🧠 Reasoning", border_style="magenta")
        )

    fix = result.get("suggested_fix", "")
    if fix:
        if _looks_like_diff(fix):
            rendered = Syntax(fix, "diff", theme="ansi_dark", line_numbers=False)
        else:
            rendered = Text(fix)
        console.print(Panel(rendered, title="🛠️  Suggested Fix", border_style="green"))


def render_history(sessions: list, console: Console | None = None) -> None:
    console = console or Console()
    if not sessions:
        console.print("[yellow]No sessions yet. Pipe an error in to get started.[/yellow]")
        return

    table = Table(title="Recent Debug Sessions", show_lines=False)
    table.add_column("ID", style="bold", justify="right")
    table.add_column("When", style="dim")
    table.add_column("Exception")
    table.add_column("Confidence", justify="right")
    table.add_column("Notes", style="dim", max_width=30)

    for s in sessions:
        conf = s.confidence_score
        conf_str = f"{conf}%" if conf is not None else "—"
        comments = getattr(s, "comments", "") or ""
        note_cell = comments if len(comments) <= 30 else comments[:27] + "..."
        table.add_row(
            str(s.id),
            _format_local_time(str(s.timestamp)),
            s.exception_type or "—",
            Text(conf_str, style=_confidence_style(conf or 0)),
            note_cell,
        )
    console.print(table)


def render_note(text: str, console: Console | None = None) -> None:
    console = console or Console()
    console.print(Panel(Text(text), title="📝 Notes", border_style="blue"))


def _confidence_style(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


def _looks_like_diff(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("- ", "+ ", "-", "+")) and not stripped.startswith(("++", "--")):
            return True
    return False
