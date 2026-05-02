from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class EcosystemNote:
    label: str
    finding: str
    prompt_note: str


# (package, exc_keywords, version_fragments_for_old_pin, finding, prompt_note)
_LOCKFILE_TRAPS = [
    (
        "pydantic",
        ["pydantic"],
        ["<2", "^1.", "~=1.", "==1."],
        "pydantic is pinned to v1 — likely the pydantic v1→v2 breaking change "
        "(validator → field_validator, BaseSettings moved, etc.)",
        "Lockfile: pydantic is pinned to v1; this trace may involve the v1→v2 migration.",
    ),
    (
        "sqlalchemy",
        ["sqlalchemy"],
        ["<2", "^1.", "~=1.", "==1."],
        "SQLAlchemy is pinned to v1 — likely the 1.x→2.0 breaking change "
        "(ORM Query API replaced, execute() semantics changed)",
        "Lockfile: SQLAlchemy is pinned to v1; this trace may involve the 1.x→2.0 migration.",
    ),
    (
        "django",
        ["django"],
        ["<3", "<4", "^2.", "^3.", "~=2.", "~=3.", "==2.", "==3."],
        "Django is pinned to v2/v3 — APIs changed across v3→v4→v5 "
        "(on_delete, CONN_MAX_AGE, url() deprecated, etc.)",
        "Lockfile: Django is pinned to v2/v3; this trace may involve Django major-version breaking changes.",
    ),
    (
        "numpy",
        ["numpy"],
        ["<2", "^1.", "~=1.", "==1."],
        "NumPy is pinned to v1 — likely the v1→v2 breaking change "
        "(dtype aliases removed, copy= keyword changed)",
        "Lockfile: NumPy is pinned to v1; this trace may involve the NumPy v1→v2 migration.",
    ),
]


def _read_lockfile_text(cwd: Path) -> str:
    for name in ("pyproject.toml", "requirements.txt", "setup.cfg"):
        candidate = cwd / name
        if candidate.exists():
            try:
                return candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    return ""


def _package_pinned_to_old(lockfile: str, package: str, version_fragments: list[str]) -> bool:
    lower = lockfile.lower()
    idx = lower.find(package.lower())
    if idx < 0:
        return False
    # inspect the 100-char window after the package name for old-version constraints
    snippet = lower[idx : idx + 100]
    return any(frag in snippet for frag in version_fragments)


def _check_lockfile(trace: str, cwd: Path) -> list[EcosystemNote]:
    lockfile = _read_lockfile_text(cwd)
    if not lockfile:
        return []
    trace_lower = trace.lower()
    notes: list[EcosystemNote] = []
    for package, exc_keywords, version_fragments, finding, prompt_note in _LOCKFILE_TRAPS:
        if not any(kw in trace_lower for kw in exc_keywords):
            continue
        if _package_pinned_to_old(lockfile, package, version_fragments):
            notes.append(
                EcosystemNote(label="Lockfile mismatch", finding=finding, prompt_note=prompt_note)
            )
    return notes


def _check_git_hint(failing_file: str, cwd: Path) -> EcosystemNote | None:
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-3", "--", failing_file],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=3,
        )
        lines = result.stdout.strip().splitlines()
        if not lines:
            return None
        recent = lines[0]
        short_path = Path(failing_file).name
        return EcosystemNote(
            label="Recent git change",
            finding=f"'{short_path}' last changed: {recent}",
            prompt_note=(
                f"Git history: the failing file '{short_path}' was recently modified "
                f"(last commit: {recent}). Check that change first."
            ),
        )
    except Exception:
        return None


def detect_framework(cwd: Path | None = None) -> str | None:
    """Detect the web framework used in the project from lockfile + filesystem signals."""
    cwd = cwd or Path.cwd()
    try:
        lockfile = _read_lockfile_text(cwd)
        lower = lockfile.lower()
        if (cwd / "manage.py").exists() and "django" in lower:
            return "django"
        if "fastapi" in lower:
            return "fastapi"
        if "flask" in lower and "django" not in lower:
            return "flask"
    except Exception:
        pass
    return None


def run_checks(
    trace: str,
    failing_file: str | None = None,
    cwd: Path | None = None,
) -> list[EcosystemNote]:
    """Run all deterministic ecosystem checks and return findings."""
    cwd = cwd or Path.cwd()
    notes: list[EcosystemNote] = []
    notes.extend(_check_lockfile(trace, cwd))
    if failing_file:
        git_note = _check_git_hint(failing_file, cwd)
        if git_note:
            notes.append(git_note)
    return notes
