from whybroke.parsers import Frame
from whybroke.parsers.python import extract_exception_type, parse_python_trace


def test_parses_frames_from_fastapi_trace(python_trace):
    frames = parse_python_trace(python_trace)
    assert len(frames) == 2
    assert frames[0] == Frame(
        filepath="/Users/dev/app/main.py", lineno=18, func_name="__call__"
    )
    assert frames[-1] == Frame(
        filepath="/Users/dev/app/src/routes/users.py",
        lineno=52,
        func_name="get_user",
    )


def test_last_frame_is_the_failing_one(python_trace):
    frames = parse_python_trace(python_trace)
    last = frames[-1]
    assert last.func_name == "get_user"
    assert last.lineno == 52


def test_handles_recursion_trace(recursion_trace):
    frames = parse_python_trace(recursion_trace)
    assert len(frames) >= 2
    assert frames[0].func_name == "<module>"
    assert all(f.filepath == "/app/recurse.py" for f in frames)


def test_returns_empty_list_for_empty_input():
    assert parse_python_trace("") == []


def test_returns_empty_list_when_no_frames():
    assert parse_python_trace("just some text, no python trace here") == []


def test_extracts_exception_type(python_trace):
    assert extract_exception_type(python_trace) == "TypeError"


def test_extracts_recursion_error(recursion_trace):
    assert extract_exception_type(recursion_trace) == "RecursionError"


def test_frame_is_frozen():
    f = Frame(filepath="a.py", lineno=1, func_name="foo")
    try:
        f.lineno = 2  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("Frame should be frozen")
