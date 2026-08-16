"""tools/routing.py — the ONLY writer for providers.json (HANDOFF-PHASE3
Addenda A/C). Shared by the CLI and the settings UI — one writer module,
one file shape. Reads/writes the routing table; validates on every mutation.

UNIVERSAL COMPATIBILITY RULE: any API must be usable for any role without
new code. OpenAI-compatible endpoint -> family "openai" (+ optional custom
headers). Non-compatible API -> run a local LiteLLM proxy and point a
family-"openai" entry at http://localhost:4000/v1. NEVER per-vendor code.
"""

from __future__ import annotations

import json
from pathlib import Path

PROVIDER_FAMILIES = ("openai", "google")
PROVIDER_TIERS = ("free", "bulk", "escalation")

# Quick-add presets — `jotbeat provider add ollama` (or the UI dropdown)
# fills everything detectable; flags/fields only override. "keyless"
# providers are local servers that need no API key at all.
# Prices for paid presets mirror the entries already in providers.json.
PRESETS: dict[str, dict] = {
    "ollama": {
        # Ollama CLOUD (ollama.com) — hosted models, no local install,
        # needs an API key from ollama.com. OpenAI-compatible /v1 endpoint.
        "base_url": "https://ollama.com/v1",
        "env_key": "OLLAMA_API_KEY",
        "family": "openai",
        "tier": "free",
        "free": True,
        "models": [
            "gpt-oss:120b",
            "gpt-oss:20b",
            "qwen3.5:397b",
            "deepseek-v4-flash:0731",
            "deepseek-v4-pro:0813",
            "kimi-k2.6",
            "kimi-k2.7-code",
            "kimi-k3",
            "glm-5.1",
            "glm-5.2",
            "minimax-m2.7",
            "minimax-m3",
            "mistral-large-3:675b",
            "nemotron-3-super",
            "nemotron-3-ultra",
            "nemotron-3-nano:30b",
            "gemma4:31b",
        ],
    },
    "ollama-local": {
        # Local Ollama server (localhost:11434) — models must be pulled first.
        "base_url": "http://localhost:11434/v1",
        "env_key": "",
        "family": "openai",
        "tier": "free",
        "free": True,
        "keyless": True,
        "models": [],  # live from the local server
    },
    "litellm": {
        "base_url": "http://localhost:4000/v1",
        "env_key": "",
        "family": "openai",
        "tier": "free",
        "free": True,
        "keyless": True,
        "models": [],
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "family": "openai",
        "tier": "free",
        "free": True,
        "models": [
            "cohere/north-mini-code:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "google/gemma-4-31b-it:free",
            "openai/gpt-oss-20b:free",
        ],
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "family": "openai",
        "tier": "free",
        "free": True,
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
        "family": "openai",
        "tier": "bulk",
        "price_in": 0.14,
        "price_out": 0.28,
        "price_cached_in": 0.0028,
        "models": ["deepseek-v4-flash", "deepseek-v4-pro"],
    },
    "zai": {
        "base_url": "https://api.z.ai/api/paas/v4",
        "env_key": "ZAI_API_KEY",
        "family": "openai",
        "tier": "bulk",
        "models": [
            "glm-4.7-flash",
            "glm-4.6v-flash",
            "glm-4.7",
            "glm-4.6v",
            "glm-5",
            "glm-5-turbo",
            "glm-5.1",
            "glm-5.2",
            "glm-5.3",
        ],
    },
    "kimi": {
        "base_url": "https://api.moonshot.ai/v1",
        "env_key": "KIMI_API_KEY",
        "family": "openai",
        "tier": "bulk",
        "models": ["kimi-k2.6"],
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "env_key": "MISTRAL_API_KEY",
        "family": "openai",
        "tier": "free",
        "free": True,
        "models": ["mistral-small-latest"],
    },
    "cerebras": {
        "base_url": "https://api.cerebras.ai/v1",
        "env_key": "CEREBRAS_API_KEY",
        "family": "openai",
        "tier": "free",
        "free": True,
        "models": ["llama-3.3-70b"],
    },
    "gemini": {
        "base_url": None,
        "env_key": "GEMINI_API_KEY",
        "family": "google",
        "tier": "free",
        "free": True,
        "models": ["gemini-3.5-flash"],
    },
    "github-models": {
        "base_url": "https://models.github.ai/inference",
        "env_key": "GITHUB_TOKEN",
        "family": "openai",
        "tier": "free",
        "free": True,
        "models": [],
    },
    "opencode": {
        # OpenCode Zen — OpenAI-compatible curated gateway (opencode.ai/docs/zen)
        "base_url": "https://opencode.ai/zen/v1",
        "env_key": "OPENCODE_API_KEY",
        "family": "openai",
        "tier": "free",
        "free": True,
        "models": ["deepseek-v4-flash"],
    },
}
PRESET_ALIASES = {
    "moonshot": "kimi",
    "google": "gemini",
    "github": "github-models",
    "opencode-zen": "opencode",
    "zen": "opencode",
}


