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
    if not env_key or not env_key.strip():
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
