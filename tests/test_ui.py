from io import StringIO

from rich.console import Console

from whybroke.storage import Session
from whybroke.ui import _format_local_time, render_analysis, render_history, render_note

SAMPLE = {
    "exception_type": "TypeError",
    "confidence_score": 92,
    "root_cause": "You are awaiting a synchronous function.",
    "reasoning": "The trace shows await on get_user_sync which returns a dict.",
    "evidence_lines": [
        'File "./src/routes/users.py", line 52, in get_user',
        "user_data = await db.get_user_sync(user_id)",
    ],
    "suggested_fix": "- user_data = await db.get_user_sync(user_id)\n+ user_data = db.get_user_sync(user_id)",
}


def _capture(render_fn, *args) -> str:
    buf = StringIO()
    console = Console(file=buf, width=100, force_terminal=False, color_system=None)
    render_fn(*args, console=console)
    return buf.getvalue()


def test_renders_all_panels():
    output = _capture(render_analysis, SAMPLE)
    assert "92%" in output
    assert "TypeError" in output
    assert "synchronous function" in output
    assert "await db.get_user_sync" in output
    assert "get_user_sync(user_id)" in output


def test_renders_low_confidence_in_red_tone():
    low = {**SAMPLE, "confidence_score": 30}
    output = _capture(render_analysis, low)
    assert "30%" in output


def test_renders_minimal_result_without_crashing():
    minimal = {
        "exception_type": "ValueError",
        "confidence_score": 50,
        "root_cause": "",
        "reasoning": "",
        "evidence_lines": [],
        "suggested_fix": "",
    }
    output = _capture(render_analysis, minimal)
    assert "ValueError" in output
    assert "50%" in output


def test_renders_history_table():
    sessions = [
        Session(
            id=1,
            timestamp="2026-04-18 10:00:00",
            raw_input="",
            ast_context="",
            exception_type="TypeError",
            confidence_score=92,
            llm_response={},
        ),
        Session(
            id=2,
            timestamp="2026-04-18 10:05:00",
            raw_input="",
            ast_context="",
            exception_type="KeyError",
            confidence_score=65,
            llm_response={},
        ),
    ]
    output = _capture(render_history, sessions)
    assert "TypeError" in output
    assert "KeyError" in output
    assert "92%" in output
    assert "65%" in output


def test_renders_empty_history():
    output = _capture(render_history, [])
    assert "No sessions" in output


def test_renders_history_with_notes_column():
    sessions = [
        Session(
            id=1,
            timestamp="2026-04-18 10:00:00",
            raw_input="",
            ast_context="",
            exception_type="TypeError",
            confidence_score=92,
            llm_response={},
            comments="short note",
        ),
        Session(
            id=2,
            timestamp="2026-04-18 10:05:00",
            raw_input="",
            ast_context="",
            exception_type="KeyError",
            confidence_score=65,
            llm_response={},
            comments="x" * 60,
        ),
    ]
    output = _capture(render_history, sessions)
    assert "Notes" in output
    assert "short note" in output
    assert "..." in output


def test_format_local_time_converts_utc_to_local():
    from datetime import datetime, timezone

    utc_str = "2026-04-20 09:52:32"
    got = _format_local_time(utc_str)
    # Parse both back and assert they refer to the same instant.
    expected_instant = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S").replace(
        tzinfo=timezone.utc
    )
    got_local = datetime.strptime(got, "%Y-%m-%d %H:%M:%S").astimezone()
    assert got_local.replace(tzinfo=got_local.tzinfo).timestamp() == expected_instant.timestamp()


def test_format_local_time_empty_and_malformed():
    assert _format_local_time("") == "—"
    assert _format_local_time("not-a-date") == "not-a-date"


def test_render_note_panel():
    buf = StringIO()
    console = Console(file=buf, width=100, force_terminal=False, color_system=None)
    render_note("fixed by pinning numpy", console=console)
    output = buf.getvalue()
    assert "Notes" in output
    assert "fixed by pinning numpy" in output
