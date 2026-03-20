# Handover: Route 6 Optimization — 160/171 High + Experiment Results

**Date:** 2026-03-17  
**Branch:** `fix/git-flow-cleanup`  
**Status:** Route 6 at **160/171 (93.6%)** — new all-time high; further experiments tested but no net gain beyond variance

---

## Score Progression

| Run | Score | Key Changes |
|-----|-------|-------------|
| Prior baseline | 156/171 | Extraction fidelity rule |
| + Completeness check (v4, ≥85 threshold) | **160/171** ✨ | Q-G7+2, Q-G8+2, Q-G4+1 |
| + Text dedup + default config | 156-158/171 | Within variance band |
| + Wider retrieval (50/25/3/exp/0.70) | ~155/171 | Q-G3+2 but Q-G8-3 (noise) |
| + MAP-REDUCE synthesis | 6/9 on Q-G7 | REDUCE still drops items — disabled |
| + 40 extract points | ~155/171 | Q-G5+2 but Q-G7-2, Q-G8-3 |
| + ONE-BY-ONE extraction fidelity | 156/171 | Q-G9-4 (over-inclusion) |
| + Doc coverage must-include | 156/171 | Q-G8+1 but Q-G9-4 |
| Final (prompts reverted to 160 baseline) | 155-160/171 | Score stability band |

## Committed Changes (This Session)

1. **`a23ecb05`** — Two-pass completeness check (ROUTE6_COMPLETENESS_CHECK=1, ≥85 threshold)
   - After synthesis, second LLM verifies high-importance key points
   - Missing items APPENDED (never rewrites) — prevents regression
   - **Achieved 160/171** — new high water mark
2. **`218234e4`** — Text-level sentence dedup in retrieval + expansion
   - Dedup by first 100 chars (lowercased) catches identical text across sentence IDs
   - Applied in both `_retrieve_sentence_evidence()` and expansion injection
3. **`1cada606`** — MAP-REDUCE synthesis (ROUTE6_MAP_REDUCE_SYNTHESIS=0, off by default)
   - Per-community MAP mini-answers → REDUCE merge
   - Tested: Q-G7 scored 6/9 vs 8/9 single-call — REDUCE still drops items
   - Returns Tuple[str, List[Dict]] from extraction for structured data access

## Key Findings

### The Precision vs Recall Trap
- Stronger prompts that improve Q-G8 (liability coverage) **hurt** Q-G9 (non-refundable terms)
- Q-G8 needs broad interpretation: warranty disclaimers ARE liability provisions
- Q-G9 needs narrow interpretation: warranty limitations are NOT forfeiture terms  
- **No single prompt instruction works for both** — this is a fundamental LLM limitation

### Score Stability Band: 155-160/171
Across 5 full benchmarks today, scores ranged 155-160. The variance comes from:
- Q-G7/G8/G9/G10: ±2-3 points per run from synthesis LLM non-determinism
- Temperature is already 0 — this is inherent model behavior
- Q-G4/G5/G6: stuck at 6/9 due to retrieval gaps (items never reach context)

### Theoretical Ceiling: 165/171
Best-observed per-question across all runs: Q-G1=9, G2=9, G3=9, G4=6, G5=9, G6=7, G7=9, G8=9, G9=9, G10=9 = 85/90 + 81 = 165

### What DOESN'T Work
| Approach | Why It Fails |
|----------|-------------|
| MAP-REDUCE synthesis | REDUCE step has same context-size problem as single-call |
| More extract points (30→40) | More noise → more items for LLM to drop |
| Wider retrieval (top_k 30→50) | Same noise problem — retrieval slots wasted on low-relevance |
| Stronger "include everything" prompts | Over-inclusion penalized by judge (Q-G9) |
| ONE-BY-ONE processing instruction | Forces inclusion of borderline items |

## Remaining Gap Analysis (11 points)

| Question | Score | Gap Type | Root Cause |
|----------|-------|----------|------------|
| Q-G4 | 6/9 | Retrieval | "inventory of furnishings" and "media invoices" never in context |
| Q-G5 | 6-9/9 | Retrieval + Variance | "indemnify/hold harmless" from PMA sometimes missing |
| Q-G6 | 6-7/9 | Retrieval | "Bayfront Animal Clinic" entity typed CONCEPT not ORG |
| Q-G7 | 6-9/9 | Variance | Synthesis drops items from 30-point context |
| Q-G8 | 5-9/9 | Variance | Sometimes says "no warranty clauses" when they're in context |
| Q-G9 | 5-9/9 | Variance | Over-includes warranty items OR correctly limits |
| Q-G10 | 7-9/9 | Variance | Minor fluctuation |

## TODO List (Priority Order)

### To Reach 163-165/171
- [ ] **Fix Q-G6 entity type** — Change "Bayfront Animal Clinic" from CONCEPT→ORGANIZATION in index (requires re-indexing or manual Cypher fix)
- [ ] **Self-consistency voting** — Run synthesis 2-3×, take union/intersection. Addresses variance on Q-G7/G8/G9
- [ ] **Query-adaptive precision** — Detect query type (broad listing vs narrow terms) and adjust prompt rules dynamically

### Code Quality
- [ ] **Push to remote** and create PR for Route 6 changes
- [ ] **Route 8 bug fixes** — document_id mismatch in min_chunks_per_doc, entity-doc-map returning 0 rows

---

## Key Files

| File | Purpose |
|------|---------|
| `src/worker/hybrid_v2/routes/route_6_concept.py` | Route 6 handler — completeness check at ~565, MAP-REDUCE at ~645, extraction at ~867, dedup at ~1440 |
| `src/worker/hybrid_v2/routes/route_6_prompts.py` | All prompts — synthesis, extraction, completeness check, MAP/REDUCE |
| `scripts/benchmark_route6_concept_r4_questions.py` | Benchmark runner |
| `scripts/evaluate_route4_reasoning.py` | LLM judge (gpt-5.1) |

## Testing Commands

```bash
# Server
PYTHONUNBUFFERED=1 nohup python -m uvicorn src.api_gateway.main:app --host 0.0.0.0 --port 8888 --timeout-keep-alive 300 > /tmp/server.log 2>&1 &

# Single question test
PYTHONPATH=. python3 scripts/benchmark_route6_concept_r4_questions.py --url http://localhost:8888 --positive-prefix Q-G --filter-qid Q-G7 --repeats 3 --no-auth --include-context --group-id test-5pdfs-v2-fix2

# Full benchmark
PYTHONPATH=. python3 scripts/benchmark_route6_concept_r4_questions.py --url http://localhost:8888 --positive-prefix Q-G --repeats 3 --no-auth --include-context --group-id test-5pdfs-v2-fix2

# LLM eval
PYTHONPATH=. python3 scripts/evaluate_route4_reasoning.py benchmarks/<file>.json
```
