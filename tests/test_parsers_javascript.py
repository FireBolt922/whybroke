from whybroke.parsers import Frame
from whybroke.parsers.javascript import (
    extract_exception_type,
    parse_js_trace,
    pick_user_frame,
)


def test_parses_v8_frames(node_trace):
    frames = parse_js_trace(node_trace)
    assert len(frames) >= 1
    first = frames[0]
    assert first == Frame(
        filepath="/Users/dev/app/server.js", lineno=42, func_name="getUser"
    )


def test_extracts_exception_type(node_trace):
    assert extract_exception_type(node_trace) == "TypeError"


def test_picks_user_frame_skipping_node_modules(node_trace):
    frames = parse_js_trace(node_trace)
    target = pick_user_frame(frames)
    assert target is not None
    assert "node_modules" not in target.filepath
    assert target.func_name == "getUser"


def test_parses_typescript_trace(ts_trace):
    frames = parse_js_trace(ts_trace)
    assert len(frames) >= 1
    user = pick_user_frame(frames)
    assert user is not None
    assert user.filepath.endswith(".ts")
    assert user.lineno == 11


def test_handles_anonymous_top_level_frame(async_rejection_trace):
    frames = parse_js_trace(async_rejection_trace)
    assert any(f.filepath.endswith("worker.js") for f in frames)


def test_returns_empty_for_empty_input():
    assert parse_js_trace("") == []


def test_returns_empty_when_no_v8_frames():
    assert parse_js_trace("just some text, no JS trace here") == []


def test_pick_user_frame_returns_none_for_empty_list():
    assert pick_user_frame([]) is None


def test_pick_user_frame_returns_none_when_all_frames_are_noise():
    frames = [
        Frame(filepath="/app/node_modules/react/index.js", lineno=1, func_name="render"),
        Frame(filepath="/app/node_modules/express/lib/router.js", lineno=5, func_name="handle"),
    ]
    assert pick_user_frame(frames) is None


def test_parses_async_frame():
    trace = (
        "TypeError: Cannot read property 'x' of undefined\n"
        "    at async getUser (/app/server.js:10:5)\n"
        "    at async Module.load (node:internal/modules/cjs/loader:123:1)\n"
    )
    frames = parse_js_trace(trace)
    assert any(f.filepath == "/app/server.js" for f in frames)
    user = pick_user_frame(frames)
    assert user is not None
    assert user.filepath == "/app/server.js"
    assert "async getUser" in user.func_name or user.func_name == "async getUser"


def test_extract_exception_type_returns_first_match():
    trace = (
        "TypeError: outer error\n"
        "    at foo (/app/a.js:1:1)\n"
        "Caused by: RangeError: inner error\n"
        "    at bar (/app/b.js:2:1)\n"
    )
    assert extract_exception_type(trace) == "TypeError"
