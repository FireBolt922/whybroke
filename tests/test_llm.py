import json

import pytest

from whybroke import llm
from whybroke.llm import (
    LLMProviderError,
    LLMResponseError,
    REQUIRED_FIELDS,
    _parse_response,
    analyze,
)

VALID_PAYLOAD = {
    "exception_type": "TypeError",
    "confidence_score": 92,
    "root_cause": "await used on a synchronous function",
    "reasoning": "The trace shows await on get_user_sync which returns a dict.",
    "evidence_lines": ["user_data = await db.get_user_sync(user_id)"],
    "suggested_fix": "- await db.get_user_sync(user_id)\n+ db.get_user_sync(user_id)",
}


def test_parse_response_happy_path():
    result = _parse_response(json.dumps(VALID_PAYLOAD))
    assert result["exception_type"] == "TypeError"
    assert result["confidence_score"] == 92
    assert set(result.keys()) >= REQUIRED_FIELDS


def test_parse_response_strips_markdown_fence():
    fenced = "```json\n" + json.dumps(VALID_PAYLOAD) + "\n```"
    result = _parse_response(fenced)
    assert result["exception_type"] == "TypeError"


def test_parse_response_strips_plain_fence():
    fenced = "```\n" + json.dumps(VALID_PAYLOAD) + "\n```"
    result = _parse_response(fenced)
    assert result["exception_type"] == "TypeError"


def test_parse_response_raises_on_invalid_json():
    with pytest.raises(LLMResponseError) as exc_info:
        _parse_response("not json at all {")
    assert exc_info.value.raw_response == "not json at all {"


def test_parse_response_raises_on_non_object():
    with pytest.raises(LLMResponseError):
        _parse_response(json.dumps(["an", "array"]))


def test_parse_response_raises_on_missing_field():
    payload = dict(VALID_PAYLOAD)
    del payload["suggested_fix"]
    with pytest.raises(LLMResponseError) as exc_info:
        _parse_response(json.dumps(payload))
    assert "suggested_fix" in str(exc_info.value)


def test_parse_response_raises_on_out_of_range_confidence():
    payload = dict(VALID_PAYLOAD)
    payload["confidence_score"] = 150
    with pytest.raises(LLMResponseError):
        _parse_response(json.dumps(payload))


def test_parse_response_raises_on_non_integer_confidence():
    payload = dict(VALID_PAYLOAD)
    payload["confidence_score"] = "high"
    with pytest.raises(LLMResponseError):
        _parse_response(json.dumps(payload))


def test_parse_response_raises_when_evidence_not_list():
    payload = dict(VALID_PAYLOAD)
    payload["evidence_lines"] = "line one"
    with pytest.raises(LLMResponseError):
        _parse_response(json.dumps(payload))


def test_analyze_dispatches_to_openai(monkeypatch):
    called = {}

    def fake_openai(system, user, key, model):
        called["provider"] = "openai"
        called["model"] = model
        called["key"] = key
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_openai", fake_openai)
    result = analyze("sys", "user", provider="openai", api_key="sk-test")
    assert result["exception_type"] == "TypeError"
    assert called["provider"] == "openai"
    assert called["model"] == "gpt-4o-mini"
    assert called["key"] == "sk-test"


def test_analyze_dispatches_to_anthropic(monkeypatch):
    called = {}

    def fake_anthropic(system, user, key, model):
        called["provider"] = "anthropic"
        called["model"] = model
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_anthropic", fake_anthropic)
    result = analyze("sys", "user", provider="anthropic", api_key="sk-ant")
    assert result["exception_type"] == "TypeError"
    assert called["model"] == "claude-sonnet-4-5"


def test_analyze_respects_model_override(monkeypatch):
    seen = {}

    def fake_openai(system, user, key, model):
        seen["model"] = model
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_openai", fake_openai)
    analyze("sys", "user", provider="openai", api_key="sk-test", model="gpt-5")
    assert seen["model"] == "gpt-5"


def test_analyze_dispatches_to_gemini(monkeypatch):
    called = {}

    def fake_gemini(system, user, key, model):
        called["model"] = model
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_gemini", fake_gemini)
    result = analyze("sys", "user", provider="gemini", api_key="k")
    assert result["exception_type"] == "TypeError"
    assert called["model"] == "gemini-2.5-flash"


def test_analyze_dispatches_to_grok(monkeypatch):
    called = {}

    def fake_grok(system, user, key, model):
        called["model"] = model
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_grok", fake_grok)
    result = analyze("sys", "user", provider="grok", api_key="xai-test")
    assert result["exception_type"] == "TypeError"
    assert called["model"] == "grok-4-fast"


