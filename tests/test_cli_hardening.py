import json

import pytest
from typer.testing import CliRunner

from whybroke import cli, config, storage
from whybroke.cli import _error_hint

RUNNER = CliRunner()


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    config_dir = tmp_path / ".whybroke"
    db_path = config_dir / "history.db"
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CREDENTIALS_PATH", config_dir / "credentials.json")
    monkeypatch.setattr(storage, "DEFAULT_DB_PATH", db_path)
    # Rebind function defaults so callers that omit db_path hit the temp DB.
    for fn in (
        storage.init_db,
        storage.save_session,
        storage.clear_history,
        storage.update_comment,
        storage.get_session,
        storage.list_recent,
    ):
        new_defaults = tuple(
            db_path if isinstance(d, type(db_path)) and d.name == "history.db" else d
            for d in (fn.__defaults__ or ())
        )
        monkeypatch.setattr(fn, "__defaults__", new_defaults)
    config_dir.mkdir(parents=True)
    (config_dir / "credentials.json").write_text(
        json.dumps({"provider": "openai", "api_key": "sk-test"})
    )
    return config_dir


def test_keyboard_interrupt_exits_cleanly(isolated_home, monkeypatch, fixtures_dir):
    def boom(**kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(cli, "analyze", boom)
    trace = (fixtures_dir / "python_traceback.txt").read_text()
    result = RUNNER.invoke(cli.app, [], input=trace)
    assert result.exit_code == 130
    assert "Cancelled" in result.output


def test_generic_exception_shows_typename_and_hint(isolated_home, monkeypatch, fixtures_dir):
    class RateLimitError(Exception):
        pass

    def boom(**kwargs):
        raise RateLimitError("429 Too Many Requests")

    monkeypatch.setattr(cli, "analyze", boom)
    trace = (fixtures_dir / "python_traceback.txt").read_text()
    result = RUNNER.invoke(cli.app, [], input=trace)
    assert result.exit_code == 1
    assert "RateLimitError" in result.output
    assert "rate limit" in result.output.lower()


def test_error_hint_matches_known_exception_names():
    assert "API key" in _error_hint("AuthenticationError", "")
    assert "rate limit" in _error_hint("RateLimitError", "").lower()
    assert "Network" in _error_hint("APIConnectionError", "")


def test_error_hint_falls_back_to_message_text():
    assert _error_hint("CustomErr", "request timed out after 60s") != ""
    assert _error_hint("CustomErr", "Invalid API key provided") != ""
    assert _error_hint("CustomErr", "something random") == ""


def test_file_not_found_for_minus_f(isolated_home, tmp_path):
    result = RUNNER.invoke(cli.app, ["--file", str(tmp_path / "nope.txt")])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


def test_note_command_updates_session(isolated_home):
    sample = {"exception_type": "TypeError", "confidence_score": 80}
    sid = storage.save_session("raw", "", sample)
    result = RUNNER.invoke(cli.app, ["note", str(sid), "flaky in CI"])
    assert result.exit_code == 0
    assert "updated" in result.output.lower()
    session = storage.get_session(sid)
    assert session is not None
    assert session.comments == "flaky in CI"


def test_note_command_clear(isolated_home):
    sample = {"exception_type": "TypeError", "confidence_score": 80}
    sid = storage.save_session("raw", "", sample, comments="old")
    result = RUNNER.invoke(cli.app, ["note", str(sid), ""])
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()
    session = storage.get_session(sid)
    assert session is not None
    assert session.comments == ""


def test_note_command_missing_id_exits_1(isolated_home):
    result = RUNNER.invoke(cli.app, ["note", "999999", "hi"])
    assert result.exit_code == 1
    assert "no session" in result.output.lower()


def test_clear_command_with_yes_flag(isolated_home):
    sample = {"exception_type": "TypeError", "confidence_score": 80}
    for _ in range(3):
        storage.save_session("raw", "", sample)
    result = RUNNER.invoke(cli.app, ["clear", "--yes"])
    assert result.exit_code == 0
    assert "cleared 3" in result.output.lower()
    assert storage.list_recent() == []


def test_clear_command_prompts_and_aborts_on_no(isolated_home):
    sample = {"exception_type": "TypeError", "confidence_score": 80}
    storage.save_session("raw", "", sample)
    result = RUNNER.invoke(cli.app, ["clear"], input="n\n")
    assert result.exit_code == 1
    assert "aborted" in result.output.lower()
    assert len(storage.list_recent()) == 1


def test_clear_command_prompts_and_confirms_on_yes(isolated_home):
    sample = {"exception_type": "TypeError", "confidence_score": 80}
    storage.save_session("raw", "", sample)
    result = RUNNER.invoke(cli.app, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert "cleared 1" in result.output.lower()
    assert storage.list_recent() == []


def test_logout_removes_credentials(isolated_home):
    assert (isolated_home / "credentials.json").exists()
    result = RUNNER.invoke(cli.app, ["logout"])
    assert result.exit_code == 0
    assert "removed" in result.output.lower()
    assert not (isolated_home / "credentials.json").exists()


def test_logout_when_no_credentials(isolated_home):
    (isolated_home / "credentials.json").unlink()
    result = RUNNER.invoke(cli.app, ["logout"])
    assert result.exit_code == 0
    assert "no credentials" in result.output.lower()


def test_analyze_note_flag_persists(isolated_home, monkeypatch, fixtures_dir):
    fake_result = {
        "exception_type": "TypeError",
        "confidence_score": 90,
        "root_cause": "x",
        "reasoning": "y",
        "evidence_lines": [],
        "suggested_fix": "",
    }

    def fake_analyze(**kwargs):
        return fake_result

    monkeypatch.setattr(cli, "analyze", fake_analyze)
    trace = (fixtures_dir / "python_traceback.txt").read_text()
    result = RUNNER.invoke(cli.app, ["--note", "repro on mac only"], input=trace)
    assert result.exit_code == 0
    sessions = storage.list_recent(limit=1)
    assert sessions and sessions[0].comments == "repro on mac only"
