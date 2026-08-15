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

from ledger import log_call

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS_FILE = ROOT / "studio" / "providers.json"


def load_routing() -> dict:
    return json.loads(PROVIDERS_FILE.read_text(encoding="utf-8"))


def active_providers(role: str) -> list[dict]:
    """Ordered provider chain for a role, filtered to providers with keys.
    'free' means $0 pricing, not keyless — every tier still needs its env key."""
    routing = load_routing()
    chain = routing["roles"][role]["chain"]
    out = []
    for name in chain:
        p = routing["providers"][name]
        if os.environ.get(p["env_key"]):
            out.append(p)
    return out


class BudgetExceeded(Exception):
    pass


class AllProvidersExhausted(Exception):
    pass


class ModelAdapter:
    def __init__(self, role: str):
        routing = load_routing()
        self.role = role
        self.cap_in = routing["roles"][role]["max_tokens_in"]
        self.cap_out = routing["roles"][role]["max_tokens_out"]

    def complete(
        self,
        instructions: str,
        context: list[str],
        task_id: str,
        output_schema: dict | None = None,
        escalation_level: int = 0,
    ) -> str:
        prompt_in = instructions + "\n\n" + "\n\n".join(context)
        est_in = len(prompt_in) // 4  # rough token estimate; provider returns exact
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
                resp = self._call(provider, instructions, context, output_schema)
                log_call(
                    task_id=task_id, role=self.role,
                    provider=provider["name"], model=provider["model"],
                    tokens_in=resp["tokens_in"], tokens_out=resp["tokens_out"],
                    cached_in=resp.get("cached_in", 0),
                    retry=0, escalated=escalation_level > 0,
                    latency_ms=int((time.time() - t0) * 1000),
                )
                return resp["text"]
            except RateLimited as e:
                last_err = e
                continue  # fall through the chain — never sleep and wait
            except Exception as e:
                last_err = e
                continue
        raise AllProvidersExhausted(f"[{self.role}] all providers failed: {last_err}")

    def _call(self, provider, instructions, context, output_schema) -> dict:
        """Dispatch to the provider's API. One small client per provider family."""
        if provider.get("provider") == "google":
            return self._call_gemini(provider, instructions, context)
        return self._call_openai_compatible(provider, instructions, context, output_schema)

    def _call_openai_compatible(self, provider, instructions, context, output_schema) -> dict:
        """One httpx client for every OpenAI-compatible provider (DeepSeek,
        DashScope/Qwen, Moonshot/Kimi, z.ai/GLM, MiniMax, Groq, Cerebras,
        Mistral, OpenRouter) — base_url + env key swapped, nothing else."""
        import httpx

        api_key = os.environ.get(provider["env_key"])
        if not api_key and not provider.get("free"):
            raise AllProvidersExhausted(f"missing env key {provider['env_key']}")

        body: dict = {
            "model": provider["model"],
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": "\n\n".join(context)},
            ],
            "max_tokens": self.cap_out,
        }
        if output_schema:
            body["response_format"] = {"type": "json_object"}

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

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
        return {
            "text": data["choices"][0]["message"]["content"],
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            # DeepSeek: prompt_cache_hit_tokens -> cached_in (BUDGET.md cost model)
            "cached_in": usage.get("prompt_cache_hit_tokens", 0),
        }

    def _call_gemini(self, provider, instructions, context) -> dict:
        """Gemini via google-genai (the one non-OpenAI-compatible provider)."""
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ.get(provider["env_key"]))
        resp = client.models.generate_content(
            model=provider["model"],
            contents="\n\n".join(context),
            config=types.GenerateContentConfig(
                system_instruction=instructions,
                max_output_tokens=self.cap_out,
            ),
        )
        usage = resp.usage_metadata
        return {
            "text": resp.text,
            "tokens_in": getattr(usage, "prompt_token_count", 0) or 0,
            "tokens_out": getattr(usage, "candidates_token_count", 0) or 0,
            "cached_in": getattr(usage, "cached_content_token_count", 0) or 0,
        }


class RateLimited(Exception):
    pass
