import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt

from whybroke import __version__
from whybroke.config import (
    SUPPORTED_PROVIDERS,
    ConfigError,
    delete_credentials,
    load_credentials,
    save_credentials,
)
from whybroke.detect import detect_language
from whybroke.ecosystem import detect_framework, run_checks
from whybroke.extractors.python_ast import get_failing_context
from whybroke.llm import LLMProviderError, LLMResponseError, analyze
from whybroke.parsers.python import extract_exception_type, parse_python_trace
from whybroke.preprocess import strip_noise
from whybroke.prompts import load_prompt
from whybroke.storage import (
    clear_history,
    get_session,
    list_recent,
    save_session,
    update_comment,
)
from whybroke.teach import render_lesson, should_show_lesson
from whybroke.ui import _format_local_time, render_analysis, render_ecosystem_notes, render_history, render_note

app = typer.Typer(
    name="whybroke",
    help="Pipe any stack trace, get the fix in 8 seconds.",
    no_args_is_help=False,
    add_completion=False,
)
console = Console()
err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"whybroke {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    file: Optional[str] = typer.Option(
        None, "--file", "-f", help="Read traceback from file instead of stdin."
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Override the default model for your provider."
    ),
    note: Optional[str] = typer.Option(
        None, "--note", "-N", help="Attach a note to this session."
    ),
    learn: Optional[bool] = typer.Option(
        None,
        "--learn/--no-learn",
        help="Show pattern lesson block. Default: on in TTY, off when piped.",
    ),
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=_version_callback, is_eager=True
    ),
) -> None:
    if ctx.invoked_subcommand is None:
        _run_analyze(file, model, note, learn)


@app.command()
def auth() -> None:
    """Configure your LLM provider API key."""
    providers_str = "/".join(SUPPORTED_PROVIDERS)
    provider = Prompt.ask(
        f"Provider ({providers_str})",
        choices=list(SUPPORTED_PROVIDERS),
        default="openai",
    )
    api_key = Prompt.ask(f"Enter {provider} API key", password=True)
    if not api_key.strip():
        err_console.print("[red]API key cannot be empty.[/red]")
        raise typer.Exit(code=1)
    save_credentials(provider, api_key.strip())
    console.print(f"[green]✓[/green] Saved {provider} credentials.")


@app.command(name="analyze")
def analyze_cmd(
    file: Optional[str] = typer.Option(None, "--file", "-f"),
    model: Optional[str] = typer.Option(None, "--model", "-m"),
    note: Optional[str] = typer.Option(
        None, "--note", "-N", help="Attach a note to this session."
    ),
    learn: Optional[bool] = typer.Option(
        None,
        "--learn/--no-learn",
        help="Show pattern lesson block. Default: on in TTY, off when piped.",
    ),
) -> None:
    """Analyze a traceback from stdin or a file."""
    _run_analyze(file, model, note, learn)


@app.command()
def history(limit: int = typer.Option(10, "--limit", "-n")) -> None:
    """Show recent debug sessions."""
    sessions = list_recent(limit=limit)
    render_history(sessions, console=console)


@app.command()
def view(session_id: int) -> None:
    """Re-render a past session by ID (no API call)."""
    session = get_session(session_id)
    if session is None:
        err_console.print(f"[red]No session with id={session_id}.[/red]")
        raise typer.Exit(code=1)
    console.print(
        f"[dim]Session {session.id} — {_format_local_time(str(session.timestamp))}[/dim]\n"
    )
    render_analysis(session.llm_response, console=console)
    if session.comments:
        render_note(session.comments, console=console)


@app.command()
def note(
    session_id: int,
    text: str = typer.Argument("", help="Note text. Pass empty string to clear."),
) -> None:
    """Add, update, or clear the note on a past session."""
    if update_comment(session_id, text):
        if text:
            console.print(f"[green]✓[/green] Note updated for session {session_id}.")
        else:
            console.print(f"[green]✓[/green] Note cleared for session {session_id}.")
    else:
        err_console.print(f"[red]No session with id={session_id}.[/red]")
        raise typer.Exit(code=1)


@app.command()
def clear(
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt."
    ),
) -> None:
    """Delete all saved debug sessions from the local history database."""
    if not yes:
        confirmed = typer.confirm(
            "This will delete ALL saved debug sessions. Continue?", default=False
        )
        if not confirmed:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(code=1)
    deleted = clear_history()
    console.print(f"[green]✓[/green] Cleared {deleted} session(s) from history.")


@app.command()
def logout() -> None:
    """Remove stored API credentials from ~/.whybroke/credentials.json."""
    if delete_credentials():
        console.print("[green]✓[/green] Credentials removed.")
    else:
        console.print("[yellow]No credentials were stored.[/yellow]")


_ERROR_HINTS = {
    "AuthenticationError": "Check your API key with `whybroke auth`.",
    "PermissionDeniedError": "Your API key is valid but lacks access to this model.",
    "RateLimitError": "You've hit a rate limit. Wait a moment and retry, or switch provider.",
    "APIConnectionError": "Network issue reaching the provider. Check your connection.",
    "APITimeoutError": "Provider timed out. Retry, or try a smaller trace.",
    "NotFoundError": "Model not found. Try `--model` with a different name.",
    "BadRequestError": "Provider rejected the request. The trace may be too large.",
}


