# Handover: Route 7 Rerank Top-K Improvement — 2026-02-26

**Date:** 2026-02-26  
**Status:** rerank_top_k=30 implemented and benchmarked locally  
**Previous best:** 55/57 (96.5%) — `route7_hipporag2_r4questions_20260226T215559Z`  
**New score:** 56/57 (98.2%) — `route7_hipporag2_r4questions_20260226T222346Z`  
**Commit base:** `5562a18 feat(route7): v7.2 all-sentence parallel reranker architecture`

---

## 1. Change Made

**Single change:** Increased `ROUTE7_RERANK_TOP_K` default from 20 → 30.

**File:** `src/worker/hybrid_v2/routes/route_7_hipporag2.py`

Three edits:
1. **Line 282:** `ROUTE7_RERANK_TOP_K` env default `"20"` → `"30"`
2. **Line 519:** When reranker is active, use its full output (`len(rerank_all_results)`) instead of capping at `ppr_passage_top_k=20` — otherwise the extra 10 reranked passages would be discarded
3. **Line 717:** Diagnostics `num_ppr_passages` now references `top_passage_scores` (already computed) instead of re-slicing

**No other parameters were changed.** `ROUTE7_DPR_TOP_K`, `ROUTE7_PPR_PASSAGE_TOP_K`, `ppr_passage_top_k` presets, and function signature defaults all remain at their original values.

---

## 2. Benchmark Comparison

### Score Improvement

| Benchmark | Score | Q-D3 | Q-D5 | Q-D10 |
|---|---|---|---|---|
| Previous (`215559Z`, rerank_top_k=20) | 55/57 (96.5%) | 2/3 | 2/3 | 3/3 |
| New (`222346Z`, rerank_top_k=30) | 56/57 (98.2%) | 3/3 | 3/3 | 2/3 |

Net: +1 point. Q-D3 and Q-D5 improved; Q-D10 dropped (see §3 for root cause).

### Passage Retrieval Comparison

| QID | Prev PPR passages | New PPR passages | Prev chunks used | New chunks used |
|---|---|---|---|---|
| Q-D1 | 20 | 30 | 15 | 21 |
| Q-D3 | 20 | 30 | 19 | 24 |
| Q-D4 | 20 | 30 | 17 | 25 |
| Q-D8 | 20 | 30 | 15 | 23 |
| Q-D10 | 20 | 30 | 17 | 22 |

All questions now retrieve 30 PPR passages (up from 20), with 19–25 chunks reaching synthesis (up from 12–19).

---

## 3. Remaining Gap: Q-D10 (2/3) — Retrieval Miss

**Query:** "List the three different 'risk allocation' statements across the set (risk of loss, liability limitations, non-transferability)."

**Expected detail missed:** *"warranty terminates if first purchaser sells or moves out"*

**Root cause: Retrieval gap, not LLM variance.**

- **sent_37** (retrieved ✅): *"This limited warranty is extended to the Buyer/Owner as the first purchaser of the home and is not transferable."*
- **sent_38** (NOT retrieved ❌): *"In the event the first purchaser sells the home or moves out of it, this limited warranty automatically terminates."*

sent_38 is the sentence immediately following sent_37 in the warranty document. The reranker scores each sentence independently and sent_38 doesn't rank in the top 30 because it uses different vocabulary ("sells the home", "moves out", "terminates") than the query ("risk allocation", "non-transferability").

**This is a single-sentence chunking limitation.** Adjacent sentences that form a logical unit (transferability + termination consequence) are scored independently, and the second half may fall below the reranker cutoff.

**Potential fixes:**
- Sentence window expansion: when a sentence is retrieved, also include its immediate neighbors (±1 sentence)
- Further increase `rerank_top_k` (e.g., 40 or 50) to catch more borderline sentences
- Composite chunking: merge adjacent short sentences into logical units during indexing

---

## 4. TODO List — Route 7 Improvement Plan

### Immediate (Code Change Ready)

- [ ] **Commit & deploy rerank_top_k=30** — Push the current working tree change and redeploy to Azure. Validate 56/57 on cloud.

### High Priority — Upstream Alignment (from Gap Analysis)

