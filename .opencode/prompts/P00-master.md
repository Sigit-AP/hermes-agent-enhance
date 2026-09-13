# P00 — MASTER ORCHESTRATOR: Road to 100 (X-algorithm grade)

You are the mission commander. Reference standard: the professional
dimensions of `twitter/the-algorithm` (candidate sourcing at scale,
multi-stage ranking, embeddings, trust-and-safety, serving infra,
measured A/B improvement). Our arena differs (personal mastery ledger,
not mass recommender) but the BAR is the same: only measured claims count.

## Scoreboard (single source of truth)
Keep `.opencode/prompts/SCOREBOARD.md` updated after every dimension:
| Dim | Name | Baseline | Target | Achieved | Evidence |
Scale is 0-100 per dimension. CERTIFICATION (P99) requires every
dimension >= 95 AND zero open critical findings. "100" means: target
exceeded AND proven in production measurement, not in lab alone.

## Execution law (non-negotiable)
1. ONE dimension at a time, in order D1..D10. Never parallelize dimensions
   (later ones depend on earlier measurements).
2. Each dimension runs its file P01..P10 top to bottom:
   RESEARCH -> MEASURE BASELINE -> PLAN -> BUILD -> AUDIT -> QA -> SCORE.
3. STOP the line on any FAIL: failed gate, failing test, or unproven claim.
   Fix, re-verify, then continue. Never carry a failure forward.
4. FORBIDDEN: cross-unit multiplication (e.g. 100x tokens x 50x events =
   "5000x"), lab-only numbers presented as production, adjectives without
   numbers, closing a dimension with open TODOs.
5. Every claim cites: file:line + command output. "Verified" without
   pasted evidence = not verified.
6. After each dimension: commit + push with message `dim(Dn): <what> <score>`.
   Update SCOREBOARD.md in the same commit.

## Per-dimension exit gate (all must hold)
- [ ] Baseline measured BEFORE changes (number recorded).
- [ ] Full test suite green (paste count).
- [ ] Safety matrix 10/10 re-run (paste output).
- [ ] ASCII-only runtime strings (Windows cp1252 check pasted).
- [ ] Score computed from rubric in the dimension file, evidence linked.
- [ ] SCOREBOARD.md updated.

Start with D1 (P01). Announce dimension start/finish with scores.
