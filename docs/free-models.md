# Using whybroke for free

You don't need a paid OpenAI key to run whybroke. Below are the free options, ranked by how generous their free tier is (as of April 2026).

## Quick pick

| If you want... | Use |
|---|---|
| **A strong agentic-coding model, free, no card** | **Z.ai** — `glm-4.7-flash` |
| Free credits across NVIDIA's hosted catalog (Nemotron, Llama-4, DeepSeek-R1, GLM) | **NVIDIA NIM** — `z-ai/glm4.7` default |
| The most generous free tier on a frontier model | **Google Gemini** (1,500 requests/day) |
| Many free models behind one key, with automatic fallback | **OpenRouter** (Llama 3.3 70B, DeepSeek R1, Gemma 3, Qwen — ~50 RPD free) |
| Ultra-fast inference, Llama 3.3 70B at 700+ tok/s | **Groq via litellm** (1,000 RPD) |
| Nothing leaves your machine | **Ollama via litellm** (unlimited, local) |

---

## Option 1 — Z.ai GLM-4.7 (recommended for free coding help)

GLM-4.7 is Z.ai's agentic-coding model — strong on Python tracebacks and diff generation. The `flash` variant is fully free with no credit card.

### Setup

1. Sign up at [https://z.ai](https://z.ai) and create an API key in the console.
2. In your terminal:

   ```bash
   whybroke auth
   # Provider: zai
   # Enter zai API key: <paste>
   ```

3. Test it:

   ```bash
   python examples/04_zero_division.py 2>&1 | whybroke
   ```

### Picking a different GLM model

Default is `glm-4.7-flash` (free). Override for the larger paid models:

```bash
whybroke --model glm-4.7         # full GLM-4.7
whybroke --model glm-5.1         # newer, paid
```

GLM models occasionally don't honor `response_format=json_object` — whybroke automatically retries the call without that flag and falls back to fence-stripping the JSON.

---

## Option 2 — NVIDIA NIM (free credits, broad catalog)

NVIDIA's hosted catalog at [build.nvidia.com](https://build.nvidia.com) gives free credits and exposes an OpenAI-compatible endpoint at `integrate.api.nvidia.com/v1`. Beyond GLM-4.7 it unlocks Nemotron, Llama-4, Qwen3, DeepSeek-R1, and more.

### Setup

1. Sign up at [https://build.nvidia.com](https://build.nvidia.com) (free, no card for the starter tier).
2. Generate an API key (`nvapi-...`).
3. In your terminal:

   ```bash
   whybroke auth
   # Provider: nvidia
   # Enter nvidia API key: <paste nvapi-... key>
   ```

### Picking a different NVIDIA-hosted model

Default is `z-ai/glm4.7`. Override with `--model`:

```bash
whybroke --model nvidia/nemotron-3-super-120b-a12b
whybroke --model meta/llama-4-maverick-17b-128e-instruct
whybroke --model deepseek-ai/deepseek-r1
whybroke --model qwen/qwen3-235b-a22b
```

Browse the full catalog at [build.nvidia.com/models](https://build.nvidia.com/models).

---

## Option 3 — OpenRouter (recommended for breadth)

One API key gives you access to ~29 free models. whybroke ships with an automatic fallback chain: if the primary model is rate-limited, it retries on DeepSeek R1 → Gemma 3 → Qwen 2.5 without you noticing.

### Setup

1. Go to [https://openrouter.ai](https://openrouter.ai) and sign up (GitHub or email — no credit card required for free-tier use).
2. Open [https://openrouter.ai/keys](https://openrouter.ai/keys) → **Create Key** → copy the `sk-or-v1-...` key.
3. In your terminal:

   ```bash
   whybroke auth
   # Provider: openrouter
   # Enter openrouter API key: <paste>
   ```

4. Test it:

   ```bash
   python examples/04_zero_division.py 2>&1 | whybroke
   ```

### Free-tier limits

- **50 requests/day** shared across all free models (with a $0 balance).
- **20 requests/minute.**
- Adding even a small balance ($5+) raises daily cap to ~200 RPD per model.

### Picking a different free model

Default is `openrouter/free` — OpenRouter's own meta-router that picks any live free model for you. This is the most resilient choice because free model IDs change month to month.

Override with `--model` to pin a specific one:

```bash
whybroke --model google/gemma-4-31b-it:free
whybroke --model nvidia/nemotron-3-super-120b-a12b:free
whybroke --model google/gemma-4-26b-a4b-it:free
```

Browse the current list at [https://openrouter.ai/models?pricing=free](https://openrouter.ai/models?pricing=free).

The automatic fallback kicks in when a call fails with rate-limit / 404 / malformed JSON / unsupported feature — so a manual `--model` pick is respected on the happy path but never leaves you stuck when a specific ID goes offline.

---

## Option 4 — Google Gemini (most generous free tier)

Gemini 2.5 Flash on Google AI Studio's free tier is the single most generous free frontier model: **1,500 requests/day**, 1M-token context.

### Setup

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey).
2. **Create API key** → copy it.
3. In your terminal:

   ```bash
   whybroke auth
   # Provider: gemini
   # Enter gemini API key: <paste>
   ```

4. Test: `python examples/04_zero_division.py 2>&1 | whybroke`

---

## Option 5 — Groq via `litellm` (fastest)

Groq serves Llama 3.3 70B at ~700 tokens/second. No native provider needed — use whybroke's `litellm` router.

### Setup

1. Go to [https://console.groq.com](https://console.groq.com) and sign up (free, no card).
2. [https://console.groq.com/keys](https://console.groq.com/keys) → **Create API Key** → copy.
3. Configure whybroke:

   ```bash
   whybroke auth
   # Provider: litellm
   # Enter litellm API key: <paste Groq key>
   ```

4. Run with Groq-prefixed model:

   ```bash
   python my_script.py 2>&1 | whybroke --model groq/llama-3.3-70b-versatile
   ```

### Limits
30 RPM, 1,000 RPD, 6,000 TPM.

---

## Option 6 — Ollama (fully local, unlimited)

Runs on your laptop. Nothing ever leaves your machine.

### Setup

1. Install Ollama: [https://ollama.com](https://ollama.com) (macOS / Linux / Windows).
2. Pull a model — code-capable 8B model, fits in ~8 GB RAM:

   ```bash
   ollama pull llama3.1:8b
   ```

3. Configure whybroke (the key can be any string — it's ignored):

   ```bash
   whybroke auth
   # Provider: litellm
   # Enter litellm API key: none
   ```

4. Run:

   ```bash
   python my_script.py 2>&1 | whybroke --model ollama/llama3.1:8b
   ```

Smaller local models may produce lower-confidence output — whybroke's generic prompt caps confidence at 60% when there's no AST context, which is the right floor.

---

## FAQ

**Which do you recommend starting with?**
Z.ai (`glm-4.7-flash`) for the best free coding-fix experience — no card, GLM-4.7 is purpose-built for agentic coding. OpenRouter if you want to experiment with many models behind one key. Gemini if you want maximum free requests/day on a frontier model. Ollama (Option 6) if your code can't leave your machine.

**Can I switch providers later?**
Yes. Running `whybroke auth` again overwrites the stored key. `whybroke logout` removes credentials entirely.

**Does whybroke send my code anywhere?**
Only to the provider you configured. Use Ollama (Option 4) for zero external calls.

**What happens when I hit a rate limit?**
On OpenRouter, whybroke automatically retries on the next free model in the fallback chain. On other providers, you'll see a friendly rate-limit hint — switch provider or wait.
