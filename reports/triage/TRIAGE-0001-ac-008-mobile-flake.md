# TRIAGE-0001 — AC-008 "player cannot move while paused" position-sampling race (FIXED)

- **id:** TRIAGE-0001
- **severity:** Minor
- **owner role:** qa (harness timing — confirmed, not a game bug)
- **status:** FIXED 2026-08-16 (see resolution)

## repro

1. `cd game && PLAYWRIGHT_BROWSERS_PATH=0 CI=1 npx playwright test` (full
   suite, all three viewport projects).
2. Observe `ac-008-pause-screen.spec.ts:123` — failed once on
   `[chromium-mobile]` in the matrix shakedown, then once on `[chromium]`
   (desktop) in the Phase 4 cert run. Not viewport-specific: load-dependent.

## expected vs actual

- **expected:** green at every viewport.
- **actual:** `expect(pausedPos.x).toBe(startPos.x)` flaked under load;
  passes when the spec runs in isolation.

## root cause (confirmed)

Not a pause bug — the game freezes correctly: `pauseGame()` zeroes velocity
AND pauses the physics world (`game/src/scenes/Game.ts:138-146`), and the
paused `update()` branch re-zeroes velocity every frame.

The race is in the harness: `state.position` is only refreshed on UNPAUSED
`update()` frames. `driveTo()` returns right after `keyboard.up`, but one
post-keyup physics step can still carry residual velocity; if `startPos` is
sampled before that step's position write lands, `startPos` is one frame
stale and the exact-equality assertion compares pre- vs post-drift samples.
The player never moves while paused — the drift happens before pause engages.

## evidence

- spec: `game/tests/ac-008-pause-screen.spec.ts:123` (assertion at :149)
- failure screenshot (desktop recurrence):
  `game/test-results/ac-008-pause-screen-AC-008-4ab05-er-cannot-move-while-paused-chromium/test-failed-1.png`
- **AI observer** (HANDOFF-PHASE4 §2.3, glm-4.6v-flash, 2026-08-16):
  classification `timing`; hypothesis — position sampled before the next
  unpaused frame refreshes it, assertion doesn't account for the drift.
  Observer proposals filed to `docs/BACKLOG.md` Proposed section. The
  observer's classification agreed with the manual root-cause above; its
  "wait for the physics update before asserting" proposal is the shape of
  the applied fix.

## resolution

Harness fix in `game/tests/ac-008-pause-screen.spec.ts` (second test):
after `driveTo`, sample `state.position` until two reads 200ms apart match
exactly (max 10 tries) before recording `startPos`. The assertion itself is
UNCHANGED (exact `toBe`, no retries) — only the reference sample is now
guaranteed settled. Verified: 6/6 green across chromium / chromium-tablet /
chromium-mobile after the fix. Catching test: the AC-008 spec itself.
