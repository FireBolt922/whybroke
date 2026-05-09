from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from whybroke.ecosystem import (
    EcosystemNote,
    _check_git_hint,
    _check_lockfile,
    _package_pinned_to_old,
    _read_lockfile_text,
    detect_framework,
    run_checks,
)


class TestReadLockfileText:
    def test_reads_pyproject_toml(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "pyproject.toml").write_text("[project]\nname = 'test'")
            result = _read_lockfile_text(tmppath)
            assert "name = 'test'" in result

    def test_reads_requirements_txt(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "requirements.txt").write_text("django>=3.0\nrequests")
            result = _read_lockfile_text(tmppath)
            assert "django" in result

    def test_reads_setup_cfg(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "setup.cfg").write_text("[metadata]\nname=test")
            result = _read_lockfile_text(tmppath)
            assert "name=test" in result

    def test_prefers_pyproject_toml_over_others(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "pyproject.toml").write_text("from_pyproject")
            (tmppath / "requirements.txt").write_text("from_requirements")
            result = _read_lockfile_text(tmppath)
            assert "from_pyproject" in result

    def test_returns_empty_string_when_no_lockfile(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            result = _read_lockfile_text(tmppath)
            assert result == ""

    def test_handles_read_errors_gracefully(self, tmp_path):
        # Create a file but make it unreadable
        lockfile = tmp_path / "pyproject.toml"
        lockfile.write_text("test")
        lockfile.chmod(0o000)
        try:
            result = _read_lockfile_text(tmp_path)
            # Should try next file
            assert result == ""
        finally:
            lockfile.chmod(0o644)


class TestPackagePinnedToOld:
    def test_detects_pydantic_v1(self):
        lockfile = "pydantic>=1.0,<2\nother-dep"
        assert _package_pinned_to_old(lockfile, "pydantic", ["<2", "==1."])

    def test_detects_django_v2(self):
        lockfile = "django==2.2\nother"
        assert _package_pinned_to_old(lockfile, "django", ["==2.", "==3."])

    def test_detects_sqlalchemy_v1(self):
        lockfile = "sqlalchemy~=1.4\nother"
        assert _package_pinned_to_old(lockfile, "sqlalchemy", ["~=1.", "<2"])

    def test_returns_false_when_package_not_in_lockfile(self):
        lockfile = "requests>=2.0\nnumpy"
        assert not _package_pinned_to_old(lockfile, "pydantic", ["<2"])

    def test_returns_false_when_package_has_new_version(self):
        lockfile = "pydantic>=2.0\nother"
        assert not _package_pinned_to_old(lockfile, "pydantic", ["<2", "==1."])

    def test_case_insensitive_matching(self):
        lockfile = "PYDANTIC==1.10\nother"
        assert _package_pinned_to_old(lockfile, "pydantic", ["==1."])


class TestCheckLockfile:
    def test_detects_pydantic_mismatch(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "requirements.txt").write_text("pydantic==1.10")
            trace = "from pydantic import BaseSettings"
            notes = _check_lockfile(trace, tmppath)
            result = [n for n in notes if "pydantic" in n.prompt_note.lower()]
            assert len(result) > 0
            assert "v1" in result[0].finding.lower()

    def test_detects_django_mismatch(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "requirements.txt").write_text("django==2.2")
            trace = "django.db.models.QuerySet AttributeError: 'QuerySet' has no 'query'"
            notes = _check_lockfile(trace, tmppath)
            result = [n for n in notes if "django" in n.prompt_note.lower()]
            assert len(result) > 0

    def test_ignores_unrelated_trace(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "requirements.txt").write_text("django==2.2\npydantic==2.0")
            trace = "KeyError: 'missing_key'"
            notes = _check_lockfile(trace, tmppath)
            assert len(notes) == 0

    def test_returns_empty_when_no_lockfile(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            trace = "from pydantic import BaseSettings"
            notes = _check_lockfile(trace, tmppath)
            assert notes == []

    def test_multiple_mismatches(self):
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "requirements.txt").write_text("pydantic==1.10\nsqlalchemy==1.4")
            trace = "pydantic error and sqlalchemy error"
            notes = _check_lockfile(trace, tmppath)
            assert len(notes) >= 2


class TestCheckGitHint:
    def test_returns_none_when_git_not_available(self, tmp_path):
        # Non-git directory
        result = _check_git_hint("nonexistent.py", tmp_path)
        assert result is None

    def test_returns_none_when_file_not_in_history(self, tmp_path):
        import subprocess

        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path)
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path))

        result = _check_git_hint("no_such_file.py", tmp_path)
        assert result is None

    def test_returns_git_hint_for_recent_file(self, tmp_path):
        import subprocess

        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path)
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path))

        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")
        subprocess.run(["git", "add", "test.py"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=str(tmp_path), capture_output=True
        )

        result = _check_git_hint("test.py", tmp_path)
        assert result is not None
        assert isinstance(result, EcosystemNote)
        assert result.label == "Recent git change"
        assert "test.py" in result.finding


class TestDetectFramework:
    def test_detects_django(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("django>=3.0")
        (tmp_path / "manage.py").write_text("")
        result = detect_framework(tmp_path)
        assert result == "django"

    def test_detects_fastapi(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("fastapi>=0.95")
        result = detect_framework(tmp_path)
        assert result == "fastapi"

    def test_detects_flask(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("flask>=2.0")
        result = detect_framework(tmp_path)
        assert result == "flask"

    def test_prefers_django_over_flask(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("django>=3.0\nflask>=2.0")
        (tmp_path / "manage.py").write_text("")
        result = detect_framework(tmp_path)
        assert result == "django"

    def test_returns_none_when_no_framework_detected(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("requests>=2.0")
        result = detect_framework(tmp_path)
        assert result is None

    def test_returns_none_when_no_lockfile(self, tmp_path):
        result = detect_framework(tmp_path)
        assert result is None

    def test_detects_next(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"next": "^14.0.0", "react": "^18.0.0"}}'
        )
        result = detect_framework(tmp_path)
        assert result == "next"

    def test_detects_express(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"express": "^4.18.0"}}'
        )
        result = detect_framework(tmp_path)
        assert result == "express"

    def test_detects_nest(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"@nestjs/core": "^10.0.0"}}'
        )
        result = detect_framework(tmp_path)
        assert result == "nest"


