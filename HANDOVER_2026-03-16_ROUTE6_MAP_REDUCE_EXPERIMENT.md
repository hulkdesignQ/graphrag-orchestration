# Handover: Route 6 MAP-REDUCE Experiment & Synthesis Tuning — 2026-03-16

## Summary

Continued Route 6 benchmark optimization. Diagnosed the root cause of Q-G7 synthesis variance (extraction was perfect but synthesis LLM silently dropped items), added an EXTRACTION FIDELITY rule that improved Q-G7 from 4/9→8/9 in isolation, then attempted a full MAP-REDUCE synthesis architecture that ultimately regressed the full benchmark. Reverted to the proven single-call synthesis approach.

**Current score: 156/171 (91.2%)** — same total as session start, but with better Q-G7 understanding and a committed EXTRACTION FIDELITY rule.

## Key Findings

### 1. Synthesis Was the Bottleneck, Not Extraction

Debug logging proved that ALL 4 consistently missing Q-G7 items were present in the extraction output with scores 80–100:
- "60 days written notice to terminate" (score 100)
- "changes to purchase contract in writing" (score 100)
- "$300 expenditure approval" (score 80)
- "written consent for assignment" (score 80)

The synthesis LLM received all 30 key points but silently dropped 4 of them.

### 2. EXTRACTION FIDELITY Rule (Committed)

**Commit `adcda8e7`**: Added a new synthesis rule that instructs the LLM to process each high-importance key point and include it if it fits the query's category. Includes both:
- **Positive examples**: written approval, consent, agreement in writing → all qualify as "notice mechanisms"
- **Negative examples**: warranty notification ≠ record-keeping (protects Q-G4 from over-inclusion)

Also softened the PRECISION OVER PADDING rule (removed overly rigid "do NOT conflate obligation categories" example).

Results:
- Q-G7 isolated: 4/9 → **8/9** (two 3/3 runs)
- Q-G4 isolated: 5/9 → **6/9**
- Full benchmark: **156/171** — no regression

### 3. MAP-REDUCE Synthesis Experiment (Reverted)

Implemented a full per-community MAP-REDUCE synthesis architecture:
- MAP: parallel per-community mini-synthesis (3–5 points each)
- REDUCE: merge all mini-answers into final response

**Isolated tests were spectacular**: Q-G7 9/9, Q-G8 9/9. But full benchmark regressed to 141–142/171.

**Root cause of regression**: Synthesis needs holistic cross-document context that per-community decomposition fragments. Each MAP call independently over-includes borderline items:
- Q-G9: 9/9→5/9 (warranty limitations labeled as "forfeiture terms")
- Q-G6: 7/9→4/9 (individual names included for entity queries)
- Q-G3: 8/9→6/9 (cross-community context lost)

**Lesson**: Per-file MAP works for extraction ("what facts exist?") but not synthesis ("how do these facts answer the query?"). Reverted in commit `a8b6a4d8`.

## Current Per-Question Scores (156/171)

| Q | Score | Status | Root Cause |
|---|-------|--------|-----------|
| Q-G1 | 9/9 | ✅ Perfect | — |
| Q-G2 | 9/9 | ✅ Perfect | — |
| Q-G3 | 7–8/9 | ✅ Variance | LLM non-determinism |
| Q-G4 | 5/9 | ❌ Gap | Missing inventory/furnishings; over-inclusion in 1/3 runs |
| Q-G5 | 7/9 | ✅ Variance | LLM non-determinism |
| Q-G6 | 7–8/9 | ✅ Variance | Individual names in 1/3 runs |
| Q-G7 | 4–6/9 | ❌ Gap | Synthesis drops items despite extraction finding them |
| Q-G8 | 6–8/9 | ⚠️ Variance | "No warranty clauses" hallucination in 1/3 runs |
| Q-G9 | 9/9 | ✅ Perfect | — |
| Q-G10 | 9/9 | ✅ Perfect | — |

## Files Changed (Committed)

1. **`src/worker/hybrid_v2/routes/route_6_prompts.py`** — EXTRACTION FIDELITY rule + softened PRECISION (commit `adcda8e7`)
2. **`src/worker/hybrid_v2/routes/route_6_concept.py`** — Removed debug logging (commit `adcda8e7`)
3. **`src/worker/hybrid_v2/routes/route_6_prompts.py`** — MAP-REDUCE prompts added then reverted (commit `a8b6a4d8`)
4. **`src/worker/hybrid_v2/routes/route_6_concept.py`** — MAP-REDUCE implementation added then reverted (commit `a8b6a4d8`)

## TODO List (For Next Session)

### High Priority — Variance Reduction

1. **Self-consistency voting** — Run synthesis 2–3× internally and take the union of items. This directly addresses LLM non-determinism without fragmenting context. Estimated impact: +3–6 points (stabilizes Q-G7, Q-G8, Q-G3 variance).

2. **Two-pass self-check** — After initial synthesis, run a second LLM call: "Given this answer and these key points, what did you miss?" Cheaper than self-consistency (2 calls instead of 3). Could help Q-G7 and Q-G8 specifically.

### Medium Priority — Q-G4 Improvement

3. **Q-G4 inventory/furnishings gap** — The "prepare complete inventory of furniture/furnishings" and "media invoices on monthly statements" items are in extraction but synthesis inconsistently includes them. May need a targeted extraction completeness rule for record-keeping queries.

4. **Smarter extraction dedup** — Current dedup (first 60 chars) doesn't catch semantic duplicates. 30 points slots are wasted on paraphrases. Semantic dedup (embedding similarity) or LLM-based dedup could free slots for unique items.

### Lower Priority — Architecture

5. **Negative test regression watch** — Q-N9 ("mold damage") may be affected by MAP-REDUCE changes — verify it still passes with the revert.

6. **Latency monitoring** — Track p50/p95 latency across benchmark runs. MAP-REDUCE was ~40s/query; single-call is ~30s. Important for production.

### Research Notes for Future Reference

- **MAP-REDUCE synthesis doesn't work for Route 6** — tested 3 variants (basic, with evidence cross-check, with precision rules). All regressed. Don't try again without a fundamentally different architecture.
- **The extraction is perfect** — all Q-G7 missing items score 80–100 in extraction output. Any future Q-G7 improvement must target synthesis, not extraction.
- **Rating model is already gpt-5.1** — Line 615 in route_6_concept.py uses `self.llm` (the main model), NOT a separate rating model. No upgrade path there.

## Commands Reference

```bash
# Single question test
python3 scripts/benchmark_route6_concept_r4_questions.py --url http://localhost:8000 --positive-prefix Q-G --filter-qid Q-G7 --repeats 3 --no-auth --include-context --group-id test-5pdfs-v2-fix2

# Full benchmark
python3 scripts/benchmark_route6_concept_r4_questions.py --url http://localhost:8000 --positive-prefix Q-G --repeats 3 --no-auth --include-context --group-id test-5pdfs-v2-fix2

# LLM eval
python3 scripts/evaluate_route4_reasoning.py benchmarks/<filename>.json
```
