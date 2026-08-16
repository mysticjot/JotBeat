"""
models.py — the model-agnostic adapter. The studio's senses, not its judgment.

Rules enforced here (BUDGET.md):
  - Only providers with a key present in the environment activate.
  - Per-role token caps are hard limits, enforced before the call.
  - On 429/rate-limit: fall through to the next provider in the chain.
  - Escalation ceiling: cheap -> frontier (shrunk context) -> human ticket.
  - Every call is ledgered. Credentials are never logged.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from ledger import log_call, log_event

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_FILE = ROOT / "studio" / "providers.json"


def load_routing() -> dict:
    return json.loads(PROVIDERS_FILE.read_text(encoding="utf-8"))


def active_providers(role: str) -> list[dict]:
    """Ordered provider chain for a role, filtered to providers with keys.
    'free' means $0 pricing, not keyless — but a provider with an EMPTY
    env_key (Ollama, LiteLLM, local servers) is keyless and always active."""
    routing = load_routing()
    chain = routing["roles"][role]["chain"]
    out = []
    for name in chain:
        p = routing["providers"][name]
        if not p.get("env_key") or os.environ.get(p["env_key"]):
            out.append(p)
    return out


class BudgetExceeded(Exception):
    pass


class AllProvidersExhausted(Exception):
    pass


class ModelAdapter:
    def __init__(
        self, role: str, cap_in: int | None = None, cap_out: int | None = None
    ):
        routing = load_routing()
        self.role = role
        # cap overrides exist for provider pings (no role context); normal
        # callers always use the role's caps from providers.json.
        self.cap_in = (
            cap_in if cap_in is not None else routing["roles"][role]["max_tokens_in"]
        )
        self.cap_out = (
            cap_out if cap_out is not None else routing["roles"][role]["max_tokens_out"]
        )

    def complete(
        self,
        instructions: str,
        context: list[str],
        task_id: str,
        output_schema: dict | None = None,
        escalation_level: int = 0,
        images: list | None = None,
    ) -> str:
        prompt_in = instructions + "\n\n" + "\n\n".join(context)
        est_in = len(prompt_in) // 4  # rough token estimate; provider returns exact
        # Images price by tiles, not characters — budget a flat 1000/image.
        est_in += 1000 * len(images or [])
        if est_in > self.cap_in:
            raise BudgetExceeded(
                f"[{self.role}] ~{est_in} input tokens exceeds cap {self.cap_in}. "
                "Shrink context (repo map instead of files, log tail, digest) — "
                "do NOT raise the cap mid-task."
            )

        chain = active_providers(self.role)
        if escalation_level > 0:
            chain = [p for p in chain if p.get("tier") == "escalation"] or chain

        last_err = None
        for provider in chain:
            t0 = time.time()
            try:
                resp = self._call(
                    provider, instructions, context, output_schema, images
                )
                log_call(
                    task_id=task_id,
                    role=self.role,
                    provider=provider["name"],
                    model=provider["model"],
                    tokens_in=resp["tokens_in"],
                    tokens_out=resp["tokens_out"],
                    cached_in=resp.get("cached_in", 0),
                    retry=0,
                    escalated=escalation_level > 0,
                    latency_ms=int((time.time() - t0) * 1000),
                )
                return resp["text"]
            except RateLimited as e:
                last_err = e
                log_event(
                    "provider_error",
                    task=task_id,
                    role=self.role,
                    provider=provider["name"],
                    error=str(e)[:300],
                )
                continue  # fall through the chain — never sleep and wait
            except Exception as e:
                last_err = e
                log_event(
                    "provider_error",
                    task=task_id,
                    role=self.role,
                    provider=provider["name"],
                    error=str(e)[:300],
                )
                continue
        raise AllProvidersExhausted(f"[{self.role}] all providers failed: {last_err}")

    def _call(
        self, provider, instructions, context, output_schema, images=None
    ) -> dict:
        """Dispatch on the provider's API FAMILY — never on its name.
        Any OpenAI-compatible endpoint (hosted or self-hosted) is config-only."""
        family = provider.get("family")
        if family == "google":
            if images:
                raise AllProvidersExhausted(
                    f"{provider['name']}: google family has no image path — "
                    "route vision through an OpenAI-compatible provider"
                )
            return self._call_google(provider, instructions, context)
        if family == "openai":
            return self._call_openai_compatible(
                provider, instructions, context, output_schema, images
            )
        raise AllProvidersExhausted(
            f"{provider['name']}: unsupported or missing family {family!r}"
        )

    def _call_openai_compatible(
        self, provider, instructions, context, output_schema, images=None
    ) -> dict:
        """One httpx client for every OpenAI-compatible endpoint —
        base_url + env key swapped, nothing else. `images` (file paths) become
        base64 data-URI content parts (OpenAI vision message shape)."""
        import base64
        import httpx

        api_key = (
            os.environ.get(provider["env_key"]) if provider.get("env_key") else None
        )
        if not api_key and not provider.get("free"):
            raise AllProvidersExhausted(f"missing env key {provider['env_key']}")

        user_content: object = "\n\n".join(context)
        if images:
            parts: list[dict] = [{"type": "text", "text": "\n\n".join(context)}]
            for img in images:
                data = base64.b64encode(Path(img).read_bytes()).decode()
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{data}"},
                    }
                )
            user_content = parts

        body: dict = {
            "model": provider["model"],
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": self.cap_out,
        }
        if output_schema:
            body["response_format"] = {"type": "json_object"}
        # Optional per-provider extra body params (providers.json "body" object)
        # — e.g. disabling a reasoning model's thinking so the token budget
        # goes to the answer, not to hidden reasoning_content. Config, not code.
        for bk, bv in (provider.get("body") or {}).items():
            body[bk] = bv

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        # Optional per-provider extra headers (providers.json "headers" object)
        # — covers api-key auth styles, referers, any quirk without code changes.
        # A value starting with "$" names an env var (resolved at call time),
        # so secret header values live in .env, never in the repo.
        for hk, hv in (provider.get("headers") or {}).items():
            headers[hk] = os.environ.get(hv[1:], "") if hv.startswith("$") else hv

        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{provider['base_url']}/chat/completions",
                headers=headers,
                json=body,
            )

        if resp.status_code == 429:
            raise RateLimited(f"{provider['name']}: HTTP 429")
        resp.raise_for_status()
        data = resp.json()

        usage = data.get("usage", {})
        content = data["choices"][0]["message"].get("content")
        # Some providers return content as a list of parts, or null on
        # truncation/refusal — normalize; an empty completion is a failed
        # call so the chain falls through to the next provider.
        if isinstance(content, list):
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
        if not content:
            ch0 = data["choices"][0]
            reasoning = ch0.get("message", {}).get("reasoning_content")
            hint = (
                "reasoning model exhausted max_tokens on thinking — "
                'disable thinking via the provider\'s "body" config'
                if reasoning
                else "truncation or refusal"
            )
            raise AllProvidersExhausted(
                f"{provider['name']}: empty completion "
                f"(finish_reason={ch0.get('finish_reason')}; {hint})"
            )
        return {
            "text": content,
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            # OpenAI-compatible cache-hit field -> cached_in (BUDGET.md cost model)
            "cached_in": usage.get("prompt_cache_hit_tokens", 0),
        }

    def _call_google(self, provider, instructions, context) -> dict:
        """The google family — via the google-genai SDK (not OpenAI-compatible)."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ.get(provider["env_key"]))
        resp = client.models.generate_content(
            model=provider["model"],
            contents="\n\n".join(context),
            config=types.GenerateContentConfig(
                system_instruction=instructions,
                max_output_tokens=self.cap_out,
                # Gemini 3.x spends output tokens on "thinking" first —
                # without this, small caps return empty text (tokens_out=0).
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        usage = resp.usage_metadata
        return {
            "text": resp.text,
            "tokens_in": getattr(usage, "prompt_token_count", 0) or 0,
            "tokens_out": getattr(usage, "candidates_token_count", 0) or 0,
            "cached_in": getattr(usage, "cached_content_token_count", 0) or 0,
        }


def ping_provider(name: str) -> dict:
    """Minimal live ping for `jotbeat provider test` — one tiny completion
    through the adapter, ledgered like any call. Never raises: a failed ping
    returns ok=False and leaves the entry registered but unverified.
    Returns {"ok", "latency_ms", "tokens_in", "tokens_out", "error"}."""
    routing = load_routing()
    provider = routing["providers"].get(name)
    if provider is None:
        return {
            "ok": False,
            "latency_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "error": f"unknown provider: {name}",
        }
    if provider.get("env_key") and not os.environ.get(provider["env_key"]):
        return {
            "ok": False,
            "latency_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "error": f"env key not set: {provider['env_key']}",
        }

    adapter = ModelAdapter("provider-test", cap_in=1000, cap_out=16)
    t0 = time.time()
    try:
        resp = adapter._call(provider, "Reply with the word: ok", ["ping"], None)
    except Exception as e:
        return {
            "ok": False,
            "latency_ms": int((time.time() - t0) * 1000),
            "tokens_in": 0,
            "tokens_out": 0,
            "error": f"{type(e).__name__}: {e}",
        }

    latency = int((time.time() - t0) * 1000)
    log_call(
        task_id="provider-test",
        role="provider_test",
        provider=provider["name"],
        model=provider["model"],
        tokens_in=resp["tokens_in"],
        tokens_out=resp["tokens_out"],
        cached_in=resp.get("cached_in", 0),
        retry=0,
        escalated=False,
        latency_ms=latency,
    )
    return {
        "ok": True,
        "latency_ms": latency,
        "tokens_in": resp["tokens_in"],
        "tokens_out": resp["tokens_out"],
        "error": None,
    }


class RateLimited(Exception):
    pass
