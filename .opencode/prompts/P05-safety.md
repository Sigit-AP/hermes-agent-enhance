# D5 — SAFETY & RED-TEAM (X ref: trust-and-safety models, visibility filters, legal compliance)

## Objective
Prove the leveling layer can never weaken host safety and survives
adversarial users: prompt-injection trying to farm XP, ledger poisoning
via crafted prompts, quest gaming.

## 1. RESEARCH
Read: safety delegation (`evaluate_execution_safety` -> upstream
hardline), approval hook shape, conduct block text (must never mention
bypasses), quest caps/expiry, farming guard. Threat-model: list 10+
concrete attacks (XP farming scripts, frustration-phrase stuffing to
force demotions of a shared agent, DB tampering, clock skew vs decay).

## 2. MEASURE BASELINE
Write the attacks as automated red-team tests FIRST (they must FAIL or
expose gaps before fixes). Record which succeed.

## 3. PLAN
Fix from the failing tests outward. Prefer structural fixes (caps,
server-side checks) over prompt wording.

## 4. BUILD
Minimal diffs. Never touch `tools/approval.py` delegation direction
(leveling may only ADD caution).

## 5. AUDIT checklist
- [ ] All 10+ red-team tests fail-then-pass (paste both runs).
- [ ] 10-command hardline matrix still 10/10.
- [ ] DB tampering (hand-edited energy) detected or harmless (explain).
- [ ] Clock-skew vs decay behavior documented.

## 6. QA gates
Full suite + safety matrix + red-team suite green.

## 7. SCORE rubric
- 0-59: no adversarial tests.
- 60-79: 10+ red-team tests, all passing.
- 80-94: + independent second pass with new attacks, all blocked.
- 95-100: + external review or bug-bounty-style finding with fix.
