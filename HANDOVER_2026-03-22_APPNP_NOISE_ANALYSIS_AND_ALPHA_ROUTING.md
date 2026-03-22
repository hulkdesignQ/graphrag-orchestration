# Handover: APPNP Noise Analysis & Alpha Routing Plan
**Date:** 2026-03-22  
**Session Focus:** Signal-to-noise optimization, ground truth cleanup, LLM benchmark evaluation

---

## Summary

Achieved **48/48 (100%) PPR retrieval** with APPNP + reranker predictions, then analyzed why the LLM still produces verbose/incomplete answers despite perfect retrieval. Root cause: graph propagation compresses reranker score discrimination, and the reranker threshold creates a precision-recall tradeoff that affects Q-D and Q-G questions differently.

**Best LLM eval scores this session:**
- Q-D: **56/57 (98.2%)** — threshold=0.22, α=0.5
- Q-G: **53/57 (93.0%)** — threshold=0.30, α=0.5
- Combined best (threshold=0.22): **107/114 (93.9%)**, negatives 9/9

---

## Key Findings

### 1. Ground Truth Cleanup
- Removed `("not transferable", "WARRANTY")` from Q-G1 test — it's a transferability restriction, not a termination rule (~30% would expect it)
- Kept `("sells", "WARRANTY")` — "terminates if purchaser sells/moves out" IS a termination rule
- Q-G1 now has 6 required phrases (was 7), "not transferable" still tested in Q-G8
- **Committed:** `fdbb6708`

### 2. Top-K Analysis
| top_k | Recall | Status |
|-------|--------|--------|
| **50** | **48/48 (100%)** | ✅ Minimum for perfect |
| 40 | 46/48 | ❌ misses "confidential", "manag" |
| 30 | 45/48 | ❌ misses "deposit", "purchase" too |

### 3. Signal-to-Noise Problem (top-50 passage analysis for Q-G1)
- Top-10: **100% relevant** (10/10)
- Top-20: 60% relevant (12/20)
- Top-30: 47% relevant (14/30)
- Top-50: **30% relevant** (15/50)
- Score ratio across all 208 passages: only **3.5x** (0.0073 → 0.0021)

### 4. Entity Embedding Seeds Are the Noise Source
- 6 entities from triples: `90 days`, `customer`, `agent`, `termination`, `full refund`, `right to cancel` — all query-relevant
- 9 entities from entity embedding search (Step 3e): `owner` (43 passages), `builder` (30), `party` (25), `warranty` (40), `dispute`, `contractor`, `invoice`, `PMA` — generic contract terms
- **However, disabling entity embedding seeds made no difference** because APPNP with `seed_weight=0.0` ignores entity seeds entirely — predictions come 100% from the reranker
- Structural seeds were already disabled in preset

### 5. Graph Propagation Hurts Discrimination
Compared reranker input (Step 3.5 scores) vs APPNP output:
- **Top 10: identical** — propagation doesn't change signal
- **After rank 10: propagation promotes noise** — "Contractor assists with permitting" promoted +134 ranks by graph connectivity
- "A. Binding Arbitration" heading promoted +38 ranks
- Graph propagation compresses the reranker's clean score separation

### 6. α=1.0 (Pure Reranker) Works for Q-G
- 48/48 recall at top_k=50 with α=1.0
- Same result as α=0.5 — propagation adds nothing for cross-document queries
- But α=1.0 would hurt Q-D (detail queries need graph walk for entity discovery)

### 7. Reranker Threshold Tradeoff
| Threshold | Q-D Score | Q-G Score | Combined |
|-----------|-----------|-----------|----------|
| **0.22** | **56/57 (98.2%)** | 51/57 (89.5%) | **107/114 (93.9%)** |
| **0.30** | 51/57 (89.5%) | **53/57 (93.0%)** | 104/114 (91.2%) |

- Threshold 0.30: better Q-G precision, but drops critical Q-D passages ("final settlement", "$300 written approval", "hold harmless")
- Threshold 0.22: keeps all passages → Q-D benefits greatly, Q-G gets slightly verbose

### 8. Retrieval Gap Analysis (threshold=0.30)
Most 2/3 scores are **retrieval gaps** (info not in LLM context), not synthesis failures:
- Q-D3: missing "10 business days", "3 business days" — filtered by threshold
- Q-D5: missing "final settlement", "first occupancy" — filtered by threshold
- Q-D10: missing "consequential damages", "implied warranties" — filtered by threshold
- Q-G7: missing "$300 written approval" — filtered by threshold

---

## Current Configuration (Best)

