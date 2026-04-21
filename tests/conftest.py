from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def python_trace() -> str:
    return (FIXTURES / "python_traceback.txt").read_text(encoding="utf-8")


@pytest.fixture
def node_trace() -> str:
    return (FIXTURES / "node_traceback.txt").read_text(encoding="utf-8")


@pytest.fixture
def recursion_trace() -> str:
    return (FIXTURES / "recursion_loop.txt").read_text(encoding="utf-8")
