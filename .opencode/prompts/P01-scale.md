# D1 — SCALE & PRODUCTION HARDENING (X ref: serve hundreds of millions, realtime)

## Objective
Prove the leveling pipeline stays correct and fast under production-like
load on a $5 VPS: concurrent gateway turns, 100k-row ledger, month-long soak.

## 1. RESEARCH
Read: agent/tier3_cognitive_core.py (`_connect` timeout=30, indexes
idx_pou_timestamp/idx_pou_complexity), conversation_loop end hook,
background_review thread model. List every shared-state touchpoint
(DB path, lru_cache, FTS triggers). Identify lock contention risks
under concurrent gateway threads.

## 2. MEASURE BASELINE (record numbers first)
- `scripts/pou-measure.py --json` on a seeded 100k-row ledger copy.
- Time: single record_turn, 50-thread concurrent record burst, JIT query
  p50/p95, FTS backfill time. Paste all timings.

## 3. PLAN
Write the fix list BEFORE code: WAL mode? busy-timeout raise? index
additions? hook async/defer under load? State expected gain per fix.

## 4. BUILD
Minimal diffs only. Never change scoring math in this dimension.

## 5. AUDIT checklist
- [ ] No lost writes under concurrency (row counts match attempts).
- [ ] No DB-locked exceptions in logs during burst test.
- [ ] p95 record_turn within budget set in PLAN.
- [ ] ASCII-only runtime strings re-checked.

## 6. QA gates
Full suite green + safety matrix + soak (7-day simulated clock or
100k-turn loop) with zero errors.

## 7. SCORE rubric
- 0-59: untested under load / lost writes observed.
- 60-79: correct under burst, timings recorded, no timeouts.
- 80-94: + soak clean + p95 within budget + report in docs.
- 95-100: + proven on live VPS traffic (attach `pou-measure.py` output).
