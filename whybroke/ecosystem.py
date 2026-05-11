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
    # --- JavaScript / TypeScript ecosystem ---
    (
        "react",
        ["react"],
        ["^16.", "^17.", "~16.", "~17.", "16.", "17."],
        "react is pinned to v16/v17 — APIs changed in v18 "
        "(createRoot replaces ReactDOM.render, automatic batching, Suspense changes)",
        "Lockfile: react is pinned to v16/v17; this trace may involve the React v18 migration.",
    ),
    (
        "next",
        ["next"],
        ["^11.", "^12.", "~11.", "~12.", "11.", "12."],
        "next is pinned to v11/v12 — App Router & many APIs changed in v13/v14",
        "Lockfile: next is pinned to v11/v12; this trace may involve Next.js App Router migration.",
    ),
    (
        "express",
        ["express"],
        ["^3.", "~3.", "3."],
        "express is pinned to v3 — middleware/routing API changed in v4",
        "Lockfile: express is pinned to v3; this trace may involve the v3→v4 migration.",
    ),
    (
        "typescript",
        ["typescript", "ts2", "tserror"],
        ["^3.", "^4.", "~3.", "~4.", "==3.", "==4."],
        "typescript is pinned to v3/v4 — many strictness flags changed in v5",
        "Lockfile: typescript is pinned to v3/v4; this trace may involve TS v5 strictness changes.",
    ),
]


def _read_lockfile_text(cwd: Path) -> str:
    for name in (
        "pyproject.toml",
        "requirements.txt",
        "setup.cfg",
        "package.json",
        "package-lock.json",
        "yarn.lock",
    ):
        candidate = cwd / name
        if candidate.exists():
            try:
                return candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    return ""


def _package_pinned_to_old(lockfile: str, package: str, version_fragments: list[str]) -> bool:
    lower = lockfile.lower()
    pkg_lower = package.lower()
    # Search every occurrence of the package name (handles nested lockfile entries)
    # and check the surrounding 400-char window to cover multi-line JSON/YAML formats.
    start = 0
    while True:
        idx = lower.find(pkg_lower, start)
        if idx < 0:
            break
        snippet = lower[idx : idx + 400]
        if any(frag in snippet for frag in version_fragments):
            return True
        start = idx + len(pkg_lower)
    return False


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
        if (cwd / "next.config.js").exists() or (cwd / "next.config.mjs").exists() or '"next"' in lower:
            return "next"
        if '"@nestjs/core"' in lower or '"nest"' in lower:
            return "nest"
        if '"express"' in lower:
            return "express"
        if (cwd / "vite.config.js").exists() or (cwd / "vite.config.ts").exists() or '"vite"' in lower:
            return "vite"
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
