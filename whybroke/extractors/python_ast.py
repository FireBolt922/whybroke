import ast
from pathlib import Path

_FALLBACK_RADIUS = 10


def get_failing_context(filepath: str, target_line: int) -> str:
    path = Path(filepath)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _line_window(source, target_line)

    best: ast.AST | None = None
    best_span = None
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", None)
        if start is None or end is None:
            continue
        if start <= target_line <= end:
            span = end - start
            if best_span is None or span < best_span:
                best = node
                best_span = span

    if best is not None:
        segment = ast.get_source_segment(source, best)
        if segment:
            return segment

    return _line_window(source, target_line)


def _line_window(source: str, target_line: int) -> str:
    lines = source.splitlines()
    if not lines:
        return ""
    start = max(0, target_line - 1 - _FALLBACK_RADIUS)
    end = min(len(lines), target_line + _FALLBACK_RADIUS)
    return "\n".join(lines[start:end])
