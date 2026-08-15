# Test Plan — Acceptance Criteria

> Template. Owned by QA; audited by the Auditor. One scripted test per AC, mapped by ID.
> Status values: `MET | FAILED | UNVERIFIED | SKIPPED`. Only the Auditor sets MET (roadmap §2.3, §2.4).
> Every accepted AC joins the regression suite and reruns on every change (roadmap §11.3).

## AC format

```markdown
## AC-NNN: <Short title>
Given <precondition>,
when <action>,
then <observable result>.

Verification: scripted browser test | deterministic check | manual
Evidence: <what proves it — state assertions, screenshots, logs>
Test: game/tests/ac-NNN-<slug>.spec.ts
Status: UNVERIFIED
```

---

## AC-000: Example — replace with real criteria

Given the game has booted,
when the Title scene renders,
then `window.__game.state.scene` equals `"Title"`.

Verification: scripted browser test
Evidence: state assertion via the debug hook (see ADR-0001)
Test: game/tests/ac-000-title.spec.ts
Status: UNVERIFIED
