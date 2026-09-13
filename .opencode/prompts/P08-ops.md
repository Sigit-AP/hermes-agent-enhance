# D8 — OBSERVABILITY & OPS (X ref: realtime monitoring, on-call rigor)

## Objective
The system watches itself in production: demotion storms, ledger stalls,
DB growth, and backup health are visible without SSH heroics.

## 1. RESEARCH
Read: `hermes level/why/quests/calibrate`, `pou-measure.py`, export/import
roundtrip, install.sh service setup. Define SLOs: ledger write success
rate, `level` command latency, DB size growth/week.

## 2. MEASURE BASELINE
On VPS: command latencies, DB size, backup/restore drill time. Record.

## 3. PLAN
Alerting rules (demotion burst, 7-day ledger silence, DB > threshold),
weekly `pou-measure.py --json` log rotation, restore drill procedure.

## 4. BUILD
Scripts + docs only. No scoring-math changes.

## 5. AUDIT checklist
- [ ] Each alert fires on a simulated condition (paste proof).
- [ ] Restore drill from export succeeds on a clean VPS path.
- [ ] Dashboard/API readout planned (not necessarily built).

## 6. QA gates
Full suite + safety matrix + drill log.

## 7. SCORE rubric
- 0-59: blind in production.
- 60-79: SLOs defined + measured + alerts fire in sim.
- 80-94: + 30 days of logged `pou-measure.py` history.
- 95-100: + a real incident caught by alerts with postmortem.
