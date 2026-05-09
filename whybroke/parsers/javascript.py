import re

from whybroke.parsers import Frame

# V8 stack frame shapes we recognise:
#     at funcName (/abs/path/file.js:42:9)
#     at /abs/path/file.js:42:9              # anonymous / top-level
#     at Object.<anonymous> (/abs/file.js:1:1)
#     at async funcName (/p/f.ts:10:3)       # async keyword prefix
#     at new ClassName (/p/f.js:5:1)
# func_name uses [^(]*? (allows internal spaces) so "async funcName" is captured whole.
_FRAME_RE = re.compile(
    r"^\s*at\s+"
    r"(?:(?P<func_name>[^\s(][^(]*?)\s+\()?"
    r"(?P<filepath>[^\s():][^\s():]*?):(?P<lineno>\d+):(?P<col>\d+)"
    r"\)?\s*$",
    re.MULTILINE,
)

# The error class line typically appears just before the `at` frames.
_EXCEPTION_RE = re.compile(
    r"^(?P<exc_type>[A-Z][A-Za-z0-9_]*(?:Error|Exception|Warning))\b",
    re.MULTILINE,
)

# Frames inside Node internals or third-party packages aren't useful for AST
# extraction — skip them when picking the failing user frame.
_NOISE_PATH_HINTS = (
    "node_modules/",
    "node:internal/",
    "internal/process/",
    "internal/modules/",
)


def parse_js_trace(trace: str) -> list[Frame]:
    frames: list[Frame] = []
    for match in _FRAME_RE.finditer(trace):
        filepath = match.group("filepath")
        if not filepath or filepath.startswith("("):
            continue
        func_name = match.group("func_name") or "<anonymous>"
        frames.append(
            Frame(
                filepath=filepath,
                lineno=int(match.group("lineno")),
                func_name=func_name,
            )
        )
    return frames


def pick_user_frame(frames: list[Frame]) -> Frame | None:
    """Return the first frame that isn't in node_modules / node internals.

    Returns None (not a noise frame) when every frame is third-party, so callers
    skip AST extraction rather than opening unrelated node_modules source.
    """
    for frame in frames:
        if not any(hint in frame.filepath for hint in _NOISE_PATH_HINTS):
            return frame
    return None


def extract_exception_type(trace: str) -> str | None:
    m = _EXCEPTION_RE.search(trace)
    return m.group("exc_type") if m else None
