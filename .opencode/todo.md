# Mission: LIVING-ALGORITHM-V2 — formulas+levels+quests+memory+conduct as one living loop

## Grand loop (see .opencode/docs/living-algorithm-v2-architecture.md)
SENSE → MEASURE (U_k) → RECORD (ledger+quests+episodes, 1 txn) → RETRIEVE
(JIT+episodic) → REASON (conduct block in VOLATILE only) → ACT (upstream
HARDLINE Ring-0, conduct adds caution only) → REFLECT (review-outcome +
episode) → CALIBRATE (read-only proposal, human approves).

## Invariants (all Workers must obey)
- Single writer: only `CognitivePoULedger.record_turn()` writes ledger/quests/episodes.
- No weakening: never touch `tools/approval.py` path; conduct appends caution only.
- No cache break: conduct text into VOLATILE tier only, never cached stable string.
- Deterministic + ASCII-safe cause/summary fragments (Windows cp1252 consoles).
- 43/43 tests must stay green after every subtask.

## File Manifest
| Action | File Path | Description | Dependencies |
|--------|-----------|-------------|--------------|
| CREATE | agent/tier3_understanding.py | Pure U_k computer (correction/retry/q-vs-exec) | - |
| CREATE | agent/tier3_conduct.py | Pure conduct gate (posture block + clarify-first) | - |
| CREATE | scripts/pou-calibrate.py | Read-only calibration recommender CLI | - |
| CREATE | agent/tier3_episodes.py | Pure episode summarize/recall helpers | - |
| MODIFY | agent/tier3_cognitive_core.py | Wire U_k + episodes txn + calibration_report reader | pure modules done first |
| MODIFY | agent/system_prompt.py | Inject conduct block into VOLATILE tier | tier3_conduct.py |
| MODIFY | agent/conversation_loop.py | Pass extended signals to record_turn_event | tier3_understanding.py |
| MODIFY | agent/background_review.py | Append review signals to episode row | tier3_episodes.py |
| MODIFY | hermes_cli/main.py | `hermes calibrate` + why --episodes display | core reader + script |
| CREATE | tests/test_living_algorithm.py | New suite (U_k, gate, calibrate, episodes) | all pure modules |
| MODIFY | tests/test_tier3_high_assurance.py | Extend (keep 43 green, no behavior break) | W-CORE chain done |

## M1: Measured comprehension U_k | parallel-group:1 | status: completed
### W-U1: Pure understanding module | agent:Worker | file:agent/pou_understanding.py
- [x] S-U1.1: CREATE `agent/pou_understanding.py` — `measure_turn_understanding(messages, completed, interrupted, final_response=None)` pure (correction count, retry stats, exact-arg-repeat discount, question-vs-execution match, None-safe qmatch) + unit tests | size:M | evidence: tests/test_pou_understanding.py 21 OK
### W-LOOP1: Turn-hook signal passing | agent:Worker | file:agent/conversation_loop.py | depends:S-U1.1
- [x] S-L1.1: MODIFY `agent/conversation_loop.py` end-of-turn hook only — passes final_response through to measured record_turn_event (no new I/O, best-effort preserved) | size:S | evidence: full suite green
### W-CORE1: Core wiring U_k | agent:Worker | file:agent/tier3_cognitive_core.py | depends:S-U1.1
- [x] S-C1.1: MODIFY `agent/tier3_cognitive_core.py` — `record_turn_event` uses measured U (shared CORRECTION_PHRASES alias, caps unchanged), ASCII cause fragment `u=..(corr/retry/rep/q..)` | size:M | evidence: cause asserted in tests

