# Handover — 2026-03-24: Overlap Monopartite & Reranker Threshold Analysis

## Summary

Extended analysis of the overlap monopartite PPR improvement for Route 8 (community_search).
Discovered that the post-PPR reranker was disabled (`rerank: False`), meaning all 50 PPR passages
went straight to MAP-REDUCE synthesis with no filtering. Enabled reranker with dynamic cutoff at
threshold 0.25 — the maximum safe value that keeps all 48/48 GT passages.

Began investigating the nature of "noise" in PPR top-50. Initial framing of 76% noise was incorrect —
further analysis needed to determine whether non-GT passages are genuinely useful supporting context
or retrievable noise. **Do not conclude before proper analysis.**

## Key Findings

### 1. Reranker Was Disabled

The community_search preset had `rerank: False`. The `rerank_dynamic_cutoff: True` and
`rerank_relevance_threshold: 0.22` settings were **dead code** — the threshold only applies
when `rerank_enabled and rerank_dynamic_cutoff` (line ~1566).

All 50 PPR passages always went to synthesis regardless of threshold setting.

### 2. GT Reranker Score Floor

Queried all 10 Q-G questions with `rerank=1, t=0.01` to get cross-encoder scores for every
PPR top-50 passage. Found the reranker score for each of the 48 GT passages:

| GT Passage | Score | Query |
|---|---|---|
| **deposit is forfeited (PC)** | **0.279** | Q-G1 (weakest) |
| volumes (HT) | 0.320 | Q-G4 |
| in writing (W) | 0.348 | Q-G7 |
| phone (W) | 0.350 | Q-G7 |
| 3 business days (PC) | 0.350 | Q-G9 |
| $35 (PM) | 0.371 | Q-G3 |
| ... (43 more above 0.37) | | |

**Threshold sweep result:**

| Threshold | GT Recall | Status |
|---|---|---|
| t ≤ 0.25 | 48/48 | ✅ Safe |
| t = 0.28 | 47/48 | ❌ Loses "deposit is forfeited" (PC) |
| t = 0.30 | 47/48 | ❌ Same |
| t = 0.35 | 43/48 | ❌ Loses 5 GT passages |
| t = 0.40 | 39/48 | ❌ |

### 3. Passage Count at t=0.25 (with rerank=1)

| Query | Passages at t=0.22 | Passages at t=0.25 | Cut |
|---|---|---|---|
| Q-G1 | 50 | 46 | -4 |
| Q-G2 | 50 | 48 | -2 |
| Q-G3 | 50 | 42 | -8 |
| Q-G4 | 50 | 43 | -7 |
| Q-G5 | 50 | 50 | 0 |
| Q-G6 | 50 | 50 | 0 |
| Q-G7 | 50 | 40 | -10 |
| Q-G8 | 50 | 47 | -3 |
| Q-G9 | 50 | 45 | -5 |
| Q-G10 | 50 | 50 | 0 |
| **AVG** | **50.0** | **46.1** | **-3.9 (7.8%)** |

### 4. Non-GT Passage Analysis (needs further work)

Scored all 500 PPR passages (120 GT, 380 non-GT):

| | Avg Reranker Score | Count |
|---|---|---|
| GT passages | 0.436 | 120 |
| Non-GT passages | 0.324 | 380 |

- 90% of non-GT score above 0.25
- 50% of non-GT score above 0.30
- Non-GT avg is 74% of GT avg

**Example (Q-G8 — insurance/indemnity question):**
Non-GT passages include warranty exclusions, liability limitations, damage claims —
topically relevant content the LLM may use to synthesize answers. Whether these are
helpful context or dilutive noise needs proper analysis (not assumption).

**⚠️ Do not conclude these are "useful context" or "noise" without evidence.**
Need to test: does cutting them improve or degrade answer quality?

## Uncommitted Change

```diff
# src/worker/hybrid_v2/routes/route_8_hipporag2_community.py (preset)
- "rerank": False,
+ "rerank": True,
- "rerank_relevance_threshold": 0.22,
+ "rerank_relevance_threshold": 0.25,
```

This enables post-PPR reranking with dynamic cutoff at t=0.25. **Not yet committed** —
pending validation that this doesn't hurt synthesis quality.

Note: enabling rerank=True adds a Voyage rerank-2.5 API call per query (~2-3s latency,
token cost). The reranker_gate already calls Voyage pre-PPR, so this is a second rerank call.

## Next Steps

### Immediate
1. **Analyze whether non-GT passages help or hurt synthesis** — this is the open question.
   Suggested approach: run benchmark at t=0.25 (fewer passages) vs t=0.01 (all 50) with
   rerank=1, compare LLM answer quality. If fewer passages = same/better quality, the
   cut passages were noise. If worse, they were useful context.

2. **Consider the cost of double reranking** — reranker_gate (pre-PPR) + rerank (post-PPR)
   means two Voyage API calls. Is the post-PPR rerank worth the latency/cost? Could the
   reranker_gate scores be reused instead of a second call?

3. **Deeper analysis of non-GT passage contribution** — for queries where the LLM answer
   is correct, which passages did it actually cite/use? Are the non-GT passages cited in
   the MAP extraction step?

### Overlap Monopartite (committed, working)
The overlap monopartite changes from prior session are committed (5d7bc9ce) and verified:
- `ROUTE7_MONOPARTITE=1` + `ROUTE7_MONOPARTITE_EDGE_WEIGHT_MODE=overlap`
- 48/48 recall, 20.8% composition change, +3 net GT
- No topK fill needed, no scaler needed

## Files

| File | Status | Description |
|---|---|---|
| `src/worker/hybrid_v2/routes/route_8_hipporag2_community.py` | **Uncommitted** | rerank=True, threshold=0.25 |
| `src/worker/hybrid_v2/retrievers/hipporag2_ppr.py` | Committed | Overlap monopartite (5d7bc9ce) |
| `/tmp/api_mono_results.json` | Temp | Saved overlap mono PPR passages |
| `/tmp/api_baseline_results.json` | Temp | Saved baseline PPR passages |
| `/tmp/test_api_mono.py` | Temp | Full pipeline GT test script |

## Server State

Overlap monopartite server running on port 8888 (PID 770463) with:
- `ROUTE7_MONOPARTITE=1`
- `ROUTE7_MONOPARTITE_EDGE_WEIGHT_MODE=overlap`
- `ROUTE8_RERANK_RELEVANCE_THRESHOLD=0.30` (env var, but code change sets preset to 0.25)
