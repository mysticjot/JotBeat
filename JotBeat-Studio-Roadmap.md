# JotBeat — The Complete Studio Roadmap

**An auditable AI game-production system: it plans, builds, tests, verifies, remembers, and explains every beat of development.**

Version 1.0 — August 2026
Owner: JotBeat (jotbeat.com)
Status: Pre-Production

---

## Table of Contents

1. Vision & Positioning
2. Design Principles
3. Studio Roster (Roles)
4. Repository Architecture
5. Document & State System
6. The Execution Loop
7. Technology Stack (Full Inventory)
8. AI Provider Routing & Model Assignments
9. Token Budget & Cost Model
10. The Kaggle GPU Pipeline
11. Quality System (QA / Cert / Bug Schema)
12. Art & Audio Pipeline
13. Release Engineering
14. Phase 0 — Foundation
15. Phase 1 — Game Scaffold
16. Phase 2 — Orchestrator Core
17. Phase 3 — Vertical Slice Mechanics
18. Phase 4 — QA & Cert Harness
19. Phase 5 — Art & Audio Pass
20. Phase 6 — Release Candidate
21. Phase 7 — Post-Launch (Deferred)
22. Risk Register
23. License Matrix
24. Glossary (Professional Terminology)
25. Definition of Done — Master Checklist

---

## 1. Vision & Positioning

### 1.1 What JotBeat is

JotBeat is an AI game-production control system. Not "type a prompt, get a game" — a studio where **agents create, but the system verifies**.

> Write a pitch. JotBeat turns it into a milestone plan, builds each backlog item, proves it against acceptance criteria, and keeps the whole production ownable.

### 1.2 The market gap it occupies

The commercial landscape (Chatforce, Rosebud, FRVR/Upit, Summer Engine, SEELE, Lovable, Base44) has solved **prompt → playable prototype**. It has not solved **prompt → trustworthy, balanced, shippable game**. Recurring gaps across all competitors:

- Creation without proof (no adversarial acceptance auditing)
- Iteration without regression safety (fixes break old features silently)
- Agents without durable memory (context resets between sessions)
- Art without enforceable style constraints (generic-looking output)
- Balance without measurable governance
- Publishing without a controlled release pipeline
- AI usage without cost predictability (credit anxiety)

### 1.3 Competitive category

```text
Prompt-to-game toys      (Rosebud / Chatforce / Upit)   — fast, weak verification
General AI app builders  (Lovable / Base44 / Replit)    — strong workflow, weak game semantics
Professional QA tooling  (modl.ai / Razer / GameDriver) — strong verification, no creation

JotBeat = the missing middle: AI game production control system
```

### 1.4 Naming & vocabulary policy

- **JotBeat** is the product and studio name (jotbeat.com). That is the only coined word in this document.
- All process vocabulary is standard industry terminology: pitch, milestone, sprint, backlog item, user story, acceptance criteria, build verification, certification, release candidate.
- The unit of work is a **backlog item** (user story with acceptance criteria); backlog items roll up into **milestones**; milestones roll up into **phases** (prototype → vertical slice → alpha → release candidate).
- If "beat" appears in user-facing marketing, it references the genuine industry term (story beat / gameplay beat) — it is never used as internal process vocabulary.

---

## 2. Design Principles

These are enforceable rules, not aspirations.

1. **No agent-to-agent conversation.** Agents emit structured artifacts; the orchestrator routes them. Eliminates the 40–60% token waste typical of multi-agent chatter.
2. **Deterministic-first.** Every check that can be code is code. AI is spent only on judgment and generation. Deterministic checks are free and local.
3. **Creation is not completion.** No backlog item is complete because an agent says so. An item is complete because evidence satisfies its acceptance criteria.
4. **The Auditor is adversarial and independent.** The system that builds never grades its own work. Console-cert model (Sony TRC / Xbox XR / Nintendo Lotcheck).
5. **The repo is the product.** Local-first, git-backed, human-readable, runnable without JotBeat. Export is not an escape hatch; it is the default state.
6. **Context budgets enforced in code.** Per-role token caps in `models.py`. The Producer rejects calls that exceed them.
7. **Escalation has a ceiling.** Cheap model → 2 verified failures → frontier model with shrunk context → 2 more failures → human ticket. Runaway cost is structurally impossible.
8. **Rate limits never idle the pipeline.** On a 429, the scheduler reorders the queue and runs CPU work (build, regression, validation) in the window.
9. **Batch GPU work.** Art and audio accumulate into one weekly Kaggle session.
10. **Everything is ledgered.** Every call logged with provider, tokens, task ID. Cost per game is a measured fact, not an estimate.

---

## 3. Studio Roster (Roles)

Professional discipline names; internal system names in parentheses.

