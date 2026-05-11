import pytest

pytest.importorskip("tree_sitter_languages")

from whybroke.extractors.tree_sitter_js import get_failing_context


def test_extracts_async_function_containing_line(fixtures_dir):
    path = fixtures_dir / "sample_buggy.js"
    # Line 9 is `const userData = await service.getUserSync(userId);` inside getUser
    result = get_failing_context(str(path), target_line=9)
    assert "async function getUser" in result
    assert "await service.getUserSync(userId)" in result
    # should NOT leak other top-level functions
    assert "function topLevelHelper" not in result


def test_extracts_method_when_line_inside_class_method(fixtures_dir):
    path = fixtures_dir / "sample_buggy.js"
    # Line 3 is `return { id: userId, name: "Ada" };` inside getUserSync
    result = get_failing_context(str(path), target_line=3)
    assert "getUserSync" in result
    assert "return {" in result


def test_typescript_extraction(fixtures_dir):
    path = fixtures_dir / "sample_buggy.ts"
    # Line 11 is the await line inside getUser
    result = get_failing_context(str(path), target_line=11)
    assert "async function getUser" in result
    assert "await service.getUserSync(userId)" in result


def test_returns_empty_for_missing_file(tmp_path):
    result = get_failing_context(str(tmp_path / "nope.js"), target_line=1)
    assert result == ""


def test_falls_back_to_line_window_when_line_outside_any_function(fixtures_dir):
    path = fixtures_dir / "sample_buggy.js"
    # Line 1 is `class UserService {` — surrounding window
    result = get_failing_context(str(path), target_line=1)
    assert "UserService" in result
