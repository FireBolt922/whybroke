from whybroke.extractors.python_ast import get_failing_context


def test_extracts_async_function_containing_line(fixtures_dir):
    path = fixtures_dir / "sample_buggy.py"
    # Line 11 is `user_data = await service.get_user_sync(user_id)` inside get_user
    result = get_failing_context(str(path), target_line=11)
    assert "async def get_user" in result
    assert "await service.get_user_sync(user_id)" in result
    # should NOT leak other top-level functions
    assert "def top_level_helper" not in result


def test_extracts_class_when_line_inside_method(fixtures_dir):
    path = fixtures_dir / "sample_buggy.py"
    # Line 5 is inside get_user_sync method of UserService class
    result = get_failing_context(str(path), target_line=5)
    # picks the innermost: the method itself
    assert "def get_user_sync" in result
    assert "return {" in result


def test_returns_empty_for_missing_file(tmp_path):
    result = get_failing_context(str(tmp_path / "nope.py"), target_line=1)
    assert result == ""


def test_falls_back_to_line_window_for_syntax_error(tmp_path):
    bad = tmp_path / "broken.py"
    bad.write_text(
        "\n".join([f"line_{i}" for i in range(1, 31)]), encoding="utf-8"
    )
    result = get_failing_context(str(bad), target_line=15)
    # window is ±10 around line 15 → lines 5..25
    assert "line_5" in result
    assert "line_25" in result
    assert "line_4" not in result
    assert "line_26" not in result


def test_falls_back_when_line_outside_any_function(fixtures_dir):
    path = fixtures_dir / "sample_buggy.py"
    # Line 1 is `import asyncio` — not inside any function
    result = get_failing_context(str(path), target_line=1)
    assert "import asyncio" in result
