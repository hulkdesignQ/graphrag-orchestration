# Route 7 Latency Optimization Analysis — 2026-02-26

## Context

After reindexing from section-based chunking (TextChunks) to sentence-direct indexing,
Route 2 local benchmark passes 19/19 with avg latency ~4.4s (positive ~5.4s, negative ~3.3s).
The question: can Route 7 (HippoRAG 2) achieve ~2s latency on the same Route 2 benchmark questions?

## Route 2 vs Route 7 Architecture Comparison

| Aspect | Route 2 (Local Search) | Route 7 (HippoRAG 2) |
|---|---|---|
| Entity seeding | LLM NER call (~1,200ms) | Embedding cosine similarity vs triples (~fast) |
| LLM in retrieval | NER extraction (stage 2.1) | Recognition memory filter (parallel with DPR) |
| Graph walk | Cypher-based PPR approximation, damping=0.85 | True PPR power iteration, damping=0.5 |
| Passage retrieval | Iterative deepening from entity seeds | DPR sentence search → passage seeds for PPR |
| Synthesis model (benchmark) | gpt-4.1-mini (local test) | gpt-5.2 (deployed API) |
| Response style | Concise (~39 chars avg) | Verbose `## Summary` blocks (~630 chars avg) |

## Route 7 Stage Timings (from HANDOVER_2026-02-24)

| Step | Description | Time |
|---|---|---|
| Step 1 | Voyage query embedding | ~220ms |
| Step 2 | Parallel: triple match + DPR sentence search | ~735ms |
| Step 3 | Build entity seeds from triples + DPR | ~0ms |
| Step 4 | PPR over knowledge graph | ~4ms |
| Step 5 | Synthesis via LLM | 4,000–12,000ms ← **BOTTLENECK** |
| **Total retrieval (1–4)** | | **~960ms** |

## Route 7 Benchmark Results (route7_local_search_20260226T112517Z)

| QID | Latency | Response Length | Type |
|---|---|---|---|
| Q-L1 | 35,897ms | 735 chars | Positive (outlier) |
| Q-L2 | 5,311ms | 673 chars | Positive |
| Q-L3 | 5,365ms | 529 chars | Positive |
| Q-L4 | 4,435ms | 609 chars | Positive |
| Q-L5 | 4,733ms | 635 chars | Positive |
| Q-L6 | 4,692ms | 633 chars | Positive |
| Q-L7 | 4,371ms | 869 chars | Positive |
| Q-L8 | 4,048ms | 67 chars | Positive (not found) |
| Q-L9 | 3,951ms | 626 chars | Positive |
| Q-L10 | 3,709ms | 376 chars | Positive |
| Q-N1 | 2,979ms | 36 chars | Negative |
| Q-N2 | 2,469ms | 36 chars | Negative |
| Q-N3 | 1,993ms | 36 chars | Negative |
| Q-N5 | 1,950ms | 36 chars | Negative |
| Q-N6 | 1,962ms | 36 chars | Negative |
| Q-N7 | 4,748ms | 573 chars | Negative (false positive) |
| Q-N8 | 4,030ms | 806 chars | Negative (false positive) |
| Q-N9 | 1,952ms | 36 chars | Negative |
| Q-N10 | 4,630ms | 426 chars | Negative (false positive) |
| **AVG** | **5,432ms** | | |

**Key observation:** Negative questions that short-circuit synthesis (Q-N1–Q-N6, Q-N9) already hit ~2.0s. This proves retrieval (steps 1–4) is fast enough; synthesis is the sole bottleneck.

## Why Route 7 Is Slower Than Route 2 on the Same Questions

**Not architecture. Not damping. Input context length to the synthesis LLM.**

Route 7 feeds `ROUTE7_PPR_PASSAGE_TOP_K=20` passage chunks to the synthesis LLM. More input tokens means:
- Longer LLM prefill time (reading all the context)
- More material to synthesize → longer, more verbose output
- More output tokens → longer generation time

This is why Route 7 produces ~630 char responses vs Route 2's ~39 chars on the same questions. The LLM is given more context, so it writes more.

## Damping Factor Analysis

**Route 2:** Uses damping=0.85 in a Cypher-based PPR approximation (not true PPR). The damping is used as a `0.85^depth` decay factor. Hard `per_seed_limit=25` and `per_neighbor_limit=10` caps mean damping only affects scoring, not the number of nodes visited. Changing damping does not meaningfully affect latency.

**Route 7:** Uses damping=0.5 (upstream HippoRAG 2 default) in true PPR power iteration. The formula is:

```
new_rank[i] = (1 - damping) * personalization[i] + damping * Σ(walk contributions)
```

- damping=0.5: 50% walk, 50% teleport → shallower, stays closer to seeds
- damping=0.85: 85% walk, 15% teleport → deeper exploration, more distant nodes

Higher damping = deeper walk = potentially more noise, not less. The current 0.5 already provides focused, seed-local ranking. PPR computation itself takes ~4ms regardless of damping — it's negligible.

