# Handover — 2026-03-21: Retrieval Tuning & Ground Truth Expansion

## Summary

This session focused on achieving **perfect retrieval recall** for the community_search (Route 8) preset by systematically tuning PPR and reranker parameters. We discovered critical gaps in the ground truth test, fixed them, and achieved **49/49 (100%) retrieval recall** at both PPR and reranker stages. The remaining optimization target is **synthesis quality** — the LLM map-reduce prompts produce verbose answers that lose points with the LLM judge.

## Key Discoveries

### 1. Ground Truth Test Was Giving False Confidence
The `scripts/test_ppr_retrieval.py` 40/40 test only checked `ppr_top_passages` (pre-reranking) and used **incomplete ground truth substrings**. For example, Q-G7 checked for `"written noti"` which matched a *different* PMA passage ("written notification within 5 business days") instead of the actual expected passage ("60 days written notice to terminate"). The test passed while the critical passage was missing.

**Fix applied:** Expanded ground truth from 40 → 49 substrings, covering all facts the LLM judge expects. Added post-reranking recall check (`final_passages`) alongside PPR recall.

### 2. PPR top_k=100 Was the Bottleneck, Not Reranker
With 208 sentences in the demo group, `ppr_passage_top_k=100` excluded cross-topic passages. The PMA "60 days written notice to terminate" passage ranked below position 100 for Q-G7 ("notice mechanisms") because it's semantically about termination. Similarly, "not transferable" ranked below 100 for Q-G1 ("termination rules") because it's about transferability.

**Fix:** `ppr_passage_top_k=150` → PPR recall goes from 46/49 → **49/49 (100%)**.

### 3. Reranker Threshold 0.25 Drops 1 Passage, 0.22 Keeps All
With top_k=150, the reranker threshold sweep showed:
- 0.15–0.22: **49/49** reranked recall (all hit dynamic_max=80)
- 0.25: 48/49 (drops "not transferable" — scores between 0.22–0.25)
- 0.30: 47/49 (too aggressive)

**Fix:** `rerank_relevance_threshold=0.22` → Reranked recall **49/49 (100%)**.

### 4. Neural Weight Doesn't Help Cross-Topic Retrieval
Swept `neural_weight` from 0.3 to 0.7 at top_k=100 — no change in the 3 misses. The cross-topic passages are a graph structure limitation, not a neural weight issue.

### 5. Semantic Prefilter Hurts (Don't Enable)
The embedding prefilter (`semantic_prefilter`) has the same cross-topic blind spot as PPR — cosine similarity between "notice mechanisms" and a termination passage is low. Enabling it drops reranked recall from 49/49 to 46-47/49. The Voyage cross-encoder (reranker) is smarter at cross-topic matching.

### 6. Retrieval Is Perfect but Synthesis Is Now the Bottleneck
LLM benchmark scores:
- **v1** (top_k=100, th=0.25, ~40p): 27/30 (90%), 100% pass rate
- **v3** (top_k=150, th=0.22, ~80p): 24/30 (80%), 90% pass rate

More passages → better retrieval recall but **noisier synthesis**. The MAP step extracts too many tangentially related facts from 80 passages, and the REDUCE step doesn't filter tightly enough. Common judge complaints: "too verbose", "misassigns roles", "includes additional clauses not asked for".

### 7. Group ID Resolution Clarified
`X-Group-ID` header value is irrelevant — the `folder_resolver` always routes to `DEMO_GROUP_ID=7e9e0c33-a31e-4b56-8ebf-0fff973f328f` (208 sentences) when no `folder_id` is provided. The `test-5pdfs-v2-enhanced-ex` group has 0 nodes.

## Current Preset State (Committed but Not Pushed)

```python
"community_search": {
    "ppr_passage_top_k": 150,              # was 100 — wider net for cross-topic
    "rerank_relevance_threshold": 0.22,    # was 0.25 — keeps all ground truth
    "rerank_dynamic_cutoff": True,
    "rerank_top_k": 260,
    "rerank_prefilter_k": 120,             # only used by semantic seeds (disabled)
    "community_passage_seeds": False,
    "community_guided_instruction": False,
    "entity_context_inject": False,
    "semantic_passage_seeds": False,
    "neural_weight": 0.5,
    "map_reduce_synthesis": True,
    "section_graph": True,
    "min_chunks_per_doc": 0,
    "max_chunks_per_doc": 0,
}
```

