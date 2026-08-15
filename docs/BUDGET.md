# Budget — Token Caps, Escalation Ceilings, Cost Model

> Template. Enforced in code by `studio/models.py`; owned by the Producer (roadmap §2.6, §9).
> Values below are the roadmap defaults — tighten them from real ledger data, not pricing pages.

## Per-role token caps (per call)

| Role | Max input tokens | Max output tokens | Notes |
|---|---|---|---|
| director | 10,000 | 2,000 | 1M-context model for whole-GDD reads |
| coder | 30,000 | 4,500 | diff-only output contract (target ~1.5k out) |
| designer | 8,000 | 2,000 | |
| artist / sound | 3,000 | 1,000 | JSON manifests are trivial |
| qa | 13,000 | 2,500 | prefix caching expected |
| auditor | 17,000 | 1,500 | receives evidence digests, never raw traces |
| publisher | 5,000 | 1,000 | |
| triage | 2,000 | 500 | cheapest classification model |

The Producer rejects calls that exceed caps.

## Escalation ceiling

```text
cheap model → 2 verified failures
→ frontier model with shrunk context → 2 more failures
→ human ticket. Runaway cost is structurally impossible (roadmap §2.7).
```

## Token-rationing rules (enforced)

1. Diff-only output contract — Coder emits unified diffs, never whole files
2. Repo map, not repo — precomputed index (~4k tokens) + max 2 target files per call
3. Log tails — error context = last 50 lines
4. Prefix caching — identical role prompts/system context across calls
5. Small model for triage, big model for surgery
6. Auditor evidence digests — structured summaries, not raw Playwright traces
7. State summarization — `STATE_SUMMARY.md` (~2k tokens) replaces raw `events.jsonl` reads

## Cost model (measured, per finished game)

- Unrationed estimate: ~5.1M tokens, 88% input. With rationing: ~2.5M tokens/game.
- Target cash cost: $0.36/game (Kimi subscribed) → $0.54 (post-downgrade). All-paid worst case ~$1.26.
- Producer computes **cost per verified task** and **cost per game** after every run from `state/events.jsonl`.
- If actual tokens/game drifts above ~3M, caps tighten automatically.

## Ledger schema (state/events.jsonl)

```json
{"ts": "ISO-8601", "task": "AC-004-door", "role": "coder",
 "provider": "dashscope", "model": "qwen3-coder-next",
 "tokens_in": 13240, "tokens_out": 1180, "cached_in": 9268,
 "retry": 2, "escalated": false, "cost_usd": 0.0024}
```

Security: the ledger logs provider names, never credentials (roadmap §8.4).
