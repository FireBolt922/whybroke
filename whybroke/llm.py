import json

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-5",
    "gemini": "gemini-2.5-flash",
    "grok": "grok-4-fast",
    "openrouter": "openrouter/free",
    "litellm": None,
    "zai": "glm-4.7-flash",
    "nvidia": "z-ai/glm4.7",
}

GROK_BASE_URL = "https://api.x.ai/v1"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
ZAI_BASE_URL = "https://api.z.ai/api/paas/v4/"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Ordered fallback list of free OpenRouter models. First entry is the meta-router
# which picks any live free model for us; the rest are explicit fallbacks that we
# verified live as of 2026-04. If a specific ID 404s, we fall through to the next.
OPENROUTER_FREE_FALLBACKS = (
    "openrouter/free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
)

# Some models (notably Gemma via Google AI Studio) don't accept a "system" role.
# For these, we fold the system prompt into the user message.
OPENROUTER_NO_SYSTEM_PROMPT = {
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
}

# Some free models don't support response_format={"type": "json_object"}. We rely
# on the prompt itself asking for JSON, and whybroke's _parse_response handles
# code-fenced output.
OPENROUTER_NO_JSON_MODE = {
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
}

REQUIRED_FIELDS = {
    "exception_type",
    "confidence_score",
    "root_cause",
    "reasoning",
    "evidence_lines",
    "suggested_fix",
}


class LLMResponseError(Exception):
    def __init__(self, message: str, raw_response: str = ""):
        super().__init__(message)
        self.raw_response = raw_response


class LLMProviderError(Exception):
    pass


def analyze(
    system_prompt: str,
    user_content: str,
    provider: str,
    api_key: str,
    model: str | None = None,
) -> dict:
    if provider not in DEFAULT_MODELS:
        raise LLMProviderError(f"Unknown provider: {provider}")

    model = model or DEFAULT_MODELS.get(provider)
    if not model:
        raise LLMProviderError(
            f"Provider '{provider}' requires an explicit model (pass --model)."
        )

    if provider == "openai":
        raw = _call_openai(system_prompt, user_content, api_key, model)
    elif provider == "anthropic":
        raw = _call_anthropic(system_prompt, user_content, api_key, model)
    elif provider == "gemini":
        raw = _call_gemini(system_prompt, user_content, api_key, model)
    elif provider == "grok":
        raw = _call_grok(system_prompt, user_content, api_key, model)
    elif provider == "openrouter":
        raw = _call_openrouter(system_prompt, user_content, api_key, model)
    elif provider == "litellm":
        raw = _call_litellm(system_prompt, user_content, api_key, model)
    elif provider == "zai":
        raw = _call_zai(system_prompt, user_content, api_key, model)
    elif provider == "nvidia":
        raw = _call_nvidia(system_prompt, user_content, api_key, model)
    else:
        raise LLMProviderError(f"Unknown provider: {provider}")

    return _parse_response(raw)