def detect_preset(hint: str) -> tuple[str, dict] | None:
    """Match a hint ('ollama', 'groq', ...) to a preset. Returns
    (preset_name, fields) or None."""
    h = (hint or "").strip().lower()
    h = PRESET_ALIASES.get(h, h)
    if h in PRESETS:
        return h, dict(PRESETS[h])
    return None


def ollama_models() -> list[str]:
    """List models installed on the local Ollama server.
    Raises RoutingError if the server isn't running."""
    import httpx

    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=5)
        r.raise_for_status()
    except Exception as e:
        raise RoutingError(
            f"Ollama server not reachable at localhost:11434 ({e}) — "
            "install it from ollama.com and run `ollama pull <model>` first"
        )
    return [m["name"] for m in r.json().get("models", [])]


class RoutingError(Exception):
    """Refusal — loud, safe, file untouched."""


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(routing: dict, path: Path) -> None:
    path.write_text(json.dumps(routing, indent=2) + "\n", encoding="utf-8")


def roles_using(routing: dict, name: str) -> list[str]:
    return [r for r, cfg in routing["roles"].items() if name in cfg["chain"]]


def build_entry(
    name: str,
    env_key: str,
    base_url: str | None,
    model: str,
    family: str,
    tier: str,
    price_in: float,
    price_out: float,
    price_cached_in: float | None = None,
    free: bool = False,
    headers: dict | None = None,
    keyless: bool = False,
) -> dict:
    """Validate and build a provider entry. Raises RoutingError on bad shape."""
    name = (name or "").strip()
    if not name:
        raise RoutingError("provider name is required")
    if family not in PROVIDER_FAMILIES:
        raise RoutingError(f"family must be one of {PROVIDER_FAMILIES}")
    if tier not in PROVIDER_TIERS:
        raise RoutingError(f"tier must be one of {PROVIDER_TIERS}")
    if family == "openai" and not base_url:
        raise RoutingError("base_url is required for family=openai")
    if keyless:
        env_key = ""  # local server (Ollama, LiteLLM) — no credential at all
        free = True
    elif not env_key or not env_key.strip():
        raise RoutingError("env_key (the variable NAME, not the value) is required")
    if not model or not model.strip():
        raise RoutingError("model is required")
    for label, v in (("price_in", price_in), ("price_out", price_out)):
        if v is None or v < 0:
            raise RoutingError(f"{label} must be a non-negative number")

    entry = {
        "name": name,
        "provider": name,
        "model": model.strip(),
        "env_key": env_key.strip(),
        "free": bool(free),
        "tier": tier,
        "family": family,
        "base_url": base_url or None,
        "price_in": float(price_in),
        "price_out": float(price_out),
    }
    if price_cached_in is not None:
        entry["price_cached_in"] = float(price_cached_in)
    if headers:
        entry["headers"] = {str(k): str(v) for k, v in headers.items()}
    return entry


def add_provider(routing: dict, entry: dict) -> None:
    name = entry["name"]
    if name in routing["providers"]:
        raise RoutingError(f"provider '{name}' already exists")
    routing["providers"][name] = entry


def remove_provider(routing: dict, name: str) -> None:
    if name not in routing["providers"]:
        raise RoutingError(f"unknown provider: {name}")
    refs = roles_using(routing, name)
    if refs:
        raise RoutingError(
            f"'{name}' is still in role chains: {', '.join(refs)} — "
            "re-route those roles first"
        )
    del routing["providers"][name]


def add_role(
    routing: dict, role: str, chain: list[str], max_in: int, max_out: int
) -> None:
    """Register a NEW role with its chain and token caps. Refuses to
    overwrite an existing role — re-chain those with set_role_chain."""
    role = (role or "").strip()
    if not role:
        raise RoutingError("role name required")
    if role in routing["roles"]:
        raise RoutingError(
            f"role '{role}' already exists — use route set to re-chain it"
        )
    missing = [n for n in chain if n not in routing["providers"]]
    if missing:
        raise RoutingError(f"unknown providers: {', '.join(missing)}")
    if not chain:
        raise RoutingError("chain must name at least one provider")
    if max_in <= 0 or max_out <= 0:
        raise RoutingError("token caps must be positive")
    routing["roles"][role] = {
        "chain": list(chain),
        "max_tokens_in": max_in,
        "max_tokens_out": max_out,
    }


def set_role_chain(routing: dict, role: str, chain: list[str]) -> list[str]:
    """Replace a role's chain. Returns diversification warnings (allowed)."""
    if role not in routing["roles"]:
        raise RoutingError(
            f"unknown role: {role} — known: {', '.join(sorted(routing['roles']))}"
        )
    missing = [n for n in chain if n not in routing["providers"]]
    if missing:
        raise RoutingError(f"unknown providers: {', '.join(missing)}")

    warnings = []
    primary = chain[0]
    for other, cfg in routing["roles"].items():
        if other != role and cfg["chain"] and cfg["chain"][0] == primary:
            warnings.append(
                f"'{primary}' is also primary for role '{other}' "
                "(diversification rule) — allowed, flagged"
            )
    routing["roles"][role]["chain"] = list(chain)
    return warnings
