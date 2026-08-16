# Triage reports — bug schema (HANDOFF-PHASE4 §2.6, roadmap §11.2)

Every triage report in this directory is `TRIAGE-<NNNN>-<slug>.md` and uses
this schema (industry standard):

- **id** — TRIAGE-NNNN, sequential.
- **title** — one line, imperative.
- **severity** — Blocker / Critical / Major / Minor / Trivial.
  - Blocker: gate or CI red; no workaround.
  - Critical: core loop broken or data loss; workaround exists.
  - Major: feature wrong but playable.
  - Minor: polish, flakes, cosmetic.
  - Trivial: typos, log noise.
- **repro steps** — numbered, from a cold start.
- **expected vs actual** — one line each.
- **evidence links** — spec file, screenshot/diff path, events.jsonl entry,
  cert report section. Links must resolve at review time.
- **suspected owner role** — coder / qa / director / auditor / harness.

**Regression rule (enforced at review):** any bugfix commit references a test
that would have caught the bug. If no such test exists, the fix commit adds
one. A fix without a regression test is kicked back at cert review.

**Flake policy:** a test that fails under suite load but passes 3x in
isolation is a Minor harness bug (timing assumption), ticketed — never
"fixed" by widening assertions or adding retries.