def _call_openai(system_prompt: str, user_content: str, api_key: str, model: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return resp.choices[0].message.content or ""


def _call_anthropic(system_prompt: str, user_content: str, api_key: str, model: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    parts = [block.text for block in resp.content if getattr(block, "type", None) == "text"]
    return "".join(parts)


def _call_gemini(system_prompt: str, user_content: str, api_key: str, model: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    return resp.text or ""


def _call_grok(system_prompt: str, user_content: str, api_key: str, model: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=GROK_BASE_URL)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return resp.choices[0].message.content or ""


def _call_openrouter(
    system_prompt: str, user_content: str, api_key: str, model: str
) -> str:
    from openai import OpenAI

    client = OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={
            "HTTP-Referer": "https://github.com/FireBolt922/whybroke",
            "X-Title": "whybroke",
        },
    )

    # Build fallback chain: user-picked model first, then remaining free models.
    # If the user explicitly chose a non-default model, we still try OpenRouter
    # free fallbacks after it — but only when the primary fails.
    candidates = [model]
    for fb in OPENROUTER_FREE_FALLBACKS:
        if fb not in candidates:
            candidates.append(fb)

    last_exc: Exception | None = None
    last_raw: str = ""
    for candidate in candidates:
        if candidate in OPENROUTER_NO_SYSTEM_PROMPT:
            messages = [
                {
                    "role": "user",
                    "content": f"{system_prompt}\n\n---\n\n{user_content}",
                }
            ]
        else:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]

        kwargs = {
            "model": candidate,
            "messages": messages,
            "temperature": 0,
        }
        if candidate not in OPENROUTER_NO_JSON_MODE:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = client.chat.completions.create(**kwargs)
            raw = resp.choices[0].message.content or ""
        except Exception as e:
            last_exc = e
            if not _is_retryable_openrouter_error(e):
                raise
            continue

        # Validate JSON before returning. Free models sometimes emit malformed
        # JSON (e.g. unescaped quotes inside string values). When that happens,
        # fall through to the next model instead of failing the whole call.
        last_raw = raw
        try:
            _parse_response(raw)
            return raw
        except LLMResponseError as e:
            last_exc = e
            continue

    if last_raw:
        # Surface the last raw payload so the user sees what came back.
        raise LLMResponseError(
            f"All OpenRouter models returned malformed JSON. Last error: {last_exc}",
            raw_response=last_raw,
        )
    raise LLMProviderError(
        f"All OpenRouter models failed. Last error: {last_exc}"
    ) from last_exc


def _is_retryable_openrouter_error(exc: Exception) -> bool:
    name = type(exc).__name__
    if name in {
        "RateLimitError",
        "NotFoundError",
        "APIStatusError",
        "InternalServerError",
    }:
        return True
    msg = str(exc).lower()
    retryable_markers = (
        "rate limit",
        "429",
        "model not found",
        "no endpoints found",
        "404",
        "503",
        "502",
        "overloaded",
        "provider returned error",
        "developer instruction is not enabled",
        "response_format",
        "system role",
        "system message",
        "system prompt",
    )
    return any(s in msg for s in retryable_markers)


def _call_openai_compatible(
    system_prompt: str,
    user_content: str,
    api_key: str,
    model: str,
    base_url: str,
) -> str:
    """Shared handler for OpenAI-compatible endpoints (zai, nvidia).

    GLM and other open models inconsistently honor response_format=json_object;
    on the first 4xx that mentions response_format we retry without it. The
    prompt itself demands JSON and _parse_response handles code-fenced output.
    """
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0,
        )
    except Exception as e:
        if "response_format" not in str(e).lower():
            raise
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
    return resp.choices[0].message.content or ""


def _call_zai(system_prompt: str, user_content: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(
        system_prompt, user_content, api_key, model, ZAI_BASE_URL
    )


def _call_nvidia(system_prompt: str, user_content: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(
        system_prompt, user_content, api_key, model, NVIDIA_BASE_URL
    )


def _call_litellm(system_prompt: str, user_content: str, api_key: str, model: str) -> str:
    import litellm

    resp = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        api_key=api_key,
        temperature=0,
        response_format={"type": "json_object"},
    )
    return resp["choices"][0]["message"]["content"] or ""


def _parse_response(raw: str) -> dict:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = _strip_code_fence(text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMResponseError(
            f"LLM returned malformed JSON: {e}", raw_response=raw
        ) from e

    if not isinstance(data, dict):
        raise LLMResponseError(
            "LLM response was not a JSON object", raw_response=raw
        )

    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        raise LLMResponseError(
            f"LLM response missing required fields: {sorted(missing)}",
            raw_response=raw,
        )

    if not isinstance(data["confidence_score"], int) or not (
        0 <= data["confidence_score"] <= 100
    ):
        raise LLMResponseError(
            "confidence_score must be an integer 0-100", raw_response=raw
        )

    if not isinstance(data["evidence_lines"], list):
        raise LLMResponseError("evidence_lines must be a list", raw_response=raw)

    # lesson is optional — normalise null/missing/non-dict to None so callers
    # can always do `result.get("lesson") or {}` safely.
    lesson = data.get("lesson")
    if not isinstance(lesson, dict):
        data["lesson"] = None

    return data


def _strip_code_fence(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