class TestJsLockfileTraps:
    def test_detects_react_v17(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^17.0.2"}}'
        )
        trace = "TypeError: ReactDOM.render is not a function in react"
        notes = _check_lockfile(trace, tmp_path)
        assert any("react" in n.prompt_note.lower() for n in notes)

    def test_detects_express_v3(self, tmp_path):
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"express": "^3.21.0"}}'
        )
        trace = "TypeError: express.something is not a function"
        notes = _check_lockfile(trace, tmp_path)
        assert any("express" in n.prompt_note.lower() for n in notes)


class TestRunChecks:
    def test_runs_lockfile_checks(self):
        trace = "from pydantic import BaseSettings"
        lockfile = "pydantic==1.10"
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            (tmppath / "requirements.txt").write_text(lockfile)
            notes = run_checks(trace, cwd=tmppath)
            assert len(notes) > 0

    def test_runs_git_checks_when_file_provided(self, tmp_path):
        import subprocess

        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=str(tmp_path)
        )
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(tmp_path))

        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")
        subprocess.run(["git", "add", "test.py"], cwd=str(tmp_path), capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"], cwd=str(tmp_path), capture_output=True
        )

        notes = run_checks("some error", failing_file="test.py", cwd=tmp_path)
        git_notes = [n for n in notes if "git" in n.label.lower()]
        assert len(git_notes) > 0

    def test_returns_empty_when_no_issues(self):
        trace = "Some random error"
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            notes = run_checks(trace, cwd=tmppath)
            assert notes == []

    def test_ecosystem_note_dataclass(self):
        note = EcosystemNote(
            label="Test",
            finding="test finding",
            prompt_note="test note",
        )
        assert note.label == "Test"
        assert note.finding == "test finding"
        assert note.prompt_note == "test note"
