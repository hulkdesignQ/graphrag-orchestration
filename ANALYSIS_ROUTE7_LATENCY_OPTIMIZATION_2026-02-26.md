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

## Next Steps

1. Run Route 7 benchmark with `ROUTE7_PPR_PASSAGE_TOP_K=5` to validate latency improvement
2. Evaluate answer quality at reduced context — ensure precision doesn't drop
3. If quality drops, try `PPR_PASSAGE_TOP_K=10` as a middle ground
4. Consider whether the Route 7 benchmark should use gpt-4.1-mini (matching Route 2 local test) for apples-to-apples comparison
