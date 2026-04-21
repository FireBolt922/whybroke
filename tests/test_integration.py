import json

import pytest
from typer.testing import CliRunner

from whybroke import cli, config, storage

RUNNER = CliRunner()

SAMPLE_RESPONSE = {
    "exception_type": "TypeError",
    "confidence_score": 92,
    "root_cause": "await used on a synchronous function",
    "reasoning": "The trace shows await applied to get_user_sync which returns a dict.",
    "evidence_lines": ["user_data = await db.get_user_sync(user_id)"],
    "suggested_fix": "- user_data = await db.get_user_sync(user_id)\n+ user_data = db.get_user_sync(user_id)",
}


@pytest.fixture
def isolated_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    config_dir = home / ".whybroke"
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CREDENTIALS_PATH", config_dir / "credentials.json")
    monkeypatch.setattr(storage, "DEFAULT_DB_PATH", config_dir / "history.db")
    # write credentials
    config_dir.mkdir(parents=True)
    (config_dir / "credentials.json").write_text(
        json.dumps({"provider": "openai", "api_key": "sk-test"})
    )
    return config_dir


@pytest.fixture
def mocked_llm(monkeypatch):
    calls = []

    def fake_analyze(**kwargs):
        calls.append(kwargs)
        return dict(SAMPLE_RESPONSE)

    monkeypatch.setattr(cli, "analyze", fake_analyze)
    return calls


def test_python_pipeline_end_to_end(isolated_home, mocked_llm, fixtures_dir):
    trace = (fixtures_dir / "python_traceback.txt").read_text()
    result = RUNNER.invoke(cli.app, [], input=trace)
    assert result.exit_code == 0, result.output
    assert "92%" in result.output
    assert "TypeError" in result.output
    assert "Session saved" in result.output
    # prompt was python-flavored because AST extraction may or may not succeed
    # (files in fixture don't exist locally) — but language detection worked
    assert len(mocked_llm) == 1


def test_non_python_falls_back_to_generic(isolated_home, mocked_llm, fixtures_dir):
    trace = (fixtures_dir / "node_traceback.txt").read_text()
    result = RUNNER.invoke(cli.app, [], input=trace)
    assert result.exit_code == 0, result.output
    assert len(mocked_llm) == 1
    system = mocked_llm[0]["system_prompt"]
    assert "No local source code" in system or "No local source" in system.replace("\n", " ")


def test_analyze_with_file_flag(isolated_home, mocked_llm, fixtures_dir, tmp_path):
    trace_file = tmp_path / "trace.txt"
    trace_file.write_text((fixtures_dir / "python_traceback.txt").read_text())
    result = RUNNER.invoke(cli.app, ["--file", str(trace_file)])
    assert result.exit_code == 0, result.output
    assert len(mocked_llm) == 1


def test_missing_credentials_shows_clear_error(tmp_path, monkeypatch, fixtures_dir):
    empty_dir = tmp_path / ".whybroke"
    monkeypatch.setattr(config, "CONFIG_DIR", empty_dir)
    monkeypatch.setattr(config, "CREDENTIALS_PATH", empty_dir / "credentials.json")
    trace = (fixtures_dir / "python_traceback.txt").read_text()
    result = RUNNER.invoke(cli.app, [], input=trace)
    assert result.exit_code == 1
    assert "whybroke auth" in result.output


def test_empty_input_errors_cleanly(isolated_home):
    result = RUNNER.invoke(cli.app, [], input="")
    assert result.exit_code == 1
    # CliRunner's input="" creates a non-tty stdin, so we hit the empty-input branch
    assert "Empty input" in result.output or "No input" in result.output


def test_malformed_llm_response_surfaces_error(isolated_home, monkeypatch, fixtures_dir):
    from whybroke.llm import LLMResponseError

    def boom(**kwargs):
        raise LLMResponseError("bad json", raw_response="not json {")

    monkeypatch.setattr(cli, "analyze", boom)
    trace = (fixtures_dir / "python_traceback.txt").read_text()
    result = RUNNER.invoke(cli.app, [], input=trace)
    assert result.exit_code == 1
    assert "malformed" in result.output.lower()


def test_session_roundtrip_via_view_command(isolated_home, mocked_llm, fixtures_dir):
    trace = (fixtures_dir / "python_traceback.txt").read_text()
    analyze_result = RUNNER.invoke(cli.app, [], input=trace)
    assert analyze_result.exit_code == 0

    # now view session 1 — must NOT call LLM
    view_result = RUNNER.invoke(cli.app, ["view", "1"])
    assert view_result.exit_code == 0
    assert "TypeError" in view_result.output
    # confirm mocked_llm was only called once (during analyze, not view)
    assert len(mocked_llm) == 1


def test_history_shows_saved_sessions(isolated_home, mocked_llm, fixtures_dir):
    trace = (fixtures_dir / "python_traceback.txt").read_text()
    RUNNER.invoke(cli.app, [], input=trace)
    RUNNER.invoke(cli.app, [], input=trace)

    hist = RUNNER.invoke(cli.app, ["history"])
    assert hist.exit_code == 0
    assert "TypeError" in hist.output


def test_view_missing_session_errors(isolated_home):
    result = RUNNER.invoke(cli.app, ["view", "999"])
    assert result.exit_code == 1
    assert "No session" in result.output
