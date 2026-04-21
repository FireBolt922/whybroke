from dataclasses import dataclass


@dataclass(frozen=True)
class Frame:
    filepath: str
    lineno: int
    func_name: str