## Files Modified (Uncommitted)

### `src/worker/hybrid_v2/routes/route_8_hipporag2_community.py`
- Preset: `ppr_passage_top_k: 100→150`, `rerank_relevance_threshold: 0.25→0.22`
- Added `rerank_dynamic_min` parameter support (config loading + `_rerank_passages()` signature + filtering logic)
- Note: `dynamic_min` is set to 0 in preset (not actively used) — the threshold change handles it

### `scripts/test_ppr_retrieval.py`
- Expanded ground truth from 40 → 49 substrings covering all LLM judge expected facts
- Added post-reranking recall check (`final_passages`) alongside PPR recall
- Output now shows `PPR=X/Y (Np) | Reranked=X/Y (Np)` per question
- Summary shows both PPR recall and Reranked recall percentages

## Experiment Results Summary

### PPR top_k Sweep (threshold=0.25)
| top_k | PPR Recall | Reranked Recall |
|-------|-----------|-----------------|
| 100   | 46/49 (93.9%) | 46/49 (93.9%) |
| 150   | 49/49 (100%) | 48/49 (98.0%) |

### Reranker Threshold Sweep (top_k=150)
| Threshold | Reranked Recall | Avg Passages |
|-----------|----------------|-------------|
| 0.15 | 49/49 (100%) | 80p (dynamic_max cap) |
| 0.18 | 49/49 (100%) | 80p |
| 0.20 | 49/49 (100%) | 80p |
| 0.22 | 49/49 (100%) | ~80p |
| 0.25 | 48/49 (98%) | 45-80p |
| 0.30 | 47/49 (95.9%) | 13-80p |

### Neural Weight Sweep (top_k=100)
All values 0.3–0.7 → same 46/49 (93.9%). No effect on cross-topic misses.

### Semantic Prefilter (top_k=150, threshold=0.22)
| Prefilter top_n | Reranked Recall |
|----------------|-----------------|
| OFF | 49/49 (100%) |
| 60 | 46/49 (93.9%) |
| 80 | 47/49 (95.9%) |
| 100 | 47/49 (95.9%) |

### LLM Benchmark Scores
| Version | Config | Score | Pass Rate |
|---------|--------|-------|-----------|
| v1 | top_k=100, th=0.25 | 27/30 (90%) | 100% |
| v3 | top_k=150, th=0.22 | 24/30 (80%) | 90% |

v3 improved Q-G5 (2→3) and Q-G7 has all notice mechanisms, but verbosity hurt Q-G4, G6, G9, G10.

## TODO — Next Steps

### 1. Fix Synthesis Verbosity (Primary)
The MAP/REDUCE prompts produce too many off-topic facts when given 80 passages. Options:
- **Tighten REDUCE prompt scope filter** — make instruction #2 more aggressive at discarding tangentially related facts
- **Lower `dynamic_max`** from 80 to ~50-60 — fewer passages = less noise for synthesis
- **Add a passage budget to MAP** — limit extracted facts per document
- **Two-stage REDUCE** — first extract, then prune before final synthesis

### 2. Evaluate dynamic_max Reduction
Test `dynamic_max` at 50 and 60 with the new retrieval settings. This is the simplest lever to reduce synthesis noise while keeping retrieval at 49/49.

### 3. Consider Threshold/Passages Tradeoff
The sweet spot may be:
- `threshold=0.25` (fewer passages, 48/49 recall — only loses "not transferable")
- The 1 recall miss may be acceptable if synthesis quality jumps back to 27-30/30

### 4. Run Multiple Benchmark Iterations
LLM evaluation is stochastic. Run 3x and average to get stable scores before comparing configs.

### 5. Commit and Push
Current changes are uncommitted. Commit after synthesis optimization is validated.

## Server State
Running on port 8888 with:
```bash
ROUTE7_SECTION_EDGE_WEIGHT=0.3 ROUTE7_APPEARS_IN_SECTION=1 ROUTE7_NEXT_IN_SECTION=1
```

## Key Insight
**Retrieval and synthesis quality are inversely correlated at the margin.** Perfect retrieval (49/49) requires ~80 passages, but 80 passages produce noisy synthesis. The optimization frontier is finding the right passage count that maximizes end-to-end answer quality — not just retrieval recall.
