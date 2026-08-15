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

### Fixed
- Windows cp1252 decode crash in `tools/shell.py` / `tools/browser.py` subprocess reads (now UTF-8 with `errors="replace"`).
- `orchestrator.py patch()` KeyError when reached from build/QA failure without an audit record.

### Changed
- Provider routing correction (HANDOFF-PHASE3 §2): triage diversification restored via `groq-free-8b` (llama-3.1-8b-instant); producer → gemini-free → deepseek-v4-flash; auditor chain kimi-k2.6 → glm-4.7 → glm-4.7-flash; vision glm-4.6v-flash → glm-4.6v (`ZAI_API_KEY`); MiniMax removed (M-series is text-only); prices synced to the verified table (HANDOFF-PHASE2 §4, Aug 15 2026).
- Qwen routing: DashScope entries removed; coder model now routes through OpenRouter free tier (`qwen/qwen3-coder:free`, `OPENROUTER_API_KEY`). Coder chain: groq-free → openrouter-qwen3-coder-free → deepseek-v4-flash.
- `models.py active_providers` activates only providers whose env key exists (free tiers are not keyless), per AGENTS.md §5.
- BUDGET.md per-role caps table mirrors providers.json roles v3.

- Phase 1 game scaffold: Phaser 4 + TypeScript + Vite from the official `template-vite-ts` (phaser 4.0.0).
- Boot → Title → Game scenes; greybox dungeon (LDtk project validated against official 1.5.3 schema, Tiled JSON export served from `assets/maps/`); wall collision; player movement; camera follow.
- `src/debug.ts`: `window.__game.state` + deterministic seed hook (ADR-0001).
- Playwright smoke suite (`game/tests/smoke.spec.ts`) asserting game state headless; CI runs build + tests.
- Phase 0 foundation: repository tree, document templates, state schemas, provider routing table, CI skeleton.
