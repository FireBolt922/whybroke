import re

_SIGNATURES = {
    "python": re.compile(r"Traceback \(most recent call last\):"),
}


def detect_language(trace: str) -> str | None:
    if not trace:
        return None
    for language, pattern in _SIGNATURES.items():
        if pattern.search(trace):
            return language
    return None
