# D2 — MODELING DEPTH & CALIBRATION (X ref: embeddings, rankers tuned on years of data)

## Objective
Replace guessed constants with data-fitted ones: T0, ENERGY_SCALE, kappa,
weights (w1/w2/w3), HCI threshold, farming thresholds — each justified by
ledger distributions, never by feel.

## 1. RESEARCH
Read: `calculate_energy_delta`, `difficulty_target`, `_rolling_means`,
`promotion_gates`, `hermes calibrate` output schema. Define what "good
calibration" means: promotions reachable in weeks of real use, demotions
only on genuine dissonance, farming unprofitable (prove by simulation).

## 2. MEASURE BASELINE
On a production-like ledger (or the 167-turn sim + extended sims):
turns-to-first-promotion, demotion rate, farming profit simulation
(optimal trivial-turn bot: XP/hour vs honest path). Record numbers.

## 3. PLAN
Propose constant changes as a bounded diff table (old -> new + reason
per constant + predicted effect). Human (Tuan) approves BEFORE apply —
no auto-apply, ever.

## 4. BUILD
Apply approved constants only. Keep formulas' shape; change numbers.

## 5. AUDIT checklist
- [ ] Every constant cites a distribution number.
- [ ] Farming-profit sim re-run: trivial path stays unprofitable.
- [ ] Promotion reachable in simulation within weeks-equivalent turns.
- [ ] `hermes calibrate` recommendations consistent with new numbers.

## 6. QA gates
Full suite + safety matrix + sim-month re-run showing sane trajectory.

## 7. SCORE rubric
- 0-59: constants still guessed / undocumented.
- 60-79: every constant traced to a measured distribution.
- 80-94: + farming unprofitable by proof + trajectory sane in sim.
- 95-100: + fitted on 30+ days of REAL production ledger.
