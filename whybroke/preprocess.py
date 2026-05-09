import re

_TRACEBACK_START = re.compile(r"Traceback \(most recent call last\):")
_FRAME_HEADER = re.compile(r'^\s*File "[^"]+", line \d+, in \S+')

# JS/Node: the error class line (e.g. `TypeError: ...`) just before `at` frames.
_JS_ERROR_HEADER = re.compile(
    r"^[A-Z][A-Za-z0-9_]*(?:Error|Exception|Warning):", re.MULTILINE
)
_JS_FRAME_HEADER = re.compile(r"^\s*at\s+\S", re.MULTILINE)

MAX_CHARS = 10_000
_HEAD_KEEP = 2_000
_TAIL_KEEP = 3_000


def strip_noise(raw: str) -> str:
    if not raw:
        return ""
    sliced = _slice_from_traceback(raw)
    deduped = _dedup_consecutive_frames(sliced)
    return _truncate(deduped)


def _slice_from_traceback(raw: str) -> str:
    # Use the LAST Python traceback header — chained exceptions produce multiple
    # "Traceback (most recent call last):" blocks and the last one is actionable.
    last_py = None
    for m in _TRACEBACK_START.finditer(raw):
        last_py = m
    if last_py:
        return raw[last_py.start():]

    js_match = _JS_ERROR_HEADER.search(raw)
    if js_match:
        # Confirm `at` frames follow — otherwise the bare "Error:" might be log
        # noise rather than a real stack trace.
        if _JS_FRAME_HEADER.search(raw, js_match.end()):
            return raw[js_match.start():]
    return raw


def _dedup_consecutive_frames(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _FRAME_HEADER.match(line) and i + 1 < len(lines):
            pair = (line, lines[i + 1])
            repeats = 0
            j = i + 2
            while j + 1 < len(lines) and (lines[j], lines[j + 1]) == pair:
                repeats += 1
                j += 2
            out.append(line)
            out.append(lines[i + 1])
            if repeats:
                out.append(f"  [... previous frame repeated {repeats} times ...]")
            i = j
            continue
        if _JS_FRAME_HEADER.match(line):
            repeats = 0
            j = i + 1
            while j < len(lines) and lines[j] == line:
                repeats += 1
                j += 1
            out.append(line)
            if repeats:
                out.append(f"  [... previous frame repeated {repeats} times ...]")
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def _truncate(text: str) -> str:
    if len(text) <= MAX_CHARS:
        return text
    head = text[:_HEAD_KEEP]
    tail = text[-_TAIL_KEEP:]
    return f"{head}\n......\n{tail}"