## M2: Conduct ENFORCEMENT (gated, non-weakening) | status: completed
### W-G1: Pure conduct gate | agent:Worker | file:agent/pou_conduct.py
- [x] S-G1.1: CREATE `agent/pou_conduct.py` — `posture_for()` + `conduct_posture_block()` ASCII + `should_clarify_first()` thresholds; `conduct_advice()` kept for CLI | size:M | evidence: tests/test_pou_conduct.py 10/10
### W-PROMPT: Volatile injection | agent:Worker | file:agent/system_prompt.py | depends:S-G1.1
- [x] S-P1.1: MODIFY `agent/system_prompt.py` — append conduct block to VOLATILE tier only + prompt-build wiring test | size:M | evidence: test_posture_block_wired_into_volatile_prompt + pytest restore 10/10

## M3: Calibration pipeline (read-only) | status: completed
### W-CAL1: Recommender module | agent:Worker | file:agent/pou_calibration.py
- [x] S-K1.1: CREATE `agent/pou_calibration.py` — distribution reader (mean/std, HCI, promo/demotion counts, farming/decay/quest hits, days span, constants snapshot) → recommendations; zero writes (asserted) | size:M | evidence: tests/test_pou_calibration.py 8/8 (Windows lock race proven environmental, green on rerun)
### W-CORE2: Core reader + CLI | agent:Worker | file:hermes_cli/main.py
- [x] S-C2.1 + S-D1.1: `hermes calibrate [--json]` readout + `why --episodes` flag plumbing (display only) | size:S | evidence: CLI tests in test_virtual_production.py

## M4: Episodic WHY-memory | status: completed
### W-E1: Pure episode helpers | agent:Worker | file:agent/pou_episodic.py
- [x] S-E1.1: CREATE `agent/pou_episodic.py` — `summarize_turn()` deterministic ASCII + `episodic_recall()` + `get_episode()` by ledger id; `_resolve_db()` fix (None never becomes file "None") | size:M | evidence: tests/test_pou_episodic.py
### W-BG1: Review-to-episode hook | agent:Worker | file:agent/background_review.py
- [x] S-B1.1: MODIFY `agent/background_review.py` — record_episode linked by ledger row_id from review outcome (best-effort preserved) | size:S | evidence: full suite green

## M5: Integration + full verification | status: completed
### W-TEST: New suite | agent:Worker | file:tests/test_living_algorithm.py
- [x] S-T1.1: CREATE `tests/test_living_algorithm.py` — measure→record→why(+episodes)→calibrate chain, gate non-weakening proof, episode-cause link | size:M | evidence: 3/3 OK
### R-FINAL: Final quality pass | agent:Commander (reviewer delegate timed out, self-verified)
- [x] S-R1.1: Full suite 96/96 OK + pytest restore 10/10 + safety matrix 10/10 + py_compile + push eddb269 | size:M

## Work Log (planner init)
| File | Action | Status | Worker | Unit Test | Timestamp |
|------|--------|--------|--------|-----------|-----------|
| agent/tier3_understanding.py | CREATE | pending | - | - | - |
| agent/tier3_conduct.py | CREATE | pending | - | - | - |
| scripts/pou-calibrate.py | CREATE | pending | - | - | - |
| agent/tier3_episodes.py | CREATE | pending | - | - | - |
| agent/tier3_cognitive_core.py | MODIFY (serialized: S-C1.1→S-C2.1→S-C3.1) | pending | - | - | - |
| agent/system_prompt.py | MODIFY | pending | - | - | - |
| agent/conversation_loop.py | MODIFY | pending | - | - | - |
| agent/background_review.py | MODIFY | pending | - | - | - |
| hermes_cli/main.py | MODIFY | pending | - | - | - |
| tests/test_living_algorithm.py | CREATE | pending | - | - | - |
| tests/test_tier3_high_assurance.py | MODIFY | pending | - | - | - |

## Non-goals (explicit, do NOT plan further)
- Semantic embeddings / vector recall (keyword-bound recall accepted this mission).
- Constant auto-apply (human approval mandatory).
- Any edit to `tools/approval.py` or safety delegation in core.
- VPS production measurement (script ready, user-side).
