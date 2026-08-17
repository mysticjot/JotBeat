# Product Backlog

> Owned by Director + Producer. Backlog items are user stories with acceptance criteria;
> items roll up into milestones, milestones into phases (roadmap §1.4).
>
> Terminology (Creative Director ruling): SALTBOUND is in vertical-slice construction.
> Current work items are **build tasks** against `docs/COMMERCIAL_BASELINE.md`.
> "Patch" is reserved for post-ship fixes only.

## Item format

```markdown
### BL-NNN: <title>
As a <player/system>, I want <capability> so that <value>.
ACs: AC-NNN, AC-NNN
Role: coder
Depends on: BL-NNN | none
Milestone: <milestone>
Priority: P0–P4
Status: BACKLOG | IN_DEVELOPMENT | CODE_REVIEW | QA | VERIFIED | KICKED_BACK | CERT_REVIEW | DONE | BLOCKED_HUMAN
```

---

## Milestone: Vertical Slice (Phase 3)

The full playable greybox dungeon: title → play → victory/game-over, all 10
acceptance criteria MET, driven through the orchestrator loop with real model
calls (HANDOFF-PHASE3 §3). Greybox only — no generated art, no audio.

AC-001 and AC-002 already exist from the Phase 1 scaffold: the Coder's job on
BL-001/BL-002 is to verify the existing behavior satisfies the AC and confirm
the Playwright test exists — do NOT rewrite working code.

### BL-001: Player Movement
As a player, I want to move the thief with the arrow keys so that I can explore the vault.
ACs: AC-001
Role: coder
Depends on: none
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-002: Wall Collision
As a player, I want walls to block movement so that the dungeon has shape.
ACs: AC-002
Role: coder
Depends on: none
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-003: Key Pickup + Inventory
As a player, I want to pick up the seal-key so that it is added to my inventory.
ACs: AC-003
Role: coder
Depends on: BL-001
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-004: Locked Door Blocks Without Key
As a player, I want the locked door to block me when I have no key so that the key matters.
ACs: AC-004
Role: coder
Depends on: BL-002, BL-003
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-005: Key Unlocks Door, Key Consumed
As a player, I want the key to unlock the door and be consumed so that progress is permanent.
ACs: AC-005
Role: coder
Depends on: BL-004
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-006: Exit Triggers Victory Scene
As a player, I want reaching the exit to trigger the Victory scene so that the run has an ending.
ACs: AC-006
Role: coder
Depends on: BL-005
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-007: Game Over State
As a player, I want a Game Over state so that failure is a real outcome.
ACs: AC-007
Role: coder
Depends on: BL-001
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-008: Pause Screen
As a player, I want to pause the game so that I can step away mid-run.
ACs: AC-008
Role: coder
Depends on: BL-001
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-009: HUD Key Count
As a player, I want the HUD to show my key count so that I always know my inventory.
ACs: AC-009
Role: coder
Depends on: BL-003
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

### BL-010: Title Screen With Start Flow
As a player, I want a title screen that starts the game so that the loop is complete.
ACs: AC-010
Role: coder
Depends on: BL-006, BL-007
Milestone: Vertical Slice
Priority: P1
Status: BACKLOG

## Milestone: Commercial Baseline (vertical-slice construction)

Build tasks against `docs/COMMERCIAL_BASELINE.md` — the gate-blocking checklist
QA runs on every `jotbeat verify`. Statuses tracked in `docs/STUDIO_STATE.md`.

- BT-1: Baseline checklist doc + gate wiring (QA runs it; Auditor blocks certs missing it).
- BT-2: Camera stability under movement — no sub-pixel drift; verified by 10s movement capture.
- BT-3: Animated character sprites — CC0 4-direction walk cycle, idle/walk animation states; no static-tile actors.
- BT-4: Audio coverage — every player action and state change has a CC0 sound; volumes in config.
- BT-5: Asset-quality upgrade — owned by the Phase 5 generated-art pass, not by churning the CC0 set.

## Queued (held pending GAME_DESIGN.md approval)

- **JotBeat Console** (Creative Director deliverable, held by construction hold): extend
  `jotbeat ui` into the studio's visible console — stdlib local server on 127.0.0.1, no new
  paid deps, presentation layer over `state/events.jsonl`, `game/assets/manifest.json`, and
  `reports/cert/`. Sections: **Pipeline** (live role view: current task, model, status from
  events.jsonl), **Gates** (pending approvals with evidence + approve/reject writing the gate
  decision), **Costs** (per-game/per-role ledger vs budget), **Artifacts** (screenshots, cert
  reports, maps, audio browser), **Backlog** (build queue vs COMMERCIAL_BASELINE.md),
  **Settings** tab (existing Keys/Providers/Routing, unchanged). **Stack line on the main
  screen: engine/version, key libs, build tooling** (Creative Director ruling — the stack is
  never inferred from bug reports; source of truth: DECISIONS.md D-0005).

## Proposed (observer candidates — awaiting human approval)
- [ ] PROPOSED: Add a short delay or wait for the physics system to complete its next update cycle before asserting the position after pausing.
- [ ] PROPOSED: Modify the test to check the position in the first unpaused frame rather than immediately after the pause event.
