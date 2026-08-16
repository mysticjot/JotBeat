# JotBeat Project GDD: Sunken Vault (Phase 1)

## Pillars
*   **Tactile Simplicity:** Crisp, grid-aligned 16-bit movement and collision.
*   **Mechanical Clarity:** Zero ambiguity. Keys open doors; exits trigger victory.
*   **System Transparency:** A robust global state hook for easy programmatic validation.

## Pitch
You are a master thief navigating a silent, sunken vault. In this 16-bit top-down dungeon crawler, you must slip through flooded corridors, locate the glowing seal-key, unlock the heavy iron door, and reach the exit before your air runs out.

## Scope
*   **Mechanics:** Top-down grid movement, solid wall collisions, item pickup, locked door consumption, exit victory zone, and a basic oxygen timer.
*   **Screens (Greybox):**
    *   *Title Screen:* Simple layout with a "Press Enter to Start" prompt.
    *   *Game Screen:* Top-down layout with the player (Blue), walls (Grey), key (Yellow), door (Red), and exit (Green).
    *   *Pause Screen:* Overlays game state, halting player and timer.
    *   *Victory Screen:* Displays a success message and an option to restart.
    *   *Game Over Screen:* Triggered by oxygen depletion; displays failure and a retry prompt.

## Core Loop
```
[Title Screen] ➔ [Explore Grid] ➔ [Collect Key] ➔ [Unlock Door] ➔ [Reach Exit] ➔ [Victory Screen]
                        ▲
                        │ (Oxygen Depleted)
                        ▼
                  [Game Over]
```

## Non-Goals
*   No generated art assets, sprites, or animations (all rendered as debug rectangles).
*   No audio, music, or sound effects.
*   No procedural generation, multiple levels, or combat.

## Milestone Plan (Vertical Slice)
| Milestone | Description | Target |
| :--- | :--- | :--- |
| **M1: Core Engine** | Setup canvas, input, rendering loop, and basic engine hooks. | Day 1 |
| **M2: Actor System**| Implement player movement, tilemap collisions, and HUD. | Day 2 |
| **M3: Game Logic**  | Add key pickup, locked door state machine, and exit trigger. | Day 3 |
| **M4: UI & States** | Implement Title, Pause, Victory, and Game Over states. | Day 4 |
| **M5: QA & Hooks**  | Expose state via `window.__game.state` and run integration suite.| Day 5 |
