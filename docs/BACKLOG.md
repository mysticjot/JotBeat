# Product Backlog

> Owned by Director + Producer. Backlog items are user stories with acceptance criteria;
> items roll up into milestones, milestones into phases (roadmap §1.4).

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
