# Test Plan — Vertical Slice (Phase 3)

All tests assert against `window.__game.state` — the load-bearing debug hook
(ADR-0001). Contract: `{ scene, position, inventory, doors, seed }` plus the
Phase 3 extensions `oxygen` (seconds remaining) and `paused` (boolean).
Playwright, headless, deterministic seed via `?seed=`. Status values:
MET | FAILED | UNVERIFIED | SKIPPED.

## AC-001: Player Movement
Given the game is running in the Game scene,
when the player presses the arrow keys,
then the player's position changes in the corresponding direction.

Verification: scripted browser test
Evidence: `window.__game.state.position.x` / `.y` change with input
Test: game/tests/ac-001-player-movement.spec.ts
Status: UNVERIFIED

## AC-002: Wall Collision
Given the player is adjacent to a wall tile,
when the player moves in the direction of the wall,
then the player's position remains unchanged and does not clip.

Verification: scripted browser test
Evidence: `window.__game.state.position` is constant after blocked input
Test: game/tests/ac-002-wall-collision.spec.ts
Status: UNVERIFIED

## AC-003: Key Pickup + Inventory
Given the player is in the same room as the key,
when the player overlaps the key entity,
then the key is removed from the map and added to the player's inventory.

Verification: scripted browser test
Evidence: `window.__game.state.inventory.keys` equals 1
Test: game/tests/ac-003-key-pickup.spec.ts
Status: UNVERIFIED

## AC-004: Locked Door Blocks Without Key
Given the player has 0 keys in their inventory,
when the player attempts to walk into the locked door tile,
then the door remains solid and blocks the player.

Verification: scripted browser test
Evidence: `window.__game.state.position` is blocked; `window.__game.state.doors.main` is `locked`
Test: game/tests/ac-004-door-blocked.spec.ts
Status: UNVERIFIED

## AC-005: Key Unlocks Door, Key Consumed
Given the player has 1 key in their inventory,
when the player collides with the locked door,
then the door opens and 1 key is removed from the inventory.

Verification: scripted browser test
Evidence: `window.__game.state.doors.main` becomes `open`; `inventory.keys` decreases to 0
Test: game/tests/ac-005-door-unlocked.spec.ts
Status: UNVERIFIED

## AC-006: Exit Triggers Victory Scene
Given the player has unlocked the door and crossed its threshold,
when the player collides with the exit tile,
then the game transitions to the Victory scene.

Verification: scripted browser test
Evidence: `window.__game.state.scene` equals `Victory`
Test: game/tests/ac-006-exit-victory.spec.ts
Status: UNVERIFIED

## AC-007: Game Over State
Given the player is in the Game scene,
when the oxygen timer reaches 0,
then the game transitions to the Game Over scene.

Verification: scripted browser test
Evidence: `window.__game.state.oxygen` equals 0; `window.__game.state.scene` equals `GameOver`
Test: game/tests/ac-007-game-over.spec.ts
Status: UNVERIFIED

## AC-008: Pause Screen
Given the game is running in the Game scene,
when the player presses the Spacebar,
then the game pauses and the oxygen timer stops.

Verification: scripted browser test
Evidence: `window.__game.state.paused` is true; `oxygen` does not decrease while paused
Test: game/tests/ac-008-pause-screen.spec.ts
Status: UNVERIFIED

## AC-009: HUD Key Count
Given the player's inventory updates,
when the HUD renders,
then the key count element matches the player's actual key inventory.

Verification: scripted browser test
Evidence: HUD text matches `window.__game.state.inventory.keys`
Test: game/tests/ac-009-hud-key-count.spec.ts
Status: UNVERIFIED

## AC-010: Title Screen With Start Flow
Given the game is freshly loaded,
when the player presses Enter on the Title scene,
then the game transitions to the Game scene with a reset state.

Verification: scripted browser test
Evidence: initial `scene` is `Title`; becomes `Game` on Enter; `position`/`inventory` reset
Test: game/tests/ac-010-title-start.spec.ts
Status: UNVERIFIED
