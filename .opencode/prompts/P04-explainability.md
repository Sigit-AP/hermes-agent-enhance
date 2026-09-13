# D4 — EXPLAINABILITY & AUDIT TRAIL (our standout vs X: their models can't self-explain)

## Objective
Every number the system ever shows traces to evidence in one command.
This is the dimension where we can exceed X — defend the lead.

## 1. RESEARCH
Read: cause/hci columns, `pou_why*`, quest cause lines, episodic links,
`hermes why --episodes`. Enumerate every user-visible number and check:
can it be traced to rows? List untraceable numbers as defects.

## 2. MEASURE BASELINE
Sample 20 ledger rows: for each, time how long (commands) it takes to
explain it. Record: rows explainable in 1 command vs not.

## 3. PLAN
Close every untraceable number: missing cause templates, missing
transition markers, export gaps. Add `hermes audit` machine-readable
dump (JSON: rows + quests + episodes + gates) for third-party review.

## 4. BUILD
Templates only (deterministic, never LLM-generated). ASCII-only.

## 5. AUDIT checklist
- [ ] 20/20 sampled rows explainable in <= 2 commands.
- [ ] Third party (or adversarial re-read) reproduces every claim.
- [ ] No number on screen lacks a `why` path.

## 6. QA gates
Full suite + safety matrix + a blind re-verification pass.

## 7. SCORE rubric
- 0-59: numbers exist without traceable causes.
- 60-79: all numbers traceable within 2 commands.
- 80-94: + machine-readable audit dump + blind re-verified.
- 95-100: + external party successfully audited a production month.