def test_analyze_dispatches_to_openrouter(monkeypatch):
    called = {}

    def fake_openrouter(system, user, key, model):
        called["model"] = model
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_openrouter", fake_openrouter)
    result = analyze("sys", "user", provider="openrouter", api_key="sk-or")
    assert result["exception_type"] == "TypeError"
    assert called["model"] == "openrouter/free"


def test_openrouter_falls_back_on_rate_limit(monkeypatch):
    from openai import OpenAI  # noqa: F401 — ensure import path exists

    attempts: list[str] = []

    class FakeRateLimit(Exception):
        pass

    FakeRateLimit.__name__ = "RateLimitError"

    class FakeChoice:
        def __init__(self, content: str):
            self.message = type("M", (), {"content": content})()

    class FakeResp:
        def __init__(self, content: str):
            self.choices = [FakeChoice(content)]

    class FakeCompletions:
        def create(self, **kwargs):
            model = kwargs["model"]
            attempts.append(model)
            if model == "openrouter/free":
                raise FakeRateLimit("429 too many requests")
            return FakeResp(json.dumps(VALID_PAYLOAD))

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = FakeChat()

    monkeypatch.setattr(llm, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeClient)

    raw = llm._call_openrouter("sys", "user", "sk-or", "openrouter/free")
    assert json.loads(raw)["exception_type"] == "TypeError"
    assert attempts[0] == "openrouter/free"
    assert len(attempts) >= 2  # primary failed, fallback succeeded


def test_openrouter_folds_system_prompt_for_gemma(monkeypatch):
    captured = {}

    class FakeChoice:
        def __init__(self, content: str):
            self.message = type("M", (), {"content": content})()

    class FakeResp:
        def __init__(self, content: str):
            self.choices = [FakeChoice(content)]

    class FakeCompletions:
        def create(self, **kwargs):
            captured["model"] = kwargs["model"]
            captured["messages"] = kwargs["messages"]
            captured["has_response_format"] = "response_format" in kwargs
            return FakeResp(json.dumps(VALID_PAYLOAD))

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("C", (), {"completions": FakeCompletions()})()

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeClient)

    llm._call_openrouter(
        "SYS_TEXT", "USER_TEXT", "sk-or", "google/gemma-4-31b-it:free"
    )
    assert captured["model"] == "google/gemma-4-31b-it:free"
    assert len(captured["messages"]) == 1
    assert captured["messages"][0]["role"] == "user"
    assert "SYS_TEXT" in captured["messages"][0]["content"]
    assert "USER_TEXT" in captured["messages"][0]["content"]
    assert captured["has_response_format"] is False


def test_openrouter_falls_back_on_malformed_json(monkeypatch):
    attempts: list[str] = []

    class FakeChoice:
        def __init__(self, content: str):
            self.message = type("M", (), {"content": content})()

    class FakeResp:
        def __init__(self, content: str):
            self.choices = [FakeChoice(content)]

    class FakeCompletions:
        def create(self, **kwargs):
            model = kwargs["model"]
            attempts.append(model)
            if model == "openrouter/free":
                return FakeResp('{"exception_type": "KeyError", "root_cause": "x has "quotes" unescaped"}')
            return FakeResp(json.dumps(VALID_PAYLOAD))

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("C", (), {"completions": FakeCompletions()})()

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeClient)

    raw = llm._call_openrouter("sys", "user", "sk-or", "openrouter/free")
    assert json.loads(raw)["exception_type"] == "TypeError"
    assert attempts[0] == "openrouter/free"
    assert len(attempts) >= 2


def test_openrouter_retryable_matches_no_endpoints_found():
    exc = Exception(
        "Error code: 404 - {'error': {'message': 'No endpoints found for qwen/qwen-2.5-72b-instruct:free.', 'code': 404}}"
    )
    assert llm._is_retryable_openrouter_error(exc) is True


def test_openrouter_retryable_matches_developer_instruction_error():
    exc = Exception(
        "Error code: 400 - Provider returned error: Developer instruction is not enabled for models/gemma-3-27b-it"
    )
    assert llm._is_retryable_openrouter_error(exc) is True


def test_openrouter_raises_non_retryable_immediately(monkeypatch):
    class FakeAuthError(Exception):
        pass

    FakeAuthError.__name__ = "AuthenticationError"

    attempts: list[str] = []

    class FakeCompletions:
        def create(self, **kwargs):
            attempts.append(kwargs["model"])
            raise FakeAuthError("invalid api key")

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("C", (), {"completions": FakeCompletions()})()

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeClient)

    with pytest.raises(FakeAuthError):
        llm._call_openrouter("sys", "user", "bad-key", "any-model")
    assert len(attempts) == 1  # did not fall back


