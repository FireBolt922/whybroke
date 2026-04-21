from whybroke.prompts import load_prompt


def test_loads_python_prompt():
    text = load_prompt("python")
    assert "Python debugging agent" in text
    assert "JSON" in text
    assert "confidence_score" in text


def test_loads_generic_prompt():
    text = load_prompt("generic")
    assert "No local source code" in text or "No local source" in text.replace("\n", " ")
    assert "confidence_score" in text


def test_unknown_language_falls_back_to_generic():
    text = load_prompt("rust")
    generic = load_prompt("generic")
    assert text == generic


def test_none_language_falls_back_to_generic():
    text = load_prompt(None)
    generic = load_prompt("generic")
    assert text == generic


def test_prompts_enforce_json_only_output():
    for name in ("python", "generic"):
        text = load_prompt(name)
        assert "JSON" in text
        assert "markdown" in text.lower()
