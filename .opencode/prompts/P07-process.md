# D7 — ENGINEERING PROCESS (X ref: monorepo discipline, review culture at scale)

## Objective
Make quality automatic, not heroic: CI gates, coverage floors, and
release checklists so no future change can silently regress the system.

## 1. RESEARCH
Inventory current process: unittest files, pytest config gaps (missing
timeout plugin breaks `pytest` default run), LF/CRLF warnings, no CI
visible in repo. List every manual step currently done by hand.

## 2. MEASURE BASELINE
Coverage of `agent/tier3_cognitive_core.py` + pou_* modules (coverage.py),
full-suite runtime, count of manual verification steps per push.

## 3. PLAN
CI workflow (or documented local gate if CI impossible): compile +
unittest + pytest-restore + safety matrix + ASCII check + recall bench,
all as one command. Coverage floor for leveling code (>=90%).

## 4. BUILD
Workflow files + one `verify` entrypoint script. No product-code changes
except what gates require.

## 5. AUDIT checklist
- [ ] One command runs everything; paste green output.
- [ ] Coverage floor met and enforced (fail below floor).
- [ ] pytest default run fixed or documented workaround.

## 6. QA gates
The gate itself is the deliverable: demonstrate a deliberately broken
change being caught by the gate.

## 7. SCORE rubric
- 0-59: manual verification only.
- 60-79: one-command gate, all green.
- 80-94: + coverage floor enforced + breakage-catch demo.
- 95-100: + gate running on every push for 30 days (CI or logged runs).