def test_analyze_dispatches_to_zai(monkeypatch):
    called = {}

    def fake_zai(system, user, key, model):
        called["model"] = model
        called["key"] = key
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_zai", fake_zai)
    result = analyze("sys", "user", provider="zai", api_key="zai-test")
    assert result["exception_type"] == "TypeError"
    assert called["model"] == "glm-4.7-flash"
    assert called["key"] == "zai-test"


def test_analyze_dispatches_to_nvidia(monkeypatch):
    called = {}

    def fake_nvidia(system, user, key, model):
        called["model"] = model
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_nvidia", fake_nvidia)
    result = analyze("sys", "user", provider="nvidia", api_key="nvapi-test")
    assert result["exception_type"] == "TypeError"
    assert called["model"] == "z-ai/glm4.7"


def test_zai_handler_uses_correct_base_url(monkeypatch):
    captured = {}

    class FakeChoice:
        def __init__(self, content: str):
            self.message = type("M", (), {"content": content})()

    class FakeResp:
        def __init__(self, content: str):
            self.choices = [FakeChoice(content)]

    class FakeCompletions:
        def create(self, **kwargs):
            captured["model"] = kwargs["model"]
            return FakeResp(json.dumps(VALID_PAYLOAD))

    class FakeClient:
        def __init__(self, **kwargs):
            captured["base_url"] = kwargs.get("base_url")
            captured["api_key"] = kwargs.get("api_key")
            self.chat = type("C", (), {"completions": FakeCompletions()})()

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    llm._call_zai("sys", "user", "zai-key", "glm-4.7-flash")
    assert captured["base_url"] == llm.ZAI_BASE_URL
    assert captured["api_key"] == "zai-key"
    assert captured["model"] == "glm-4.7-flash"


def test_nvidia_handler_uses_correct_base_url(monkeypatch):
    captured = {}

    class FakeChoice:
        def __init__(self, content: str):
            self.message = type("M", (), {"content": content})()

    class FakeResp:
        def __init__(self, content: str):
            self.choices = [FakeChoice(content)]

    class FakeCompletions:
        def create(self, **kwargs):
            captured["model"] = kwargs["model"]
            return FakeResp(json.dumps(VALID_PAYLOAD))

    class FakeClient:
        def __init__(self, **kwargs):
            captured["base_url"] = kwargs.get("base_url")
            self.chat = type("C", (), {"completions": FakeCompletions()})()

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    llm._call_nvidia("sys", "user", "nvapi-key", "z-ai/glm4.7")
    assert captured["base_url"] == llm.NVIDIA_BASE_URL
    assert captured["model"] == "z-ai/glm4.7"


def test_openai_compatible_retries_without_response_format(monkeypatch):
    """If a model rejects response_format=json_object, retry without it."""
    attempts: list[dict] = []

    class FakeChoice:
        def __init__(self, content: str):
            self.message = type("M", (), {"content": content})()

    class FakeResp:
        def __init__(self, content: str):
            self.choices = [FakeChoice(content)]

    class FakeCompletions:
        def create(self, **kwargs):
            attempts.append(kwargs)
            if "response_format" in kwargs:
                raise Exception("400 - response_format is not supported")
            return FakeResp(json.dumps(VALID_PAYLOAD))

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = type("C", (), {"completions": FakeCompletions()})()

    import openai

    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    raw = llm._call_zai("sys", "user", "k", "glm-4.7-flash")
    assert json.loads(raw)["exception_type"] == "TypeError"
    assert len(attempts) == 2
    assert "response_format" in attempts[0]
    assert "response_format" not in attempts[1]


def test_analyze_dispatches_to_litellm_with_explicit_model(monkeypatch):
    called = {}

    def fake_litellm(system, user, key, model):
        called["model"] = model
        return json.dumps(VALID_PAYLOAD)

    monkeypatch.setattr(llm, "_call_litellm", fake_litellm)
    result = analyze(
        "sys", "user", provider="litellm", api_key="k", model="ollama/llama3"
    )
    assert result["exception_type"] == "TypeError"
    assert called["model"] == "ollama/llama3"


def test_analyze_litellm_requires_explicit_model():
    with pytest.raises(LLMProviderError) as exc_info:
        analyze("sys", "user", provider="litellm", api_key="k")
    assert "explicit model" in str(exc_info.value).lower()


def test_analyze_rejects_unknown_provider():
    with pytest.raises(LLMProviderError):
        analyze("sys", "user", provider="cohere", api_key="x")


def test_analyze_propagates_response_error(monkeypatch):
    monkeypatch.setattr(llm, "_call_openai", lambda *a, **k: "not json")
    with pytest.raises(LLMResponseError):
        analyze("sys", "user", provider="openai", api_key="sk-test")
