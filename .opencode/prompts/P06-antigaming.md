# D6 — ANTI-GAMING & FRAUD ECONOMICS (X ref: spam/abuse arms race)

## Objective
Make cheating the leveling system provably unprofitable: optimal bot
play must always lose to honest use. Numbers, not slogans.

## 1. RESEARCH
Read: farming guard (30/h, x0.5), quest caps (+150/turn), AUTO_TURN cap
0.15, trivial-turn economics. Model the attacker: infinite trivial turns,
correction-stuffing, multi-session splitting, clock games.

## 2. MEASURE BASELINE
Simulator: optimal-farming bot vs honest trajectory over 30 virtual days.
Metrics: XP/hour each, level reached each, guard trigger counts. Record.

## 3. PLAN
Close every profitable hole found: dynamic thresholds, diminishing
returns per session, cross-session velocity checks. Each fix must keep
honest-path speed unchanged (prove with the same sim).

## 4. BUILD
Server-side (DB-query) checks only; never client-side promises.

## 5. AUDIT checklist
- [ ] Farming bot XP/hour < 10% of honest path in sim.
- [ ] Honest trajectory speed unchanged vs pre-fix sim.
- [ ] All economics in WHY-visible causes (guard hits logged).

## 6. QA gates
Full suite + safety matrix + sim committed as regression test.

## 7. SCORE rubric
- 0-59: no attacker model / sim.
- 60-79: sim exists, farming unprofitable, honest path intact.
- 80-94: + second attacker strategy family defeated.
- 95-100: + 30-day production ledger shows zero farming patterns.
