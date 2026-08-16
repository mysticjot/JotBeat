# JotBeat Slop Standard — binding on every role

> Creative Director directive, 2026-08-16. Distilled from two MIT-licensed sources:
> [stop-slop](https://github.com/hardikpandya/stop-slop) (Hardik Pandya) and
> [no-ai-slop](https://github.com/petergyang/no-ai-slop) (Peter Yang).
> **The test: if a line could appear in any AI-generated game ever made, it is slop.**

## Absolute bans (player-facing text)

- **Clichés:** "ancient evil", "darkness stirs", "whispers of the deep", "destiny awaits" — and their whole family (forgotten realm, awakening power, chosen one, unspeakable force).
- **Banned words:** delve, foster, leverage, utilize, empower, robust, tapestry, realm, beacon, meticulous, intricate, paramount, transformative, elevate, embark, harness, ever-evolving.
- **Purple prose:** stacked adjectives, abstract nouns doing the work of scenes, importance puffery ("marks a pivotal moment", "stands as a testament").
- **Fake-profound kickers:** the cute aphorism that pretends to be depth. End on the concrete fact.
- **Dramatic fragmentation:** "X. And Y. And Z." / "That's it. That's the whole thing."
- **Rhetorical setups:** "What if I told you…", "Plot twist:", self-answered Question? Answer. pairs.

## Structural rules

- **Binary contrasts** ("It's not X. It's Y.") are slop — state Y directly. **EXCEPTION: lines fixed verbatim as CANON in `docs/NARRATIVE_BIBLE.md` are exempt** (the reveal "The door you opened wasn't the exit. It was the lock." is canon, not a crutch). The auditor checks the exemption against the bible, not from memory.
- **Throat-clearing openers** ("Here's the thing", "The uncomfortable truth is") — cut, state the point.
- **Voice guide wins:** every string must satisfy `NARRATIVE_BIBLE.md` §Voice — spare, salt-rough, transactional; short declaratives; second person only on the reveal.
- **Concrete over abstract:** names, numbers, mechanisms beat atmosphere words.

## Beyond text (all roles)

- No mechanic without an AC.
- No asset that fails the Art Bible scan.
- No code pattern that exists to look productive rather than to work.

## Enforcement chain

1. **Narrative Designer writes/reviews** — no player-facing string ships without its pass (`studio/roles/narrative.py`).
2. **Auditor rejects** — any player-facing string reading as generic AI output = FAILED verdict, offending line quoted, kicked back. Slop is a cert failure, same class as a broken AC.
3. Nothing generic reaches the human.
