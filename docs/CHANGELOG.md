# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [semver](https://semver.org/).

## [Unreleased]

### Added
- Phase 2 orchestrator: LangGraph task loop (`studio/orchestrator.py`, `state.py`, `ledger.py`, `models.py` integrated as-is from the brain handoff); `roles/` with `dispatch()` + 9 role modules + auditor; deterministic `tools/` (BVT shell, Playwright browser, git commit); CLI commands `brief` / `plan` / `run-next` / `verify` / `report`.
- OpenAI-compatible provider client in `models.py._call` (httpx; DeepSeek/Qwen/Kimi/GLM/MiniMax/Groq share base_url+env-key swap; Gemini via google-genai); DeepSeek `prompt_cache_hit_tokens` mapped to `cached_in`.
- `providers.json` v3 routing table (per-model entries, free tiers, base_urls); `task-queue.json` `{"items": []}` schema with underscore statuses incl. `BLOCKED_HUMAN`.
- `studio/test_graph_live.py` in CI (Python 3.12 via setup-python); `requirements.txt` pins langgraph + langgraph-checkpoint-sqlite.
- ADR-0002: no Phaser runtime global in ESM builds — explicit imports only.
- Provider CLI (Phase 3 Addendum A): `jotbeat provider list|add|remove|test` + `jotbeat route set` — full model agnosticism, no hand-edited JSON, key presence only (never values). `provider test` pings through ModelAdapter, ledgered, never crashes the loop; `provider remove` refuses while chained; `route set` validates names and warns on diversification violations.
- `family` field on every provider entry; `models.py._call` dispatches on family ONLY (`openai` → shared httpx client, `google` → google-genai) — zero provider-name strings in models.py. Any OpenAI-compatible endpoint (incl. self-hosted) is now a pure config add.
- `studio/test_provider_cli.py` — add/route/remove round-trip acceptance test, wired into CI.
- Keys CLI (Phase 3 Addendum B): `jotbeat keys set|list|remove` — masked getpass input, atomic .env writes (temp + rename, comments/unrelated lines preserved), `git check-ignore` guard fails closed, char-count confirmations only, expected key names derived from providers.json (stale lines flagged). `studio/tools/keys.py` is the single writer.
- Settings UI (Phase 3 Addendum C): `jotbeat ui` — stdlib-only local server bound to 127.0.0.1 (non-loopback refused), self-contained HTML page with API Keys (masked, never rendered back), Providers (add/remove incl. custom headers), Role Routing (primary/fallback, diversification warnings). All writes share the CLI's writer modules. `studio/test_ui.py` + `studio/test_keys_cli.py` in CI.
- Optional per-provider `headers` object merged into requests; `$ENV_VAR` values resolve from the environment so secret headers stay out of the repo. `provider add --header KEY=VALUE` (repeatable); UNIVERSAL COMPATIBILITY RULE (non-OpenAI API → local LiteLLM proxy, never per-vendor code) documented in `--help`.
- Quality gate (AGENTS.md §6): `jotbeat quality` (`studio/tools/quality.py`) runs aislop (error-level findings must be 0) + fallow dead-code/dupes (must be clean) via npx — no global installs needed, same gate runs in CI. `.aislop/config.yml` pins `ci.failBelow: 40` baseline (ratchet up only). `.fallowrc.json` scopes fallow to `game/` and suppresses verified false positives (publicDir `style.css` pair, ADR-0001 `DebugState`, Phaser lifecycle hooks with inline documented ignores).

### Fixed
- aislop first scan (24/100, 5 errors): removed dead `typing.Any` import in `orchestrator.py`; replaced 4 bare except-pass sentinels with `contextlib.suppress` + stated intent (`keys.py` temp-file cleanup, `ui_server.py` best-effort logging / pythonw stdout). `aislop fix --safe` applied (formatting, import sorting) — score 40/100, 0 errors.
- Settings UI: Save/Test/Remove clicks could fail silently when the settings server was unreachable (dead pythonw instance) — `fetch` errors are now caught and surfaced as an explicit message ("cannot reach the settings server — relaunch JotBeat Studio.bat"). Save success confirms inline ("NAME set (N chars)", field clears, row flips to "set · N chars", dot goes green). Browser click-tested end-to-end via Playwright on both the CLI and .bat launch paths.
- Windows cp1252 decode crash in `tools/shell.py` / `tools/browser.py` subprocess reads (now UTF-8 with `errors="replace"`).
- `orchestrator.py patch()` KeyError when reached from build/QA failure without an audit record.

### Changed
- `jotbeat verify` is now the phase-end endpoint (AGENTS.md §1): BVT + scripted QA + the §6 quality gate (aislop + fallow) in one command; all three must pass or it exits 1. A phase gate declared without a green quality run is void.
- Provider routing correction (HANDOFF-PHASE3 §2): triage diversification restored via `groq-free-8b` (llama-3.1-8b-instant); producer → gemini-free → deepseek-v4-flash; auditor chain kimi-k2.6 → glm-4.7 → glm-4.7-flash; vision glm-4.6v-flash → glm-4.6v (`ZAI_API_KEY`); MiniMax removed (M-series is text-only); prices synced to the verified table (HANDOFF-PHASE2 §4, Aug 15 2026).
- Qwen routing: DashScope entries removed; coder model now routes through OpenRouter free tier (`qwen/qwen3-coder:free`, `OPENROUTER_API_KEY`). Coder chain: groq-free → openrouter-qwen3-coder-free → deepseek-v4-flash.
- `models.py active_providers` activates only providers whose env key exists (free tiers are not keyless), per AGENTS.md §5.
- BUDGET.md per-role caps table mirrors providers.json roles v3.

- Phase 1 game scaffold: Phaser 4 + TypeScript + Vite from the official `template-vite-ts` (phaser 4.0.0).
- Boot → Title → Game scenes; greybox dungeon (LDtk project validated against official 1.5.3 schema, Tiled JSON export served from `assets/maps/`); wall collision; player movement; camera follow.
- `src/debug.ts`: `window.__game.state` + deterministic seed hook (ADR-0001).
- Playwright smoke suite (`game/tests/smoke.spec.ts`) asserting game state headless; CI runs build + tests.
- Phase 0 foundation: repository tree, document templates, state schemas, provider routing table, CI skeleton.
