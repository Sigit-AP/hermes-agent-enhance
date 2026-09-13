# P99 — FINAL CERTIFICATION: 100 (run only after D1..D10 all exit-gated)

## Eligibility (hard gates — any failure aborts certification)
- [ ] SCOREBOARD.md shows every dimension >= 95.
- [ ] Zero open critical/high findings across all dimensions.
- [ ] Full suite green on the final tree (paste count).
- [ ] Safety matrix 10/10 on the final tree (paste output).
- [ ] At least one production proof per dimension scored >= 95
      (lab-only 95s are capped at 94 — no exceptions).

## Certification procedure
1. Re-run every dimension's QA gates from scratch on the final tree.
   One failure anywhere = back to that dimension, certificate denied.
2. Independent re-read: re-verify 20 random ledger rows, 5 random
   claims in docs, 3 random test assertions. Log each check.
3. Write `.opencode/prompts/CERTIFICATE.md`: per-dimension final
   scores + evidence links (commit hashes, command outputs, dates),
   known limitations (explicit, no hiding), and signatures
   (commander + date).
4. Tag the release: `git tag -a leveling-100 -m <summary>` + push tag.

## Meaning of 100 (honest definition, read carefully)
100 = every professional dimension independently verified at
industrial grade for THIS system's arena, with production proof.
It does NOT mean: better than X at X's game, bug-free forever, or
finished learning. It means: the strongest verifiable claim we can
honestly make — and every number in it traces to evidence.
