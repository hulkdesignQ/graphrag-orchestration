# Handover: Dynamic Cutoff Fix & Reranker Analysis
**Date:** 2026-03-20  
**Branch:** `main` (commit `538c5bbc`)  
**Prior commits on `fix/git-flow-cleanup`:** `518bf202`, `bb4e3be2`, `35ee47e1`, `662e45c4`, `b1e353ff`, `26f0b334`

---

## Summary

This session accomplished three things:
1. **Proved the reranker's value is reordering, not filtering** — it promotes relevant passages by avg 7.6 ranks
2. **Fixed the broken dynamic cutoff pipeline** — two bugs prevented it from ever filtering passages
3. **Cleaned the `community_search` preset** — disabled redundant community seed injection (Neural PPR achieves 100% recall without it)

---

## Key Findings

### Reranker Impact (Voyage rerank-2.5)
- The reranker **actively reorders** all passages — zero stay in the same position
- Net effect: **promotes** relevant passages (mean Δ = -7.6 ranks upward)
- Biggest wins: passages at PPR rank 30-50 pulled to top 5-15
- PPR top-1 often demoted — reranker disagrees with PPR's top pick in most questions
- **Reranker adds zero value for retrieval recall** (40/40 with and without)
- **Reranker adds clear value for synthesis quality** — better-ordered context → more focused LLM output

### Dynamic Cutoff Bugs Found & Fixed
Two bugs prevented the reranker's dynamic cutoff from ever working:

1. **`dynamic_max=80` capped Voyage response** — only top 80 scores were returned, all scoring > 0.24, so no threshold could filter. **Fix:** when dynamic cutoff is active, request ALL candidates from Voyage so low-scoring passages are visible.

2. **Doc interleaving overrode cutoff result** — `passage_limit` was always reset to `ppr_passage_top_k` (line 1231), discarding whatever the dynamic cutoff decided. Then `max_chunks_per_doc` interleaving further replaced the passage list. **Fix:** respect reranker's output length when dynamic cutoff is active; skip doc interleaving when dynamic cutoff handles selection.

### Preset Config Loading Bugs
- `community_passage_seeds` default was hardcoded to `"1"` — preset value `False` was ignored
- `rerank_relevance_threshold` default was hardcoded to `"0.15"` — preset value was ignored
- Both now read from preset via `preset.get()`

### Community Seed Injection Unnecessary
- Neural PPR achieves **40/40 (100%) retrieval recall** without community passage seeds
- Community seeds added ~30-40 extra passages per query but didn't improve recall
- Disabling them reduces reranker token usage and latency

---

## Threshold Sweep Results (Seeds OFF)

| Threshold | Avg Passages | Total Facts | Avg Latency |
|:---------:|:---:|:---:|:---:|
| 0.15 | 50 | 323 | 29.0s |
| 0.20 | 46 | **332** | 27.9s |
| **0.25** | **36** | 289 | 26.5s |
| 0.30 | 27 | 260 | 27.9s |
| 0.35 | 19 | 216 | 21.0s |

**Selected: 0.25** — best balance of passage count and fact extraction.

---

## Current `community_search` Preset

```python
"community_search": {
    "ppr_passage_top_k": 100,
    "community_passage_seeds": False,     # Neural PPR achieves 100% recall
    "community_guided_instruction": True,  # guide reranker with community summaries
    "rerank_dynamic_cutoff": True,         # let reranker score decide survival
    "rerank_relevance_threshold": 0.25,    # natural breakpoint
    "rerank_top_k": 260,                   # Voyage scores all, threshold filters
    "min_chunks_per_doc": 0,               # disabled — dynamic cutoff handles selection
    "max_chunks_per_doc": 0,               # disabled — dynamic cutoff handles selection
    "map_reduce_synthesis": True,
    "section_graph": True,
}
```

---

## Files Modified

- **`src/worker/hybrid_v2/routes/route_8_hipporag2_community.py`**
  - `community_search` preset: seeds off, dynamic cutoff on, threshold 0.25
  - `_rerank_passages()`: request all candidates when dynamic cutoff active (line ~3128)
  - `passage_limit`: respect reranker output when dynamic cutoff active (line ~1237)
  - Doc interleaving: skip when dynamic cutoff + rerank active (line ~1298)
  - Config loading: `community_passage_seeds` and `rerank_relevance_threshold` read from preset
  - Added `final_passages` metadata field (post-reranker ordering)

---

## Server State
Running on port 8888 with:
```bash
ROUTE7_SECTION_EDGE_WEIGHT=0.3 ROUTE7_APPEARS_IN_SECTION=1 ROUTE7_NEXT_IN_SECTION=1 \
ROUTE7_NEURAL_WEIGHT=0.5 ROUTE7_RERANK_PREFILTER_K=120
```

---

## TODO — Continue Next Session

### Immediate
- [ ] **Voyage score distribution varies per query** — Q-G8 (dispute resolution) keeps 49/50 passages even at threshold 0.25 because all passages score uniformly high. Consider adaptive threshold (e.g., keep top N% or use score gap detection instead of fixed threshold)
- [ ] **LLM answer quality comparison** — we measured fact counts but haven't done LLM-judged quality evaluation. Need to compare answer correctness/completeness between old preset (seeds ON, interleave max5) vs new preset (seeds OFF, dynamic cutoff 0.25)
- [ ] **Verify `max_chunks_per_doc` and `min_chunks_per_doc` at 0 doesn't break non-community presets** — other presets (default, precision) may rely on these defaults

### Production Defaults to Evaluate
- [ ] **Set `neural_weight=0.5` as community_search preset default** — currently requires env var override
- [ ] **Set `semantic_seed_top_k=0` as default** — Neural PPR supersedes cross-encoder seeding
- [ ] **Set `rerank_prefilter_k=120` as default** — reduces reranker token cost
- [ ] **Evaluate rerank=0 for non-community queries** — PPR ranking is already excellent

### Adaptive Threshold (Research)
- [ ] **Score gap detection** — instead of fixed 0.25, find the largest score gap in Voyage output and cut there (natural breakpoint varies: rank 23 for Q-G1, but rank 49 for Q-G8)
- [ ] **Percentile-based cutoff** — keep top 30% of scores instead of absolute threshold
- [ ] **Per-query calibration** — use the score distribution shape to determine cutoff

### Pipeline Cleanup
- [ ] **Merge `fix/git-flow-cleanup` branch** commits into main (6 commits for LLM splitter, ground truth fixes, production hardening)
- [ ] **Remove `final_passages` metadata** if not needed in production (adds ~2KB per response)
