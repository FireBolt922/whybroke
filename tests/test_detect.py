from whybroke.detect import detect_language


def test_detects_python_traceback(python_trace):
    assert detect_language(python_trace) == "python"


def test_returns_none_for_node_trace(node_trace):
    assert detect_language(node_trace) is None


def test_returns_none_for_empty_string():
    assert detect_language("") is None


def test_returns_none_for_plain_text():
    assert detect_language("hello world, nothing broke here") is None


def test_detects_python_embedded_in_noise():
    trace = (
        "INFO: starting server\n"
        "WARNING: deprecated call\n"
        "Traceback (most recent call last):\n"
        '  File "app.py", line 1, in <module>\n'
        "ValueError: boom\n"
    )
    assert detect_language(trace) == "python"


def test_detects_python_from_recursion_trace(recursion_trace):
    assert detect_language(recursion_trace) == "python"
