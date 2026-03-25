# Handover: Sentence Window & LLM Dedup Analysis

**Date:** 2026-03-25
**Branch:** (working tree, uncommitted)

---

## Summary

Expanded GT from 48→88 verified phrases, found PPR top_k=75 achieves 100% recall, exhaustively tested LLM dedup prompt variants, and discovered that **sentence window ±1 is the key lever** for synthesis quality — jumping from 25/30 to **29/30** without any dedup.

---

## Key Findings

### 1. Ground Truth Expansion (48 → 88 phrases)

- Cross-referenced question bank Expected text against actual Neo4j source documents
- Removed hallucinated facts (e.g. "availability" not in WARRANTY doc)
- Fixed text mismatches ("1 year" → "one (1) year", "risk of loss" → "holds risk")
- **88 verified GT phrases**, all confirmed present in source Sentence nodes

### 2. PPR Recall at Various top_k

| top_k | Recall | Notes |
|-------|--------|-------|
| 50 | 83/88 (94.3%) | Current preset; 5 phrases in ranks 51+ |
| 65 | 86/88 | 2 still missing |
| 70 | 86/88 | Same 2 (indemnif, Three Hundred) |
| **75** | **88/88 (100%)** | Minimum for full recall |
| 100 | 88/88 | No additional benefit |

### 3. LLM Dedup — Exhaustive Prompt Testing

All tested against cached PPR top-75 passages (`/tmp/ppr_cache_75.json`):

| Variant | GT | Avg Kept | Verdict |
|---------|-----|----------|---------|
| A: Original ("many are redundant") | 84-85/88 | ~50 | Too aggressive, drops GT |
| B: "Keep at least half" | 80-86/88 | ~60 | Unstable |
| **C: Same-doc only** | **88/88** | **~73** | Safe but useless (drops ~2/75) |
| D: "Dedup not filter" | 84-87/88 | ~65 | Still loses GT |
| E: Keep-based (output IDs to keep) | 74/88 | ~40 | Much worse |
| F: Keep same-doc | 77/88 | ~45 | Same problem |
| G: Two groups (useful/redundant) | 70/88 | ~50 | Terrible |
| H: Unique vs duplicate | 82-87/88 | ~60 | Unstable |
| I: ATF two-step (analyze then filter) | 87/88 | ~72 | 2x latency, still loses 1 |
| Doc-rescue guardrail (post-dedup) | 87-88/88 | varies | Helps but not sufficient |

**Conclusion:** No LLM dedup prompt achieves both meaningful dedup AND lossless GT. The LLM conflates "irrelevant to question" with "redundant" — it drops off-topic passages, not just duplicates.

### 4. Reranker-Based Filtering (Voyage rerank-2)

| Threshold | GT | Total Dropped | Notes |
|-----------|-----|---------------|-------|
| 0.22 | 88/88 | 17 | Safe |
| **0.23** | **88/88** | **21** | Max safe threshold |
| 0.24 | 87/88 | — | Starts failing |

Deterministic, no variance. Better than any LLM dedup variant.

### 5. Synthesis Benchmarks (the breakthrough)

| Config | Score | Notes |
|--------|-------|-------|
| Previous baseline (top_k=50, with dedup) | 26/30 | From earlier session |
| Raw PPR top-75, no dedup, no window | **25/30** | Extra passages don't hurt |
| **PPR top-75, no dedup, sentence window ±1** | **29/30** | 🏆 Only Q-G3 at 2/3 |

**Sentence window is the real lever.** The ±1 surrounding context gives synthesis the full clause structure needed to extract complete facts.

### 6. Q-G3 (Only Miss at 2/3)

- Judge says: missed explicit "invoice total 29,900.00" and "builder repairs at no charge"
- Answer was 4,890 chars / 44 bullets — too verbose, real facts buried in noise
- Q-G5 also verbose (7,489 chars / 51 bullets) but scored 3/3
- Synthesis prompt instructions #6 ("be EXHAUSTIVE") and #8 ("completeness over brevity") may encourage over-inclusion

---

## Uncommitted Changes

### Modified files:
1. **`scripts/test_ppr_retrieval.py`** — GT expanded from 48→88 verified phrases
2. **`QUESTION_BANK_5PDFS_2025-12-24.md`** — Expanded Expected text for Q-G1–G8
3. **`src/worker/hybrid_v2/routes/route_8_hipporag2_community.py`** — Doc-rescue guardrail code added to `_llm_dedup_passages`
4. **`src/worker/hybrid_v2/pipeline/synthesis.py`** — Minor synthesis prompt edits from earlier tuning

### Temp files (not committed):
- `/tmp/ppr_cache_75.json` — Cached PPR top-75 passages for all 10 Q-G queries
- `/tmp/qg_cached_contexts_raw75.json` — Synthesis contexts from raw PPR (no window)
- `/tmp/qg_cached_contexts_window1.json` — Synthesis contexts with ±1 sentence window
- `/tmp/sentence_neighbors.json` — Neo4j NEXT_IN_SECTION neighbor data for all 188 unique sentences
- `/tmp/source_docs.json` — All source document sentences (5 docs, for GT verification)
- `/tmp/test_dedup_offline.py` — Offline LLM dedup tester (AAD auth, multiple variants)
- `/tmp/synth_only_bench.py` — Synthesis-only benchmark harness

### Benchmark files:
- `benchmarks/synth_only_20260325T224655Z.json` + `.eval.md` — Raw PPR 75, no window: **25/30**
- `benchmarks/synth_only_20260325T225639Z.json` + `.eval.md` — PPR 75 + window ±1: **29/30**

---

## Next Steps

### Immediate (production changes):
1. **Bump `ppr_passage_top_k` from 50 → 75** in comprehensive_search preset
2. **Decide on LLM dedup**: disable entirely or use reranker threshold 0.23 instead
3. **Commit GT expansion** (test_ppr_retrieval.py + question bank)

### Synthesis prompt tuning:
4. **Tighten verbosity** — Q-G3/Q-G5 produce 44-51 bullets; need to balance exhaustiveness with focus
5. Consider "focus on the specific question scope" instruction to reduce off-topic bullets
6. Re-test after prompt tightening to see if Q-G3 reaches 3/3

### LLM dedup future directions (parked):
7. **Score-based**: LLM scores each passage 1-10 for uniqueness; apply our own cutoff
8. **Within-doc only + reranker cross-doc**: LLM handles real within-doc redundancy, reranker handles cross-doc noise
9. **Merge/compress**: Instead of dropping, merge near-duplicate passages preserving all facts
10. **Fact-extract then programmatic dedup**: LLM extracts key facts per passage, then code finds strict subsets

### Server state:
- Running on port 8888 (PID 256584) with original dedup prompt + doc rescue guardrail
- Uses `comprehensive_search` preset (still top_k=50 in code)

---

## Architecture Insight

The retrieval-to-synthesis pipeline quality stack:

```
PPR top_k=75 (100% GT recall)
    → Sentence window ±1 (NEXT_IN_SECTION neighbors — key quality lever)
        → [Optional] LLM dedup or reranker filter
            → v10_comprehensive synthesis prompt
                → Answer (29/30 current best)
```

**Sentence window matters more than dedup.** The ±1 context provides clause boundaries, section headers, and surrounding conditions that let synthesis extract complete facts. Without it, isolated sentences lose their meaning (e.g., "one (1) year" without knowing it refers to the warranty period).
