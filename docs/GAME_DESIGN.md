# SALTBOUND: The Sunken Seal — Game Design (Game 1)

> One page. Produced by Narrative Designer + Director from `docs/NARRATIVE_BIBLE.md` canon — no new story invention. **Status: AWAITING CREATIVE DIRECTOR APPROVAL. No construction until approved.** Canon beats and card lines are fixed verbatim; this document maps them to buildable areas.

**Fantasy:** you are a thief who dives into a drowned kingdom to steal the key to its deepest lock — and the air in your lungs is counting down.

**Target playthrough:** 15–25 minutes. Top-down 16-bit dungeon crawler (Phaser 4, grid movement, per GDD pillars).

## Structure

### Area 1 — The Shallows (~4–6 min)
Sunken outskirts: open water over rooftops, wide rooms, generous light.
- Teaches: movement, wall collision, the lungstone HUD (a relic, not a bar — mechanical canon).
- **First lungstone pickup** placed on the critical path: touching it refills air. Oxygen drain is gentle; the player can loiter and survive.
- No combat. Ends at a descent gate: a sigil-marked door, unlocked, going down.

### Area 2 — The Drowned Rows (~6–9 min)
Drowned tenements in tight rows: narrow lanes, blind corners, doors named for their seals.
- **Combat introduced.** Enemy 1: **Drowner** — a drowned deckhand husk. Slow, drifts toward Maren, contact damage. Enemy 2: **Silt Eel** — fast, holds still until it lunges in a straight line down a lane.
- **Key/lock economy introduced:** small vault doors, each key placed *deeper than the door it opens* (canon). Keys are consumed on use.
- Oxygen tightens: longer gaps between lungstones; pickups placed as pacing valves — each one sits just past a risk (an eel lane, a drowner cluster).

### Area 3 — The Vault Approach (~5–8 min)
The deep stair to the great vault. Sigil markings on the door art may foreshadow what the doors are *for*; UI never says it (mechanical canon).
- Both enemy types combined in layered rooms; tightest oxygen economy in the game.
- The **Curator makes contact** — a dive-bell line, transactional, in voice-guide register. He knows more about the doors than an employer should (canon); he does not explain.
- Climax: the Seal-Key chamber. Lifting the Seal-Key → **the water changes**: lungstone drain rate increases (tuning change, not a new mechanic — canon). The way back is the pressure spike.

### Finale (~2 min)
- The iron door — presented to the player as the escape. Maren opens it.
- Victory card, verbatim: *"The door you opened wasn't the exit. It was the lock."*
- Curator handoff, verbatim: *"Do you know what this opens?"*
- The knock from below. Something answers.
- Hook card, verbatim: *"SALTBOUND will return in The Iron Chapel."*

## Content checklist (the bar COMMERCIAL_BASELINE.md matches against)

- [ ] 3 areas + finale, in order, with distinct layouts and escalating oxygen pressure
- [ ] 2 enemy types minimum (Drowner, Silt Eel), each with distinct behavior
- [ ] Lungstone pickups placed as pacing valves in every area
- [ ] Canon beats 1–8 delivered in order (routine job → Seal-Key → water changes → iron door → reveal card → handoff → knock → hook card)
- [ ] Card lines verbatim from NARRATIVE_BIBLE; all other player-facing text through Narrative Designer + slop check
- [ ] State frame: boot → title → intro card → play → pause → victory sequence / game over → restart; no dead ends
- [ ] Oxygen expressed as the lungstone relic; post-Seal-Key escalation is a drain-rate tuning change only

## Out of scope for Game 1

Procedural generation, multiple endings (the re-seal-or-open choice is the saga finale, not Game 1), Maren speaking on-screen (default: she does not — canon OPEN, unresolved), naming what lies below.
