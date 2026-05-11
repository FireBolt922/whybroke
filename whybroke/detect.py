import re

# Order matters: Python's "Traceback" header is unambiguous, so it is checked
# first. JS is detected by V8 frame syntax (`    at name (file:line:col)`).
_SIGNATURES: list[tuple[str, re.Pattern[str]]] = [
    ("python", re.compile(r"Traceback \(most recent call last\):")),
    (
        "javascript",
        re.compile(r"(?:^|\n)\s*at\s+(?:[^\s(]+\s+\()?[^\s()]+:\d+:\d+\)?"),
    ),
]


def detect_language(trace: str) -> str | None:
    if not trace:
        return None
    for language, pattern in _SIGNATURES:
        if pattern.search(trace):
            return language
    return None
