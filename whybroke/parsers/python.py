import re

from whybroke.parsers import Frame

_FRAME_RE = re.compile(
    r'^\s*File "(?P<filepath>[^"]+)", line (?P<lineno>\d+), in (?P<func_name>\S+)',
    re.MULTILINE,
)

_EXCEPTION_RE = re.compile(
    r"^(?P<exc_type>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Warning|Interrupt|Exit|Stop[A-Za-z]*))(?::\s*(?P<message>.*))?$",
    re.MULTILINE,
)


def parse_python_trace(trace: str) -> list[Frame]:
    frames: list[Frame] = []
    for match in _FRAME_RE.finditer(trace):
        frames.append(
            Frame(
                filepath=match.group("filepath"),
                lineno=int(match.group("lineno")),
                func_name=match.group("func_name"),
            )
        )
    return frames


def extract_exception_type(trace: str) -> str | None:
    last = None
    for match in _EXCEPTION_RE.finditer(trace):
        last = match.group("exc_type")
    return last
