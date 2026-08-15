# Changelog

All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/), versioning: [semver](https://semver.org/).

## [Unreleased]

### Added
- Phase 2 orchestrator: LangGraph task loop (`studio/orchestrator.py`, `state.py`, `ledger.py`, `models.py` integrated as-is from the brain handoff); `roles/` with `dispatch()` + 9 role modules + auditor; deterministic `tools/` (BVT shell, Playwright browser, git commit); CLI commands `brief` / `plan` / `run-next` / `verify` / `report`.
- OpenAI-compatible provider client in `models.py._call` (httpx; DeepSeek/Qwen/Kimi/GLM/MiniMax/Groq share base_url+env-key swap; Gemini via google-genai); DeepSeek `prompt_cache_hit_tokens` mapped to `cached_in`.
- `providers.json` v3 routing table (per-model entries, free tiers, base_urls); `task-queue.json` `{"items": []}` schema with underscore statuses incl. `BLOCKED_HUMAN`.
- `studio/test_graph_live.py` in CI (Python 3.12 via setup-python); `requirements.txt` pins langgraph + langgraph-checkpoint-sqlite.
- ADR-0002: no Phaser runtime global in ESM builds — explicit imports only.

### Fixed
- Windows cp1252 decode crash in `tools/shell.py` / `tools/browser.py` subprocess reads (now UTF-8 with `errors="replace"`).
- `orchestrator.py patch()` KeyError when reached from build/QA failure without an audit record.

### Changed
- Qwen routing: DashScope entries removed; coder model now routes through OpenRouter free tier (`qwen/qwen3-coder:free`, `OPENROUTER_API_KEY`). Coder chain: groq-free → openrouter-qwen3-coder-free → deepseek-v4-flash. Triage/producer re-pointed to the OpenRouter Qwen entry.
- `models.py active_providers` activates only providers whose env key exists (free tiers are not keyless), per AGENTS.md §5.
- BUDGET.md per-role caps table mirrors providers.json roles v3.

- Phase 1 game scaffold: Phaser 4 + TypeScript + Vite from the official `template-vite-ts` (phaser 4.0.0).
- Boot → Title → Game scenes; greybox dungeon (LDtk project validated against official 1.5.3 schema, Tiled JSON export served from `assets/maps/`); wall collision; player movement; camera follow.
- `src/debug.ts`: `window.__game.state` + deterministic seed hook (ADR-0001).
- Playwright smoke suite (`game/tests/smoke.spec.ts`) asserting game state headless; CI runs build + tests.
- Phase 0 foundation: repository tree, document templates, state schemas, provider routing table, CI skeleton.
