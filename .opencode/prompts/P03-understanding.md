# D3 — SEMANTIC UNDERSTANDING & RECALL (X ref: SimClusters/TwHIN embeddings)

## Objective
Recall that understands meaning, not just keywords: zero-overlap queries
must retrieve. Precision@3 measured on a production-scale memory corpus.

## 1. RESEARCH
Read: substrate query path (FTS5 -> IDF rescoring -> fallback), stemmer,
word-set matching, `tests/test_virtual_production.py` VIRT-4 harness.
Survey light options that run on a $5 VPS: synonym-expansion dictionary,
ONNX local embeddings, sqlite-vec. Compare RAM/build cost honestly.

## 2. MEASURE BASELINE
Extend VIRT-4 corpus (target 200+ memories, 50 paraphrase queries incl.
zero-overlap cases). Record precision@1/@3 per method. This baseline is
the contract all later claims compare against.

## 3. PLAN
Cheapest method that moves zero-overlap precision first. Only adopt a
dependency if measured gain >= 2x over synonym expansion AND VPS RAM
budget allows. Document the rejected options with numbers.

## 4. BUILD
Feature-flagged retrieval path (env flag, default off until proven).
Never remove the keyword path — it is the fallback.

## 5. AUDIT checklist
- [ ] Zero-overlap precision measured, not asserted.
- [ ] Latency p95 per query recorded (VPS-grade CPU).
- [ ] RAM footprint recorded; fallback path tested with flag off.
- [ ] ASCII-only outputs re-checked.

## 6. QA gates
Full suite + safety matrix + recall benchmark in CI (the VIRT-4 test).

## 7. SCORE rubric
- 0-59: keyword-only recall, zero-overlap failing.
- 60-79: synonym/stem layer, measured gain, flagged.
- 80-94: embeddings hybrid, precision documented, VPS-viable.
- 95-100: + 30-day production recall log confirms lab numbers.