def _error_hint(exc_name: str, message: str) -> str:
    if exc_name in _ERROR_HINTS:
        return _ERROR_HINTS[exc_name]
    lower = message.lower()
    if "rate limit" in lower or "429" in lower:
        return _ERROR_HINTS["RateLimitError"]
    if "timeout" in lower or "timed out" in lower:
        return _ERROR_HINTS["APITimeoutError"]
    if "connection" in lower or "network" in lower:
        return _ERROR_HINTS["APIConnectionError"]
    if "authentication" in lower or "invalid api key" in lower or "401" in lower:
        return _ERROR_HINTS["AuthenticationError"]
    return ""


def _read_input(file: Optional[str]) -> str:
    if file:
        path = Path(file)
        if not path.exists():
            err_console.print(f"[red]File not found: {file}[/red]")
            raise typer.Exit(code=1)
        return path.read_text(encoding="utf-8", errors="replace")
    if sys.stdin.isatty():
        err_console.print(
            "[yellow]No input. Pipe a traceback in, or use --file.[/yellow]\n"
            "[dim]Example:  python my_script.py 2>&1 | whybroke[/dim]"
        )
        raise typer.Exit(code=1)
    return sys.stdin.read()


def _run_analyze(
    file: Optional[str],
    model: Optional[str],
    note: Optional[str] = None,
    learn: Optional[bool] = None,
) -> None:
    raw = _read_input(file)
    if not raw.strip():
        err_console.print("[red]Empty input.[/red]")
        raise typer.Exit(code=1)

    try:
        creds = load_credentials()
    except ConfigError as e:
        err_console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=1)

    provider = creds["provider"]
    api_key = creds["api_key"]

    with console.status("[cyan]🔍 Parsing traceback...", spinner="dots"):
        clean = strip_noise(raw)
        language = detect_language(clean)

    ast_context = ""
    user_content = clean
    failing_file: Optional[str] = None

    if language == "python":
        frames = parse_python_trace(clean)
        if frames:
            last = frames[-1]
            failing_file = last.filepath
            with console.status(
                f"[cyan]📂 Extracting AST context from {last.filepath}...",
                spinner="dots",
            ):
                ast_context = get_failing_context(last.filepath, last.lineno)
            if ast_context:
                user_content = (
                    f"Stack trace:\n{clean}\n\n"
                    f"Source code (extracted via AST) for the failing function "
                    f"at {last.filepath}:{last.lineno}:\n"
                    f"```python\n{ast_context}\n```"
                )

    # --- Ecosystem checks (deterministic, no LLM) ---
    with console.status("[cyan]🔬 Running ecosystem checks...", spinner="dots"):
        eco_notes = run_checks(trace=clean, failing_file=failing_file)
        framework = detect_framework()

    render_ecosystem_notes(eco_notes, console=console)

    # Inject 1-line summaries into the LLM prompt (not raw files)
    context_notes: list[str] = [n.prompt_note for n in eco_notes]
    if framework:
        context_notes.append(f"Framework: {framework} project detected.")
    if context_notes:
        user_content += "\n\nContext notes:\n" + "\n".join(f"- {c}" for c in context_notes)

    prompt_name = "python" if (language == "python" and ast_context) else "generic"
    system_prompt = load_prompt(prompt_name)

    try:
        with console.status(f"[cyan]🧠 Asking {provider}...", spinner="dots"):
            result = analyze(
                system_prompt=system_prompt,
                user_content=user_content,
                provider=provider,
                api_key=api_key,
                model=model,
            )
    except KeyboardInterrupt:
        err_console.print("\n[yellow]Cancelled.[/yellow]")
        raise typer.Exit(code=130)
    except LLMResponseError as e:
        err_console.print(f"[red]LLM returned malformed data:[/red] {e}")
        if e.raw_response:
            err_console.print(f"[dim]Raw response (first 500 chars):[/dim]\n{e.raw_response[:500]}")
        raise typer.Exit(code=1)
    except LLMProviderError as e:
        err_console.print(f"[red]Provider error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        kind = type(e).__name__
        hint = _error_hint(kind, str(e))
        err_console.print(f"[red]{kind}:[/red] {e}")
        if hint:
            err_console.print(f"[dim]{hint}[/dim]")
        raise typer.Exit(code=1)

    if "exception_type" not in result or not result.get("exception_type"):
        result["exception_type"] = extract_exception_type(clean) or "Unknown"

    session_id = save_session(
        raw_input=raw,
        ast_context=ast_context,
        llm_response=result,
        comments=note or "",
    )

    render_analysis(result, console=console)

    # --- Pattern lesson (TTY-smart, optional) ---
    if should_show_lesson(learn):
        lesson = result.get("lesson")
        if lesson:
            render_lesson(lesson, console=console)

    if note:
        render_note(note, console=console)
    console.print(
        f"\n[dim]Session saved. Run [bold]whybroke view {session_id}[/bold] to see this again.[/dim]"
    )


if __name__ == "__main__":
    app()
