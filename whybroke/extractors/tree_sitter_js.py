from __future__ import annotations

from pathlib import Path

_FALLBACK_RADIUS = 10

_FUNCTION_NODE_TYPES = {
    "function_declaration",
    "function_expression",
    "arrow_function",
    "method_definition",
    "generator_function",
    "generator_function_declaration",
    "class_declaration",
}

_TS_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts"}
_TSX_EXTENSIONS = {".tsx", ".jsx"}


def _grammar_for(filepath: str) -> str:
    suffix = Path(filepath).suffix.lower()
    if suffix == ".tsx":
        return "tsx"
    if suffix in _TS_EXTENSIONS:
        return "typescript"
    return "javascript"


def get_failing_context(filepath: str, target_line: int) -> str:
    path = Path(filepath)
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""

    try:
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from tree_sitter_languages import get_parser  # type: ignore

            parser = get_parser(_grammar_for(filepath))
            tree = parser.parse(source.encode("utf-8"))
    except ImportError:
        return _line_window(source, target_line)
    except Exception:
        return _line_window(source, target_line)

    best = None
    best_span = None

    # Iterative DFS — avoids Python recursion-limit errors on large/deep files.
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        start_line = node.start_point[0] + 1  # tree-sitter is 0-indexed
        end_line = node.end_point[0] + 1
        if (
            node.type in _FUNCTION_NODE_TYPES
            and start_line <= target_line <= end_line
        ):
            span = end_line - start_line
            if best_span is None or span < best_span:
                best = node
                best_span = span
        stack.extend(node.children)

    if best is not None:
        try:
            return source.encode("utf-8")[best.start_byte : best.end_byte].decode(
                "utf-8", errors="replace"
            )
        except Exception:
            pass

    return _line_window(source, target_line)


def _line_window(source: str, target_line: int) -> str:
    lines = source.splitlines()
    if not lines:
        return ""
    start = max(0, target_line - 1 - _FALLBACK_RADIUS)
    end = min(len(lines), target_line + _FALLBACK_RADIUS)
    return "\n".join(lines[start:end])