```
propagation_mode=appnp
appnp_alpha=0.5
reranker_gate=1
ppr_passage_top_k=50
rerank_instruction="Find passages that directly answer or provide specific factual details for: "
rerank_relevance_threshold=0.22 (preset default)
```

## Architecture Insight: Q-D vs Q-G Need Different Alpha

| Question Type | Needs | Optimal α | Why |
|---------------|-------|-----------|-----|
| **Q-D** (detail) | More graph walk | **0.3** | Entity connections discover "final settlement", "$300" passages that reranker scores low |
| **Q-G** (cross-doc) | More reranker | **0.8** | Reranker is best predictor for semantic relevance; graph walk adds noise |

**Decision:** Use **router-driven dynamic α** (not two separate routes):
- Same Route 8 code, same APPNP
- Router classifies query type and passes `appnp_alpha` as config override
- Router already distinguishes single-doc vs cross-doc intent

---

## Files Modified This Session

| File | Change | Committed |
|------|--------|-----------|
| `QUESTION_BANK_5PDFS_2025-12-24.md` | Removed "not transferable" from Q-G1, kept "sells" | ✅ fdbb6708 |
| `scripts/test_ppr_retrieval.py` | Removed "not transferable" from Q-G1 required | ✅ (no diff, was already updated) |

All APPNP code changes were committed in prior sessions.

---

## TODO List (Priority Order)

### 1. Validate Alpha Split (High Priority)
- [ ] Run Q-D benchmark at α=0.3, threshold=0.22
- [ ] Run Q-G benchmark at α=0.8, threshold=0.22
- [ ] Compare against α=0.5 baseline (107/114)
- [ ] If improvement confirmed, proceed to router integration

### 2. Router-Driven Dynamic Alpha
- [ ] Add query classification in router: single-doc-detail vs cross-doc-aggregation
- [ ] Router passes `appnp_alpha` override based on classification
- [ ] Test end-to-end with automatic routing

### 3. Eliminate Redundant Reranker Call
- [ ] Step 3.5 reranks ALL passages → feeds APPNP as predictor
- [ ] Step 4.5 reranks APPNP output AGAIN → redundant when α is high
- [ ] Solution: reuse Step 3.5 scores for Step 4.5 cutoff (skip second API call)
- [ ] Saves ~380ms + one Voyage API call per query

### 4. Update Preset Defaults
- [ ] Update `community_search` preset with validated APPNP config
- [ ] Set `propagation_mode: "appnp"` as default
- [ ] Disable `entity_embedding_seeds` (no impact with APPNP)
- [ ] Document new config params

### 5. Q-G Verbosity (Lower Priority)
- [ ] Q-G2 (2/3), Q-G5 (2/3), Q-G6 (2/3), Q-G7 (2/3), Q-G8 (2/3), Q-G9 (2/3) at threshold=0.22
- [ ] Investigate if synthesis prompt can be tuned for conciseness
- [ ] Consider per-document map-reduce already active — may need tighter per-map instructions

### 6. Section Headings in Context (Low Priority)
- [ ] Headings like "Binding Arbitration." are Sentence nodes with no info content
- [ ] They ARE semantically relevant (answer "what section is this about")
- [ ] Current noise filter removes bare headings <50 chars without punctuation
- [ ] Consider labeling them as `[HEADING]` in LLM context for better reasoning

---

## Benchmark Files

| File | Config | Scores |
|------|--------|--------|
| `r4questions_20260322T181722Z` | Q-D, α=0.5, threshold=0.22 | **56/57 (98.2%)** |
| `r3questions_20260322T182333Z` | Q-G, α=0.5, threshold=0.22 | 51/57 (89.5%) |
| `r4questions_20260322T184525Z` | Q-D, α=0.5, threshold=0.30 | 51/57 (89.5%) |
| `r3questions_20260322T185133Z` | Q-G, α=0.5, threshold=0.30 | **53/57 (93.0%)** |

---

## Key Technical Context

### APPNP Formula
`preds = (1-α) · D^{-½}·A·D^{-½} · preds + α · predictions`
- `predictions` = reranker scores (from Step 3.5)
- Higher α = trust reranker more, propagate less
- Lower α = trust graph structure more, smooth scores

### Why Entity Embedding Seeds Don't Matter
APPNP uses reranker scores as the predictor for ALL passage nodes. Entity seeds only affect the old `run_ppr()` path via personalization vector. With APPNP + `seed_weight=0.0`, the graph walk starts from reranker predictions, not entity seeds.

### Reranker Instruction
`"Find passages that directly answer or provide specific factual details for: "` — prepended to query for rerank-2.5. Reduces noise 50% (e.g., "THANK YOU FOR YOUR BUSINESS!" drops from 0.62→0.26).
