from io import StringIO

import pytest
from rich.console import Console

from whybroke.teach import render_lesson, should_show_lesson


class TestShouldShowLesson:
    def test_respects_explicit_true_override(self):
        assert should_show_lesson(override=True) is True

    def test_respects_explicit_false_override(self):
        assert should_show_lesson(override=False) is False

    def test_defaults_to_false_when_not_tty(self, monkeypatch):
        import sys

        monkeypatch.setattr("sys.stdout.isatty", lambda: False)
        assert should_show_lesson(override=None) is False

    def test_defaults_to_true_when_tty(self, monkeypatch):
        import sys

        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert should_show_lesson(override=None) is True

    def test_override_takes_precedence_over_tty_check(self, monkeypatch):
        import sys

        monkeypatch.setattr("sys.stdout.isatty", lambda: True)
        assert should_show_lesson(override=False) is False

        monkeypatch.setattr("sys.stdout.isatty", lambda: False)
        assert should_show_lesson(override=True) is True


class TestRenderLesson:
    def _capture_render(self, lesson: dict) -> str:
        buf = StringIO()
        console = Console(file=buf, width=100, force_terminal=False, color_system=None)
        render_lesson(lesson, console)
        return buf.getvalue()

    def test_renders_complete_lesson(self):
        lesson = {
            "pattern_name": "Async/Await Confusion",
            "broken_snippet": "user = await get_user_sync(id)",
            "why_it_bites": "get_user_sync is not async",
            "fix_snippet": "user = get_user_sync(id)",
        }
        output = self._capture_render(lesson)
        assert "Async/Await Confusion" in output
        assert "Async/Await Confusion" in output
        assert "user = await get_user_sync(id)" in output
        assert "get_user_sync is not async" in output
        assert "user = get_user_sync(id)" in output

    def test_renders_lesson_without_why(self):
        lesson = {
            "pattern_name": "Missing Import",
            "broken_snippet": "x = json.loads(data)",
            "why_it_bites": "",
            "fix_snippet": "import json\nx = json.loads(data)",
        }
        output = self._capture_render(lesson)
        assert "Missing Import" in output
        assert "x = json.loads(data)" in output
        assert "import json" in output

    def test_ignores_none_lesson(self):
        output = self._capture_render(None)
        assert output == ""

    def test_ignores_empty_dict_lesson(self):
        output = self._capture_render({})
        assert output == ""

    def test_ignores_invalid_lesson_type(self):
        output = self._capture_render("not a dict")
        assert output == ""

    def test_ignores_lesson_with_missing_pattern_name(self):
        lesson = {
            "broken_snippet": "x = 1",
            "why_it_bites": "test",
            "fix_snippet": "x = 2",
        }
        output = self._capture_render(lesson)
        assert output == ""

    def test_ignores_lesson_with_missing_broken_snippet(self):
        lesson = {
            "pattern_name": "Test",
            "why_it_bites": "test",
            "fix_snippet": "x = 2",
        }
        output = self._capture_render(lesson)
        assert output == ""

    def test_ignores_lesson_with_missing_fix_snippet(self):
        lesson = {
            "pattern_name": "Test",
            "broken_snippet": "x = 1",
            "why_it_bites": "test",
        }
        output = self._capture_render(lesson)
        assert output == ""

    def test_handles_whitespace_only_fields(self):
        lesson = {
            "pattern_name": "   ",
            "broken_snippet": "x = 1",
            "why_it_bites": "test",
            "fix_snippet": "x = 2",
        }
        output = self._capture_render(lesson)
        assert output == ""

    def test_renders_with_empty_why_field(self):
        lesson = {
            "pattern_name": "Import Pattern",
            "broken_snippet": "json.loads(x)",
            "why_it_bites": "",
            "fix_snippet": "import json\njson.loads(x)",
        }
        output = self._capture_render(lesson)
        assert "Import Pattern" in output
        assert "json.loads(x)" in output

    def test_renders_syntax_highlighted_code(self):
        lesson = {
            "pattern_name": "Decorator Order",
            "broken_snippet": "@app.route('/')\n@cache.cached()\ndef view(): pass",
            "why_it_bites": "Cache will cache the decorator itself",
            "fix_snippet": "@cache.cached()\n@app.route('/')\ndef view(): pass",
        }
        output = self._capture_render(lesson)
        assert "Decorator Order" in output
        assert "def view()" in output

    def test_renders_multi_line_explanation(self):
        lesson = {
            "pattern_name": "Complex Explanation",
            "broken_snippet": "result = json.loads(data)",
            "why_it_bites": "This pattern is broken because:\n1. Missing import\n2. Error handling",
            "fix_snippet": "import json\nresult = json.loads(data)",
        }
        output = self._capture_render(lesson)
        assert "Complex Explanation" in output
        assert output != ""

    def test_console_is_used_for_output(self):
        lesson = {
            "pattern_name": "Test Pattern",
            "broken_snippet": "x = 1",
            "why_it_bites": "why",
            "fix_snippet": "x = 2",
        }
        buf = StringIO()
        console = Console(file=buf, width=80, force_terminal=False)
        render_lesson(lesson, console)
        output = buf.getvalue()
        assert len(output) > 0
        assert "Test Pattern" in output