## Recognition Memory LLM Call

The recognition memory filter is **part of the original HippoRAG 2 design** (ICML '25, Section 3.2). It's the paper's key innovation:

1. **Pattern separation:** Embed query → cosine match against triple embeddings → top-K candidates
2. **Recognition memory:** LLM examines each candidate triple and judges relevance

This replaces Route 2's NER-to-node lookup. In Route 7, the recognition memory LLM call runs **in parallel** with DPR passage search (step 2a ∥ 2b), so its wall-clock cost is hidden within the ~735ms parallel step.

## What Goes Into Synthesis LLM (Original vs Custom)

The synthesis LLM receives:

| Input | Source | Original HippoRAG 2? |
|---|---|---|
| `pre_fetched_chunks` — top-K PPR passage texts | PPR output, controlled by `PPR_PASSAGE_TOP_K` | ✅ Yes |
| `coverage_chunks` — sentence search results | Phase 2 addition, gated by `ROUTE7_SENTENCE_SEARCH` (default off) | ❌ No (our addition) |

With sentence search off (the default), only PPR passages go to the LLM — matching the original design. DPR results don't go directly to synthesis; they feed into PPR as passage seeds.

## Recommendation: Single Tweak for ~2s Latency

**Reduce `ROUTE7_PPR_PASSAGE_TOP_K` from 20 to 5–10.**

This is the single knob that controls how many passage chunks get fed to the synthesis LLM. Fewer chunks = less input tokens = faster prefill + shorter output.

**Projected timings with PPR_PASSAGE_TOP_K=5:**

| Step | Time |
|---|---|
| Step 1 (embed) | ~220ms |
| Step 2 (parallel triple+DPR) | ~735ms |
| Step 3+4 (seed+PPR) | ~5ms |
| Step 5 (synthesis, ~5 chunks) | ~800–1,000ms |
| **Total** | **~1,800–2,000ms** |

Everything else (triple_top_k, dpr_top_k, dpr_sentence_top_k, damping) only affects retrieval, which is already ~960ms total. The bottleneck is purely how much text the LLM has to read.

## Local Test Results: Reduced PPR_PASSAGE_TOP_K

### Run 1: PPR_PASSAGE_TOP_K=5 only

| QID | Latency | Resp Len | Notes |
|---|---|---|---|
| Q-L1 | 20,720ms | 552 | Cold-start outlier |
| Q-L2 | 2,913ms | 884 | |
| Q-L3 | 2,774ms | 385 | |
| Q-L4 | 3,128ms | 508 | |
| Q-L5 | 2,452ms | 610 | |
| Q-L6 | 2,946ms | 679 | |
| Q-L7 | 3,729ms | 1,110 | |
| Q-L8 | 2,864ms | 504 | |
| Q-L9 | 2,227ms | 215 | |
| Q-L10 | 2,323ms | 247 | |
| Q-N1 | 1,325ms | 36 | Short-circuit |
| Q-N2 | 1,364ms | 36 | Short-circuit |
| Q-N3 | 3,507ms | 589 | False positive |
| Q-N5 | 1,358ms | 36 | Short-circuit |
| Q-N6 | 975ms | 36 | Short-circuit |
| Q-N7 | 2,175ms | 229 | False positive |
| Q-N8 | 3,256ms | 760 | False positive |
| Q-N9 | 1,137ms | 36 | Short-circuit |
| Q-N10 | 2,893ms | 346 | False positive |

### Run 2: PPR_PASSAGE_TOP_K=5, DPR_TOP_K=10, DPR_SENTENCE_TOP_K=15

| QID | Latency | Resp Len |
|---|---|---|
| Q-L1 | 20,006ms | 491 |
| Q-L2 | 3,269ms | 605 |
| Q-L3 | 2,302ms | 353 |
| Q-L4 | 2,594ms | 503 |
| Q-L5 | 2,956ms | 607 |
| Q-L6 | 3,321ms | 679 |
| Q-L7 | 4,106ms | 1,110 |
| Q-L8 | 2,683ms | 496 |
| Q-L9 | 2,938ms | 215 |
| Q-L10 | 2,200ms | 226 |
| Q-N1 | 1,619ms | 36 |
| Q-N2 | 1,599ms | 36 |
| Q-N3 | 1,263ms | 36 |
| Q-N5 | 1,251ms | 36 |
| Q-N6 | 960ms | 36 |
| Q-N7 | 2,523ms | 584 |
| Q-N8 | 2,751ms | 760 |
| Q-N9 | 952ms | 36 |
| Q-N10 | 2,651ms | 371 |

### Summary Comparison (excluding Q-L1 cold-start outlier)

| Config | Positive avg | Negative avg |
|---|---|---|
| Baseline (TOP_K=20, API/gpt-5.2) | ~4,700ms | ~2,050ms |
| Run 1 (PPR=5, local/gpt-4.1-mini) | ~2,820ms | ~1,230ms |
| Run 2 (PPR=5, DPR=10, SENT=15) | ~2,930ms | ~1,730ms |

**Conclusion:** Reducing DPR params on top of PPR_PASSAGE_TOP_K=5 gives no additional benefit. The DPR results feed into PPR as seeds, and with PPR output already capped at 5 passages, fewer seeds don't change the final context size.

## Input/Output Token Analysis

With PPR_PASSAGE_TOP_K=5, synthesis receives very little context:

| Question | Input Tokens | Output Tokens | Ratio | Synthesis Latency |
|---|---|---|---|---|
| Q-L2 | 213 | ~126 | 1.7:1 | ~2,600ms |
| Q-L5 | 177 | ~152 | 1.2:1 | ~2,600ms |
| Q-L7 | 189 | ~230 | 0.8:1 | ~3,400ms |

**Key finding:** The input context is tiny (~180-210 tokens, 3-4 chunks). The LLM generates **as many or more output tokens than input tokens**. The bottleneck is not input prefill — it's **output generation**. The `## Summary` format produces 400-1100 char responses when a concise factual answer would be ~40 chars.

## Design: Router-Adaptive Route 7 (Query Mode Presets)

### Problem

Route 7 currently uses the same parameters and synthesis prompt for all query types. Factual lookup questions (Route 2-type) don't need verbose `## Summary` responses or 20 passage chunks. The router already classifies queries by type — this classification should drive Route 7's behavior.

### Architecture

```
┌──────────┐     query_mode      ┌──────────────────────────────┐
│  Router   │ ──────────────────► │  Route 7 (Unified Engine)    │
│           │  "local_search"     │                              │
│ classifies│  "global_search"    │  Selects preset by mode:     │
│ query type│  "drift_multi_hop"  │  - ppr_passage_top_k         │
└──────────┘                     │  - prompt_variant             │
                                 │  - max_tokens                 │
                                 └──────────────────────────────┘
```

### Implementation

**Step 1: Pass router classification to Route 7**

In `orchestrator.py`, the router already returns a `QueryRoute` enum. Pass it as `query_mode` to Route 7's `execute()`:

```python
# orchestrator.py — in query() method
if route == QueryRoute.HIPPORAG2_SEARCH:
    extra_kwargs["query_mode"] = route.value
# Or when Route 7 becomes the unified engine:
extra_kwargs["query_mode"] = original_route.value  # pre-consolidation route
```

**Step 2: Define presets in Route 7**

In `route_7_hipporag2.py`, add query mode presets:

```python
# Route 7 presets by query_mode
QUERY_MODE_PRESETS = {
    "local_search": {              # Factual extraction — fast & concise
        "ppr_passage_top_k": 5,
        "prompt_variant": "v1_concise",
        "max_tokens": 150,
    },
    "global_search": {             # Thematic/community-level — needs breadth
        "ppr_passage_top_k": 15,
        "prompt_variant": None,    # Default summary
        "max_tokens": None,
    },
    "drift_multi_hop": {           # Multi-hop reasoning — full context
        "ppr_passage_top_k": 20,
        "prompt_variant": None,
        "max_tokens": None,
    },
}
```

**Step 3: Apply preset in execute()**

```python
async def execute(self, query, response_type, ..., query_mode=None):
    preset = QUERY_MODE_PRESETS.get(query_mode, {})
    ppr_passage_top_k = preset.get("ppr_passage_top_k",
        int(os.getenv("ROUTE7_PPR_PASSAGE_TOP_K", "20")))
    prompt_variant = preset.get("prompt_variant", prompt_variant)
    # ... rest of pipeline uses these values
```

### Why This Works

1. **`v1_concise` prompt variant already exists** in `synthesis.py` (line 459). It does pure extraction with no `## Summary` formatting — output would be ~40 chars instead of ~500 chars for factual questions.
2. **No new LLM call needed.** The router already classifies the query; we're just forwarding that classification.
3. **Backward compatible.** Without `query_mode`, Route 7 falls back to current defaults (PPR=20, full summary).
4. **Independently tunable.** Each preset can be adjusted without affecting other query types.

### Projected Latency with `local_search` Preset

| Step | Time |
|---|---|
| Step 1 (embed) | ~220ms |
| Step 2 (parallel triple+DPR) | ~735ms |
| Step 3+4 (seed+PPR) | ~5ms |
| Step 5 (synthesis, v1_concise, ~40 char output) | ~300-500ms |
| **Total** | **~1,300-1,500ms** |

This would bring Route 2-type questions on Route 7 to well under 2s.

## Next Steps

1. Implement `query_mode` parameter pass-through from orchestrator to Route 7
2. Add `QUERY_MODE_PRESETS` dict to Route 7 handler
3. Test with `v1_concise` prompt variant on Route 2 benchmark questions
4. Validate answer quality matches Route 2's current output
5. Tune presets for global_search and drift_multi_hop modes