- [ ] **OpenIE triple extraction at indexing time** — Currently, Route 7 relies on entity-relationship triples extracted by the LlamaIndex-based pipeline during indexing. Upstream HippoRAG 2 uses explicit OpenIE-style triple extraction (`subject predicate object`) with dedicated fact embeddings, enabling query-to-fact cosine matching. Implementing a dedicated OpenIE extraction step during indexing would:
  - Produce higher-quality triples with explicit predicates
  - Enable fact-level embedding storage (separate from entity embeddings)
  - Align with upstream's `fact_embedding_store` architecture
  - **File:** `src/worker/hybrid_v2/indexing/dual_index.py` (has `_extract_triples()` stub)

- [ ] **Seed ALL passages (Gap 1)** — Currently only top-20 DPR hits are seeded as passage nodes in PPR. Upstream seeds ALL passages with `similarity × passage_node_weight`. This ensures every document has a non-zero teleport probability, enabling cross-document discovery. Options:
  - Seed top-200 DPR hits (approximation)
  - Pre-compute all passage similarities in batch
  - **File:** `route_7_hipporag2.py` lines 446–454

- [ ] **Use raw fact scores for entity seeds (Gap 2)** — Currently, each surviving triple adds +1.0 to entity seeds, then normalised to sum=1.0. This discards relevance (0.9 vs 0.3 cosine) and IDF signals. Upstream uses `fact_score / entity_doc_frequency`. Fix: pass cosine scores through from `TripleEmbeddingStore.search()`.
  - **File:** `route_7_hipporag2.py` lines 414–416

### Medium Priority — Retrieval Quality

- [ ] **Sentence window expansion** — When a sentence is retrieved, also fetch ±1 adjacent sentences to capture logical continuations (e.g., sent_37 + sent_38 for Q-D10). This is a common RAG pattern ("small-to-big" with sentence windows).
  - **File:** `route_7_hipporag2.py` `_fetch_chunks_by_ids()`

- [ ] **Increase PPR passage top-K (Gap 3)** — Upstream uses `retrieval_top_k=200`, Route 7 uses 20. Even with reranker at 30, PPR output is capped at 20. Consider raising `ROUTE7_PPR_PASSAGE_TOP_K` to 50–100 for better coverage when reranker is disabled.
  - **File:** `route_7_hipporag2.py` line 277

### Low Priority — Ablation & Validation

- [ ] **Damping factor ablation (Gap 5)** — α=0.5 is upstream default, but small corpus may benefit from α=0.7 for deeper exploration. Run benchmark sweep {0.5, 0.7, 0.85}.

- [ ] **Verify RELATED_TO edge weights match upstream (Gap 4)** — Downstream of OpenIE implementation. Check co-occurrence weighting semantics.

---

## 5. Benchmark History

| File | Score | Config | Notes |
|---|---|---|---|
| `r3questions_20260222T122103Z` | 50/57 | Pre-merge baseline | |
| `r3questions_20260223T080528Z` | 53/57 | Pre-merge | |
| `r3questions_20260224T125539Z` | 55/57 | 18 chunks | Best score before reranker |
| `r3questions_20260224T141339Z` | 55/57 | 13 chunks | Post-merge baseline |
| `r4questions_20260226T215559Z` | 55/57 | rerank_top_k=20, v7.2 reranker | Reranker architecture baseline |
| **`r4questions_20260226T222346Z`** | **56/57** | **rerank_top_k=30, v7.2 reranker** | **Current best** |

---

## 6. Files Reference

| File | Role |
|---|---|
| `src/worker/hybrid_v2/routes/route_7_hipporag2.py` | Main Route 7 handler — seeding, PPR, synthesis |
| `src/worker/hybrid_v2/retrievers/hipporag2_ppr.py` | PPR engine — graph loading, power iteration |
| `src/worker/hybrid_v2/retrievers/triple_store.py` | Triple embedding store + recognition memory |
| `src/worker/hybrid_v2/indexing/dual_index.py` | Indexing pipeline (triple extraction stub) |
| `scripts/benchmark_route7_hipporag2.py` | Benchmark harness |
| `scripts/evaluate_route4_reasoning.py` | LLM-as-judge evaluation |
| `HANDOVER_2026-02-25_ROUTE7_UPSTREAM_GAP_ANALYSIS.md` | Detailed upstream comparison |
| `ANALYSIS_ROUTE7_LATENCY_OPTIMIZATION_2026-02-26.md` | Latency analysis & query-mode presets |