| Discipline | System name | Owns | Does NOT own |
|---|---|---|---|
| **Game Director** (`director`) | Creative vision, pillars, scope, milestone plan, clarification questions | Marking work complete |
| **Producer** (`producer`) | Schedule, backlog, state files, budget ledger, caps enforcement | Creative decisions |
| **Gameplay Programmer** (`coder`) | Phaser scenes, mechanics, entities, input, collision, UI screens | Self-verification |
| **Game/Systems Designer** (`designer`) | Tuning data, difficulty curves, balance flags, pacing | Final "fun" judgment (human's) |
| **Level Designer** (`level`) | LDtk maps, encounter layouts, procedural-gen parameters | Engine code |
| **Artist / Technical Artist** (`artist`) | Art Bible enforcement, asset manifests, prompt craft, palette | Unvalidated output |
| **Audio Designer** (`sound`) | Event-to-sound map, tracks, SFX, loudness metadata | Implementation wiring |
| **QA Engineer / SDET** (`qa`) | Test plan execution, Playwright suites, bug reports | Fixing bugs |
| **Certification / Compliance** (`auditor`) | MET / FAILED / UNVERIFIED / SKIPPED verdicts with evidence | Building anything |
| **Release Engineer** (`publisher`) | Builds, packaging, itch.io upload, versioning, preview deploys | Scope changes |
| **Narrative Designer** (`writer`, later) | World bible, dialogue, item descriptions | Mechanics |

**Builder** is not an AI role — it is deterministic tooling (install, compile, lint, bundle, asset validation).

---

## 4. Repository Architecture

```text
jotbeat/
├─ game/                        # Phaser 4 + TypeScript game project
│  ├─ src/
│  │  ├─ scenes/                # Boot, Title, Game, Victory, GameOver, Pause
│  │  ├─ entities/              # Player, Key, Door, Exit
│  │  ├─ systems/               # input, collision, inventory
│  │  └─ debug.ts               # window.__game.state hook (QA interface)
│  ├─ assets/
│  │  ├─ sprites/  ├─ tiles/  ├─ audio/  └─ manifest.json
│  ├─ maps/                     # LDtk project + exports
│  └─ tests/                    # Playwright + Vitest suites
│
├─ studio/                      # The orchestration system (Python)
│  ├─ cli.py                    # jotbeat init|brief|plan|run-next|verify|report
│  ├─ orchestrator.py           # LangGraph state machine
│  ├─ state.py                  # load/save project state
│  ├─ models.py                 # model-agnostic adapter + provider chain + token caps
│  ├─ ledger.py                 # token/cost accounting into events.jsonl
│  ├─ providers.json            # routing table: tiers, prices, cache flags, ceilings
│  ├─ roles/
│  │  ├─ director.py  ├─ coder.py    ├─ designer.py
│  │  ├─ artist.py    ├─ sound.py    ├─ qa.py
│  │  ├─ auditor.py   └─ publisher.py
│  ├─ tools/
│  │  ├─ files.py  ├─ git.py  ├─ shell.py  ├─ browser.py  └─ kaggle.py
│  └─ prompts/                  # role system prompts (stable prefixes for caching)
│
├─ docs/                        # The codified context (agent memory)
│  ├─ GDD.md                    # Game Design Document
│  ├─ TEST_PLAN.md              # acceptance criteria + test mapping
│  ├─ ART_BIBLE.md              # art direction + asset specification
│  ├─ NARRATIVE_BIBLE.md        # world/lore/voice
│  ├─ BACKLOG.md                # product backlog
│  ├─ ADR.md                    # architecture decision records
│  ├─ BUDGET.md                 # token caps, escalation ceilings, cost model
│  └─ CHANGELOG.md
│
├─ state/
│  ├─ project-state.json        # current truth
│  ├─ task-queue.json           # sprint backlog / task board
│  ├─ balance-model.json        # tuning data
│  └─ events.jsonl              # append-only ledger (telemetry + cost)
│
├─ artifacts/
│  ├─ screenshots/  ├─ audio/  ├─ builds/  └─ traces/
│
└─ reports/
   ├─ bvt/                      # build verification results
   ├─ regression/               # automated regression runs
   ├─ cert/                     # compliance/acceptance audits
   └─ triage/                   # bug reports with severity
```

---

## 5. Document & State System

The agents have no memory. The files remember.

| File | Industry name | Consumed by |
|---|---|---|
| `GDD.md` | Game Design Document | Director, Coder, Auditor |
| `TEST_PLAN.md` | Acceptance Criteria / Test Plan | QA, Auditor |
| `ART_BIBLE.md` | Art Direction Document / Style Guide | Artist, validators |
| `NARRATIVE_BIBLE.md` | World Bible | Writer, Artist, Sound |
| `BACKLOG.md` | Product Backlog | Director, Producer |
| `ADR.md` | Architecture Decision Records | Coder, Auditor |
| `BUDGET.md` | (JotBeat-specific) cost governance | Producer, models.py |
| `project-state.json` | Current milestone state | All roles |
| `task-queue.json` | Sprint Backlog / Task Board | Orchestrator |
| `balance-model.json` | Tuning Data / Economy Sheet | Designer, Coder |
| `events.jsonl` | Telemetry log / Changelog / Ledger | Producer, Auditor |
| `STATE_SUMMARY.md` (generated) | Rolling digest (~2k tokens) | All roles (replaces raw event reads) |

**Context-slicing rule:** each role receives only its relevant slice. Coder: repo map + target files + task + ACs. Artist: Art Bible + manifest + task. Auditor: AC + evidence digests (never the Coder's self-assessment).

### Acceptance criterion format (TEST_PLAN.md)

```markdown
## AC-004: Key Unlocks Door
Given the player has collected the key,
when the player touches the locked door,
then the door opens and the key is consumed.

Verification: scripted browser test
Evidence: inventory count decreases; door state becomes `open`
Test: game/tests/ac-004-door.spec.ts
Status: MET | FAILED | UNVERIFIED | SKIPPED
```

---

## 6. The Execution Loop

```text
JOT → BEAT PLAN → TASK QUEUE → ROLE EXECUTION → ARTIFACTS
    → BUILD VERIFICATION → SCRIPTED QA → SPEC AUDIT
    → PASS / PATCH / ESCALATE → COMMIT → REPORT
```

```python
def run_next_task():
    state = load_project_state()
    task = get_next_ready_task()
    mark_running(task)

    result = execute_role(task, state)          # role-routed model call
    save_artifacts(result)

    build_result = builder.run()                # deterministic, $0
    qa_result = qa.run(task.acceptance_ids)     # Playwright, $0 infra

    audit = auditor.audit(                      # adversarial, independent
        task=task, build=build_result, qa=qa_result,
        acceptance=load_acceptance(task.acceptance_ids),
    )

    if audit.status == "MET":
        mark_complete(task); commit_changes(task)
    elif audit.status == "FAILED":
        create_patch_task(task, audit)          # bounded by escalation ceiling
    else:
        mark_unverified(task, audit)            # human ticket
```

**Workflow states (bug-tracker language):**

```text
BACKLOG → IN SPRINT → IN DEVELOPMENT → CODE REVIEW → QA
→ VERIFIED / KICKED BACK → CERT REVIEW → DONE
```

---

## 7. Technology Stack (Full Inventory)

### 7.1 Engine & game code

| Need | Pick | License | Owner role |
|---|---|---|---|
| Engine | **Phaser 4 + TypeScript** (`npm create @phaserjs/game@latest`) | MIT | Coder |
| Bundler | **Vite** (ships with template) | MIT | Release Eng |
| Level editor | **LDtk** (primary) / **Tiled** (fallback) | MIT / GPL | Level Designer |
| Pathfinding | **EasyStar.js** | MIT | Coder |
| Procedural gen (later) | **rot.js** | MIT (BSD) | Level Designer |
| Physics | Phaser Arcade / Matter.js (bundled) | MIT | Coder |
| Skeletal animation | **DragonBones** (Phaser plugin) | Free/OSS | Artist |
| UI animation (DOM layer) | **GSAP / Anime.js** | Mixed/Free | Artist |

### 7.2 Art pipeline

| Need | Pick | License |
|---|---|---|
| Image generation | **ComfyUI** (Kaggle-hosted, batch mode) | GPL runtime |
| Pixel-art models | SDXL/SD1.5 pixel LoRAs inside ComfyUI | per-model |
| Sprite editing | **LibreSprite** (Aseprite fork) / **Piskel** | GPL / Apache |
| Image work | **Krita / GIMP** | GPL |
| Atlas packing | **Free Texture Packer** | MIT |
| Palette extraction | **Color Thief** (from concept art → Art Bible lock) | MIT |
| Compression | **Squoosh / TinyPNG** | Free |
| Validation | Custom **Pillow** validators (dimensions, palette drift, alpha, tileability) | HPND |

### 7.3 Audio pipeline

| Need | Pick | License |
|---|---|---|
| Music generation | **ACE-Step** (1.5 XL Turbo on Kaggle T4) | Apache 2.0 — shippable |
| SFX generation | **Stable Audio Open** | Free commercial <$1M rev |
| Procedural SFX (placeholders) | **jsfxr / sfxr / ChipTone** | Free/OSS |
| Generative music (placeholders) | **Tone.js** | MIT |
| In-game playback | Phaser sound manager / **Howler.js** | MIT |
| Editing/mastering | **FFmpeg** (EBU R128 loudness) / **Audacity** | LGPL / GPL |
| Waveform QA viz | **Wavesurfer.js** | BSD |
| ⚠ Prototype-only | MusicGen (weights CC-BY-NC) | Never ship its output |

### 7.4 QA & testing

| Need | Pick | License |
|---|---|---|
| Browser automation | **Playwright** (fake input + state assertions + screenshots) | Apache 2.0 |
| Unit tests | **Vitest** | MIT |
| Visual regression | Playwright `toHaveScreenshot()` / **BackstopJS** | MIT |
| Pixel diffing | **pixelmatch** | MIT |
| Viewport matrix | Responsiveness checkers (awesome-webdev list) | Free |
| Load performance | **PageSpeed / GTmetrix** in BVT | Free |

### 7.5 Orchestration & infrastructure

| Need | Pick | License/Cost |
|---|---|---|
| Agent state machine | **LangGraph** | MIT |
| Local model runtime (optional) | **Ollama** | MIT |
| Patch application | **Aider** (optional helper) | Apache 2.0 |
| State store | JSON + **SQLite** | — |
| CI / BVT runner | **GitHub Actions** | Free |
| Always-on host (optional) | **Oracle Cloud Always Free** ARM VM (4 core/24GB) | $0 |
| Versioning | **git** + **git-lfs** (binary assets) | — |
| Preview hosting | **GitHub Pages / Cloudflare Pages** | $0 |
| Artifact storage | **Cloudflare R2** (10GB free) | $0 |
| itch.io upload | **butler** (official CLI) | Free |
| Desktop wrap (later) | **Tauri** / Electron | MIT |
| Mobile wrap (later) | **Capacitor** | MIT |
| Dashboard (Phase 7) | React + Tailwind + shadcn/ui, Lucide/Tabler icons, Google Fonts | OSS |

---

## 8. AI Provider Routing & Model Assignments

One specialist per job. No DeepSeek stacking. All providers are API-key signups behind a git-ignored `.env`; `models.py` activates only providers whose keys exist.

### 8.1 Routing table (providers.json)

| Role | Model | Why this one | $/1M in | $/1M out | Cached in |
|---|---|---|---|---|---|
| Director | **Gemini** (free tier) | 1M context for whole-GDD reads | $0 | $0 | — |
| **Coder** | **Qwen3-Coder-Next** | Purpose-built coder; 92.7% tool-format following = parseable patches, fewer format retries | $0.11 | $0.80 | — |
| QA (test authoring) | **DeepSeek V4 Flash** | Test code is code; 79% SWE-bench at $0.28 output; prefix cache eats context | $0.14 | $0.28 | $0.003 |
| Auditor (while subscribed) | **Kimi K2.6** | Long-document review; sunk subscription = $0 marginal cash | $0.95 | $4.00 | $0.19 |
| Auditor (post-downgrade) | **GLM-4.7** | Open-weights quality tier for review | $0.30 | $1.18 | $0.059 |
| Escalation | **GLM-4.7** / DeepSeek V4 Pro | Hard bugs, shrunk context only | $0.30–0.44 | $0.87–1.18 | — |
| Vision observer | **MiniMax M3** | Native multimodal, cheapest frontier-ish | $0.30 | $1.20 | — |
| Triage | **Qwen3.5 Flash** | Cheapest input on market; classification needs no brains | $0.03 | $0.30 | — |
| Art/Sound manifests | **Groq** (free tier) | JSON manifests are trivial | $0 | $0 | — |
| Free-chain backbone | Groq → Cerebras → Gemini → GitHub Models → Mistral → OpenRouter | Development iteration at $0 | $0 | $0 | — |

### 8.2 Key sources

| Provider | Key location |
|---|---|
| DeepSeek | platform.deepseek.com |
| Qwen | Alibaba Model Studio / DashScope — **international endpoint** |
| Kimi | platform.moonshot.ai |
| GLM | z.ai (international) |
| MiniMax | platform.minimax.io |
| Gemini | Google AI Studio |
| Groq / Cerebras / Mistral | respective consoles, free tiers |
| OpenRouter | openrouter.ai (optional master router; $10 top-up raises free limits) |
| GitHub Models | GitHub PAT |
| fal.ai (art overflow) | fal.ai dashboard |

### 8.3 Non-key components

Kaggle/Colab (account-driven notebooks, not REST keys) · jsfxr/Tone.js/Howler.js (libraries) · Playwright/Vitest/LDtk/Vite/butler (local tools) · Oracle/Actions/Pages (platform accounts).

### 8.4 Security rules

- Keys live in `.env`, never in the repo, never in prompts, never in `events.jsonl`
- The ledger logs provider names, never credentials
- Free tiers train on prompts — fine for JotBeat's own game code; nothing sensitive goes through Tier 0
- Check output-ownership terms per provider before commercial release

---

## 9. Token Budget & Cost Model

### 9.1 What one finished game costs (measured model)

| Role | Calls/game | In/call | Out/call | Game total |
|---|---|---|---|---|
| Coder | 85 | 30k | 4.5k | 2.93M |
| Auditor | 75 | 17k | 1.5k | 1.39M |
| QA | 30 | 13k | 2.5k | 0.47M |
| Director | 20 | 10k | 2k | 0.24M |
| Art/Sound | 10 | 3k | 1k | 0.04M |
| **Total (unrationed)** | **220** | | | **~5.1M tokens, 88% input** |

With token rationing (§9.3): **~2.5M tokens/game**.

### 9.2 Single-game invoice (capability-matched routing)

| Role | Model | Tokens (in/out) | Cost |
|---|---|---|---|
| Director | Gemini free | 160k / 40k | $0.00 |
| Coder | Qwen3-Coder-Next | 1.19M / 128k | $0.23 |
| QA | DeepSeek V4 Flash (70% cached) | 210k / 75k | $0.03 |
| Auditor | Kimi K2.6 (sunk sub) → GLM-4.7 later | 520k / 98k | $0.00 cash now / $0.18 later |
| Escalation | GLM-4.7 | 80k / 15k | $0.04 |
| Vision observer | MiniMax M3 | 100k / 12k | $0.04 |
| Triage | Qwen3.5 Flash | 100k / 25k | $0.01 |
| Manifests | Groq free | 30k / 10k | $0.00 |

```text
TODAY (Kimi subscribed):        $0.36 cash per finished game
AFTER KIMI DOWNGRADE:           $0.54 per finished game
Art (Kaggle free GPU):          $0.00     (paid fallback: ~$0.72 via fal.ai)
Audio (jsfxr/Kaggle):           $0.00
Hosting / CI / QA infra:        $0.00
ALL-PAID WORST CASE:            ~$1.26 per game
FREE-CHAIN BEST CASE:           $0.00 per game (development pace)
```

### 9.3 Token-rationing rules (BUDGET.md enforces these)

1. **Diff-only output contract** — Coder emits unified diffs, never whole files (output ~4.5k → ~1.5k/call)
2. **Repo map, not repo** — precomputed index (~4k tokens) + max 2 target files per call
3. **Log tails** — error context = last 50 lines; retries stop snowballing
4. **Prefix caching** — identical role prompts/system context across calls; DeepSeek cache rate $0.003/M
5. **Small model for triage, big model for surgery** — failure classification is a 2k-token Qwen3.5 Flash call
6. **Auditor evidence digests** — structured summaries, not raw Playwright traces
7. **State summarization** — `STATE_SUMMARY.md` (~2k tokens) replaces raw `events.jsonl` reads

### 9.4 Supply math (why it's sustainable)

```text
Free chain:   ~2,500–3,500 calls/day, ~8–15M tokens/day
One game:     ~220 calls, ~2.5–5M tokens
GPU:          ~1 hour/game vs 30 free GPU-hours/week
Sustained:    1–2 games/day free; ~30 games/month ≈ 152M tokens
              (Mistral's 1B free tokens/month alone covers 6x)
```

### 9.5 The ledger schema (events.jsonl)

```json
{"ts": "2026-08-15T...", "task": "AC-004-door", "role": "coder",
 "provider": "dashscope", "model": "qwen3-coder-next",
 "tokens_in": 13240, "tokens_out": 1180, "cached_in": 9268,
 "retry": 2, "escalated": false, "cost_usd": 0.0024}
```

- Producer computes **cost per verified task** and **cost per game** after every run
- Routing table re-ranked monthly from real ledger data, not pricing pages
- If actual tokens/game drifts above ~3M, caps tighten automatically

### 9.6 Caveats

- Vendor benchmarks are upper bounds; ordering is trustworthy, exact percentages are not
- DeepSeek has warned API pricing may rise — provider chain makes it a config change
- Cheapest per token ≠ cheapest per finished task (retries multiply input)

---

## 10. The Kaggle GPU Pipeline

### 10.1 What Kaggle provides (verified)

- **30 GPU-hours/week, guaranteed** (fixed published quota, resets weekly — unlike Colab's fluctuating 15–30h)
- Hardware: **T4 (16GB) or P100 (16GB)**; 2×T4 (32GB) option
- Sessions up to ~9–12 hours; **20GB persistent storage**; no credit card
- **Preinstalled:** PyTorch, diffusers, ComfyUI — no pip-install tax
- Ready notebooks exist for ComfyUI (GUI via LocalTunnel) and **ACE-Step 1.5 XL Turbo tuned for Kaggle T4** (commercial-friendly license)

### 10.2 The automation gotcha

Kaggle is **not a live server**. No SSH into running GPU sessions. What is automatable: the **Kaggle API `kernels push`** — submit a script/notebook, it runs on GPU, poll + download outputs. Therefore the integration is a **batch job pattern, not a daemon**.

### 10.3 The weekly batch flow

```text
1. Director accumulates art/audio tasks all week (batching rule §2.9)
2. Artist renders manifest: [{asset, prompt, size, palette_lock, seed}, ...]
3. CLI: kaggle kernels push → ComfyUI script runs batch on T4
   (ACE-Step music + Stable Audio Open SFX run in the SAME session)
4. Outputs land as Kaggle dataset → downloaded into game/assets/
5. Pillow validators run: dimensions, palette drift, alpha, tileability
6. Passes committed; failures logged; manifest updated with provenance
   (model + license per asset)
```

### 10.4 Capacity

```text
60–100 sprites (SDXL, ~20–30s each on T4):   ~30–50 min
3 music tracks (ACE-Step):                   ~5–10 min
SFX batch:                                   ~10 min
─────────────────────────────────────────────────────────
One game's GPU need:  ~1 hour  |  Weekly free supply: 30 hours
Fallback if quota exhausted or batch fails: fal.ai @ ~$0.012/image
```

---

## 11. Quality System

### 11.1 The layered model

```text
LAYER 1 — Deterministic (free, local, instant)
  Build verification (BVT): install, compile, lint, bundle, asset validation
  Unit tests: Vitest on game logic
  Scripted E2E: Playwright fake input + window.__game.state assertions

LAYER 2 — AI observer (cheap, second opinion)
  MiniMax M3 reviews screenshots/traces, classifies failures,
  proposes new edge-case scenarios

LAYER 3 — Cert audit (adversarial, independent)
  Auditor issues MET / FAILED / UNVERIFIED / SKIPPED per AC
  with evidence links; never sees the Coder's self-assessment
```

**Rule:** pure autonomous free-roaming playtesting is not the source of truth. Scripted scenarios with game-state assertions are. (Validated by production experience: fake input layer + scripted scenarios beat end-to-end autonomy on speed and stability.)

### 11.2 Bug report schema (industry format)

```text
ID: JB-0142
Title: Player clips through locked door at (12,7)
Severity: Blocker | Critical | Major | Minor | Trivial
Priority: P0–P4
Build: #14
Repro: 3/3 — 1. Start level 2  2. Hold Right against door  3. ...
Expected: door blocks without key
Actual: player passes through on frame-perfect input
Environment: Chromium 128 headless, 1280x720
Attachments: screenshots/jb-0142.png, traces/jb-0142.zip
Status: New → Triaged → In Progress → Fixed → Verified → Closed
```

### 11.3 Regression rule

Every accepted AC joins the regression suite. Every new backlog item reruns all previous ACs. A change cannot be DONE unless the full suite passes. This is the structural answer to the industry's #1 complaint: "fixes that break old features."

---

## 12. Art & Audio Pipeline

### 12.1 The Art Bible contract (ART_BIBLE.md)

Style lock is machine-checkable, not a mood board:

```json
{
  "style_lock": "16-bit top-down dungeon",
  "tile_size": 32,
  "palette": ["#1b1026", "#3b2d4d", "#8f6b3a"],
  "lighting": "soft top-left",
  "outline": "1px dark",
  "camera": "top-down",
  "must_tile": true,
  "transparent_background": false
}
```

- **Color Thief** extracts the locked palette from approved concept art
- Pillow validators enforce every field on every generated asset
- Failure = asset rejected before it reaches the repo

### 12.2 Placeholder-first rule

Art and Sound start as stub roles emitting manifests + greybox/proxy assets + jsfxr scratch audio. The pipeline proves itself on placeholders before touching the GPU. Real assets swap in behind the same manifest interface.

### 12.3 Audio event map

```json
{"jump": "sfx/jump.wav", "pickup_key": "sfx/key.wav",
 "door_unlock": "sfx/door.wav", "victory": "music/victory.ogg",
 "loudness_target": "-16 LUFS", "format": "ogg + mp3 fallback"}
```

FFmpeg normalizes loudness (EBU R128) on every track in CI.

---

## 13. Release Engineering

```text
npm run build → dist/ → BVT gate → version bump (semver)
→ ZIP package → butler push (itch.io, draft channel)
→ GitHub Pages / Cloudflare Pages preview link
→ Release report: changelog + cert summary + known issues + ledger cost
```

- Release flow: **Release Candidate → cert pass → Gold → ship**
- Desktop (Tauri/Electron) and mobile (Capacitor) are post-launch tracks, not MVP
- The game builds and runs without JotBeat — the repo is the product

---

## 14. Phase 0 — Foundation  ·  ~2 days

### 14.1 Repository

- [ ] Create repo: `game/`, `studio/`, `docs/`, `state/`, `artifacts/`, `reports/`
- [ ] `git init`, GitHub remote, branch protection on main
- [ ] `.gitignore`: `.env`, `node_modules/`, `dist/`, Kaggle outputs
- [ ] `.env` scaffold with all provider key slots (empty)
- [ ] git-lfs configured for `artifacts/` and binary assets

### 14.2 Documents (the codified context)

- [ ] `docs/GDD.md` — template with pillars, scope, non-goals sections
- [ ] `docs/TEST_PLAN.md` — AC format + status fields
- [ ] `docs/ART_BIBLE.md` — style-lock JSON schema section
- [ ] `docs/NARRATIVE_BIBLE.md` — world/voice template
- [ ] `docs/BACKLOG.md` — prioritized backlog format
- [ ] `docs/ADR.md` — decision record format
- [ ] `docs/BUDGET.md` — token caps, escalation ceilings, cost model (§9)
- [ ] `docs/CHANGELOG.md`

### 14.3 State & config

- [ ] `state/project-state.json` schema
- [ ] `state/task-queue.json` schema
- [ ] `state/events.jsonl` ledger schema (§9.5)
- [ ] `studio/providers.json` routing table (§8.1)
- [ ] GitHub Actions: empty-build CI green

**Gate:** `jotbeat init` generates this tree from a template; CI passes on an empty game.

---

## 15. Phase 1 — Game Scaffold  ·  ~2–3 days

### 15.1 Engine

- [ ] `npm create @phaserjs/game@latest` → Phaser 4 + TypeScript + Vite
- [ ] Boot → Title scene renders (black screen + text acceptable)
- [ ] LDtk project created; one greybox dungeon map loads
- [ ] Tile collision active on walls
- [ ] Player placeholder (colored rect/programmer art) moves with arrow keys
- [ ] Camera follows player

### 15.2 QA interface (build it now, not later)

- [ ] `debug.ts` exposes `window.__game.state` (scene, position, inventory, door states)
- [ ] Deterministic RNG seed hook
- [ ] Playwright installed; smoke test: game loads headless, state readable

### 15.3 Build

- [ ] `npm run build` → `dist/` green locally
- [ ] GitHub Actions BVT runs the same build on every push
- [ ] Preview deploy to GitHub Pages / Cloudflare Pages

**Gate:** BVT green in CI; Playwright can read game state from a headless run.

---

## 16. Phase 2 — Orchestrator Core  ·  ~3–4 days

### 16.1 State machine

- [ ] LangGraph workflow: BACKLOG → IN DEV → CODE REVIEW → QA → CERT → DONE
- [ ] Task lifecycle: claim, run, artifact-save, verify, complete/kickback
- [ ] Dependency resolution (door task requires collision task)

### 16.2 Model adapter (`models.py`)

- [ ] Provider chain: free tier → DeepSeek → specialists, fallthrough on 429
- [ ] Only providers with keys in `.env` activate
- [ ] Per-role token caps enforced (BUDGET.md values)
- [ ] Diff-only output contract for Coder
- [ ] Prefix caching enabled where supported
- [ ] Escalation ceiling: 2 failures → frontier (shrunk context) → 2 more → human ticket

### 16.3 Ledger

- [ ] Every call logged to `events.jsonl` (§9.5 schema)
- [ ] `jotbeat report` shows tokens/cost per task, per role, per game
- [ ] `STATE_SUMMARY.md` generator (rolling ~2k-token digest)

### 16.4 CLI

- [ ] `jotbeat brief "..."` → GDD draft + milestone plan
- [ ] `jotbeat plan` / `run-next` / `verify` / `report`
- [ ] Rate-limit-aware scheduler (reorders queue, fills windows with CPU work)

**Gate:** a stub task flows through the full loop and lands in the ledger with a cost attached.

---

## 17. Phase 3 — Vertical Slice Mechanics  ·  ~1 week

### 17.1 Planning

- [ ] Director converts the dungeon pitch → GDD + milestone plan
- [ ] TEST_PLAN.md written: AC-001…AC-010 with verification methods
- [ ] Backlog prioritized; dependencies mapped

### 17.2 Mechanics (Coder: Qwen3-Coder-Next)

- [ ] Player movement (arrow keys) — AC-001
- [ ] Wall collision — AC-002
- [ ] Key pickup + inventory — AC-003
- [ ] Locked door blocks without key — AC-004
- [ ] Key unlocks door, key consumed — AC-005
- [ ] Exit triggers Victory scene — AC-006
- [ ] Game Over state — AC-007
- [ ] Pause screen — AC-008
- [ ] HUD (key count) — AC-009
- [ ] Title screen with start flow — AC-010

### 17.3 Screens (greybox)

- [ ] Title / Game Over / Victory / Pause — DOM overlay (GSAP) or Phaser scenes
- [ ] Triage loop live: build failure → Qwen3.5 Flash classification → fix

**Gate:** all 10 ACs implemented; BVT green; playable start-to-victory in placeholder art.

---

## 18. Phase 4 — QA & Cert Harness  ·  ~1 week

### 18.1 Scripted QA

- [ ] Playwright suite: one test per AC, mapped by ID (`ac-004-door.spec.ts`)
- [ ] Fake input layer drives the player deterministically
- [ ] Assertions against `window.__game.state`
- [ ] Screenshot + console capture per test
- [ ] Viewport matrix (desktop/tablet/mobile sizes)

### 18.2 Regression

- [ ] Full AC suite reruns on every merged change
- [ ] Visual regression baseline (title, gameplay, victory screenshots)

### 18.3 AI observer

- [ ] MiniMax M3 reviews failure screenshots
- [ ] Failure classification feeds triage
- [ ] Edge-case scenario proposals → new test candidates

### 18.4 Cert audit

- [ ] Auditor (Kimi now; GLM-4.7 post-downgrade) issues verdicts per AC
- [ ] Evidence digests, not raw traces
- [ ] `reports/cert/` output: verdict + evidence links + patch instructions
- [ ] Adversarial test: deliberately break the door; cert must catch it
- [ ] Bug schema live (§11.2) with severity ladder

**Gate:** vertical slice passes cert with readable audit report; planted bug gets kicked back.

---

## 19. Phase 5 — Art & Audio Pass  ·  ~1 week

### 19.1 Art Bible lock

- [ ] Concept art approved; Color Thief extracts locked palette
- [ ] ART_BIBLE.md finalized (tile size, light, outline, palette)
- [ ] Asset validators enforcing every field

### 19.2 Kaggle batch

- [ ] `studio/tools/kaggle.py`: kernels push + output download
- [ ] ComfyUI batch: player, key, door, tiles, exit, UI art
- [ ] ACE-Step tracks: main theme, victory sting
- [ ] Stable Audio Open SFX batch (or jsfxr finals if chiptune fits the bible)
- [ ] Provenance recorded per asset (model + license)

### 19.3 Integration

- [ ] Free Texture Packer atlases; Phaser loads them
- [ ] Audio event map wired (jump, pickup, door, victory)
- [ ] FFmpeg loudness normalization in CI
- [ ] Placeholder assets fully replaced; visual regression baselines updated

**Gate:** the slice looks and sounds like one coherent game; every asset validates against the Art Bible.

---

## 20. Phase 6 — Release Candidate  ·  ~3–4 days

### 20.1 Polish (deterministic, near-zero cost)

- [ ] LibreSprite touch-up pass on flagged sprites
- [ ] WebAIM contrast checks on UI text
- [ ] Full viewport matrix regression
- [ ] PageSpeed check on web build

### 20.2 Ship

- [ ] Version tag (semver), CHANGELOG entry
- [ ] dist/ → ZIP → butler → itch.io draft page
- [ ] Public preview link (GitHub Pages / Cloudflare Pages)
- [ ] itch.io page: description, screenshots, controls

### 20.3 Release report

- [ ] Cert summary (all ACs MET)
- [ ] Known issues list
- [ ] Ledger: actual cost vs. $0.36–0.54 model; routing table re-rank

**Gate:** playable on itch.io; audit trail complete; cost measured.

---

## 21. Phase 7 — Post-Launch (Deferred)

- [ ] Studio dashboard: React + Tailwind + shadcn/ui rendering `project-state.json` + `events.jsonl` (viewer, not source of truth)
- [ ] Telemetry → Live Ops loop (death heatmaps, quit points → Designer)
- [ ] Second genre template (platformer, puzzle)
- [ ] Mobile wrap via Capacitor; desktop via Tauri
- [ ] Narrative Designer role: Ink / Yarn Spinner dialogue trees
- [ ] Commercial polish pipeline for public release

---

## 22. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Free-tier rate limits stall a run | High | Low | Rate-limit-aware scheduler; paid fallthrough ($0.36/game) |
| Free tier terms change / shrink | Medium | Medium | Provider chain; paid backbone absorbs |
| Kaggle quota or batch failure | Medium | Low | fal.ai fallback ~$0.72/game |
| Model price hikes (DeepSeek warned) | Medium | Low | providers.json is config, not code |
| Free tiers train on prompts | Certain | Low | Only JotBeat's own code; verify output terms before commercial release |
| MusicGen-class license trap | Low | High | Provenance manifest; Apache-2.0/licensed models only for shipping |
| Vendor benchmark overstatement | Certain | Medium | Ledger measures cost-per-verified-task on real runs; monthly re-rank |
| AI-generated art looks generic | High | Medium | Art Bible + palette enforcement + human polish pass |
| Scope creep (3D, multiplayer) | High | High | Non-goals in GDD; Phase 7 gate |

---

## 23. License Matrix

| Component | License | Ship? |
|---|---|---|
| Phaser 4, Vite, Playwright, Vitest, LangGraph, LDtk, EasyStar, rot.js, Tone.js, Howler.js, pixelmatch | MIT/Apache | ✅ |
| ComfyUI (runtime), LibreSprite, Krita, GIMP, Audacity | GPL | ✅ (tools, not linked code) |
| ACE-Step | Apache 2.0 | ✅ |
| Stable Audio Open | Free commercial <$1M rev | ✅ |
| DeepSeek V4 | MIT (weights) | ✅ |
| FFmpeg | LGPL/GPL | ✅ (CLI use) |
| MusicGen weights | CC-BY-NC | ❌ prototype only |
| Tiled (if used) | GPL (editor) | ✅ (exports are data) |
| Tauri, Capacitor, Electron | MIT | ✅ |

**Rule:** every generated asset carries provenance (model + license) in `assets/manifest.json`. The Auditor checks it at cert time.

---

## 24. Glossary (Professional Terminology)

| Term | Meaning |
|---|---|
| **Vertical slice** | Small, fully-playable, polished proof of the whole game |
| **Greybox / blockout** | Untextured placeholder level geometry |
| **Programmer art / proxy assets** | Placeholder visuals |
| **Scratch audio / temp track** | Placeholder sound |
| **GDD** | Game Design Document |
| **Art Bible / ADD** | Art Direction Document — the style lock |
| **World/Narrative Bible** | Lore, voice, continuity reference |
| **ADR** | Architecture Decision Record |
| **BVT** | Build Verification Test |
| **Smoke test** | Fast "does it boot" check |
| **Regression suite** | All previously-accepted tests rerun per change |
| **Cert** | Platform-style compliance review (Sony TRC / Xbox XR / Nintendo Lotcheck model) |
| **Kickback** | Work rejected at review, returned with notes |
| **Severity ladder** | Blocker / Critical / Major / Minor / Trivial |
| **RC → Gold** | Release Candidate → Gold Master → ship |
| **Live Ops** | Post-launch telemetry, tuning, content |
| **Tuning data** | Balance numbers (HP, prices, curves) |
| **Asset provenance** | Record of what made each asset and under what license |

---

## 25. Definition of Done — Master Checklist

A game is **DONE** when every box is true:

- [ ] All ACs in TEST_PLAN.md marked **MET** by the Auditor (not the Coder)
- [ ] Full regression suite green on the release build
- [ ] Cert report exists in `reports/cert/` with evidence links
- [ ] Every asset validates against ART_BIBLE.md
- [ ] Every asset has provenance + license in the manifest
- [ ] Audio loudness normalized; event map complete
- [ ] BVT green in CI; PageSpeed acceptable; viewport matrix passed
- [ ] Zero open Blocker/Critical bugs; known Minor issues documented
- [ ] CHANGELOG + version tag + release ZIP + itch.io page live
- [ ] Ledger shows actual cost per game; routing re-ranked
- [ ] The repo builds and plays **without JotBeat running**

---

*JotBeat: the studio where agents create, and the system verifies.*
