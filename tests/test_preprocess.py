from whybroke.preprocess import MAX_CHARS, strip_noise


def test_empty_input_returns_empty():
    assert strip_noise("") == ""


def test_drops_noise_before_traceback(python_trace):
    result = strip_noise(python_trace)
    assert result.startswith("Traceback (most recent call last):")
    assert "GET /users/1" not in result


def test_keeps_input_when_no_traceback():
    raw = "hello world\nno traceback here"
    assert strip_noise(raw) == raw


def test_dedups_consecutive_frames(recursion_trace):
    result = strip_noise(recursion_trace)
    assert "[... previous frame repeated" in result
    # original had 3 repeated deep() frames, so dedup summarizes 2 extras
    assert "repeated 2 times" in result


def test_dedup_does_not_touch_distinct_frames(python_trace):
    result = strip_noise(python_trace)
    assert "[... previous frame repeated" not in result


def test_truncates_oversized_input():
    big = "Traceback (most recent call last):\n" + ("x" * (MAX_CHARS + 5000))
    result = strip_noise(big)
    assert len(result) < MAX_CHARS + 200
    assert "......" in result


def test_short_input_not_truncated(python_trace):
    result = strip_noise(python_trace)
    assert "......" not in result
