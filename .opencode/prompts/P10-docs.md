# D10 — DOCUMENTATION & KNOWLEDGE TRANSFER (professional finish)

## Objective
A stranger can operate, audit, and extend the leveling system from docs
alone. Professional systems outlive their authors.

## 1. RESEARCH
Audit every user-facing surface: README leveling section, all CLI
`--help` texts, cause-line vocabulary, error messages. List drift
(code does X, docs say Y) as defects with file:line.

## 2. MEASURE BASELINE
Count: documented commands vs existing commands, documented rules vs
enforced rules, stale examples (run each example, record pass/fail).

## 3. PLAN
Fix list: rewrite stale sections, add runbook (install -> first
promotion -> backup -> restore -> audit), glossary of WHY vocabulary.

## 4. BUILD
Docs only. Every example re-run after writing.

## 5. AUDIT checklist
- [ ] Every CLI example pasted from a real run (no hand-typed output).
- [ ] A fresh reader completes install->level->why->backup->restore
      following only the docs (or the failure is logged and fixed).
- [ ] ASCII-safe throughout (Windows console check).

## 6. QA gates
Full suite + safety matrix (docs must not claim untested behavior).

## 7. SCORE rubric
- 0-59: docs drift from code.
- 60-79: zero drift, all examples re-run.
- 80-94: + full runbook tested end-to-end by a fresh reader/environment.
- 95-100: + external user onboards from docs alone, zero questions.
