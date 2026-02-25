# Handover: Route 7 HippoRAG 2 — Upstream Gap Analysis

**Date:** 2026-02-25  
**Status:** Investigation complete, fixes not yet implemented  
**Current score:** 55/57 (best), 52-53/57 (typical with latency-optimised settings)  
**Failing question:** Q-D3 (cross-document timeframe comparison) — consistently fails

---

## 1. Root Issue: Q-D3 Cross-Document Retrieval Failure

**Query:** `Compare "time windows" across the set: list all explicit day-based timeframes.`  
**Expected:** 4 documents (WARRANTY, HOLDING TANK, PROPERTY MANAGEMENT, PURCHASE CONTRACT)  
**Actual:** Only 2 documents retrieved in every run

| Benchmark | Docs Retrieved | PPR Passages |
|---|---|---|
| `...170527Z` | WARRANTY + PROPERTY MGMT | 20 |
| `...180926Z` | WARRANTY + HOLDING TANK | 12 |
| `...182224Z` | WARRANTY + HOLDING TANK | 12 |

The failure is deterministic — same 3 surviving triples every run:
1. `Limited Warranty HAS sixty (60) days`
2. `repair or replace TIME sixty (60) days`
3. `coverage terms HAS one year or sixty days after commencement`

All triples point to WARRANTY entities only. Property Management and Purchase Contract are never seeded.

---

## 2. Upstream Comparison: Architectural Deviations Found

We compared Route 7 against the reference implementation at
[OSU-NLP-Group/HippoRAG](https://github.com/OSU-NLP-Group/HippoRAG) (`src/hipporag/HippoRAG.py` + `src/hipporag/utils/config_utils.py`).

### 2.1 Parameters That Match Upstream

| Parameter | Upstream | Route 7 | Status |
|---|---|---|---|
| `passage_node_weight` (MENTIONS edge weight) | 0.05 | 0.05 | ✅ Match |
| `damping` (α — PPR damping/teleport factor) | 0.5 | 0.5 | ✅ Match |
| `linking_top_k` / `triple_top_k` | 5 | 5 | ✅ Match |
| `synonymy_edge_sim_threshold` | 0.8 | 0.8 | ✅ Match |
| `is_directed_graph` | False | False | ✅ Match |
| Graph: RELATED_TO edge weight | `r.weight` (default 1.0) | `r.weight` (default 1.0) | ✅ Match |
| Graph: SEMANTICALLY_SIMILAR edge weight | `similarity` | `similarity` | ✅ Match |
| PPR convergence | igraph `prpack` | Custom power iteration, L1 threshold 1e-6 | ✅ Equivalent |

### 2.2 Significant Deviations

#### Gap 1: Passage Seeding — Top-20 DPR vs ALL Passages (CRITICAL)

| Aspect | Upstream | Route 7 |
|---|---|---|
| Which passages seeded | **ALL** passages in corpus | **Top-20** DPR hits only |
| Seed weight per passage | `embedding_sim × 0.05` | `(score / Σscores) × 0.05` |
| Collective passage share | ~60-70% of seed vector | ~4.8% of seed vector |

**Upstream** (`HippoRAG.py`): Every passage node in the graph gets a non-zero seed weight (`similarity_to_query × passage_node_weight`). This ensures PPR has a teleport path to every document, enabling cross-document discovery.

**Route 7** (`route_7_hipporag2.py` line 376-382): Only the top-20 DPR sentence hits are seeded. Documents without a top-20 hit have **zero** seed probability. PPR can only reach them through entity graph traversal, which is heavily attenuated by the 0.05 MENTIONS edge weight.

#### Gap 2: Entity Seed Scale — Normalized vs Raw (CRITICAL)

| Aspect | Upstream | Route 7 |
|---|---|---|
| Phrase/entity seed values | Raw cosine similarity scores (~0.3-0.8 each) | Accumulate +1.0 per triple, then normalise to sum=1.0 |
| Relative entity:passage ratio | ~30:70 (passages dominate due to corpus-wide seeding) | ~95:5 (entities dominate) |

**Route 7** normalises entity seeds to sum=1.0 (line 371-374), then passage seeds to sum=0.05 (line 382). After PPR re-normalises the combined personalization vector, entities hold **95.2%** and all 20 passages share **4.8%**. The random walk is trapped in entity-space.

#### Gap 3: retrieval_top_k — 200 vs 20

| Aspect | Upstream | Route 7 |
|---|---|---|
| `retrieval_top_k` | **200** | **20** (`ROUTE7_PPR_PASSAGE_TOP_K`) |

Upstream considers top-200 passages from PPR for downstream QA. Route 7 only takes top-20. Even if PPR discovered passages from 4+ documents, the top-20 cutoff may exclude lower-ranked documents.

#### Gap 4: Fact/Triple Nodes in PPR Graph — Present vs Absent

| Aspect | Upstream | Route 7 |
|---|---|---|
| `graph_type` | `facts_and_sim_passage_node_unidirectional` | Entity + Sentence only |
| Fact nodes in graph | **Yes** — triples are graph nodes with edges | **No** — triples used for seed selection only |

**What are fact nodes?** In the upstream HippoRAG 2 codebase, "facts" are the extracted OpenIE triples (subject, predicate, object). They are **not** the same as entity nodes — they are a separate node type that represents the *relationship* itself.

**Upstream graph structure (`HippoRAG.py:add_fact_edges`, `add_passage_edges`, `augment_graph`):**
- **Entity nodes** (phrase nodes): One per unique entity name (e.g. "Fabrikam Inc.")
- **Passage nodes**: One per chunk/passage (equivalent to our Sentence nodes)
- **Fact nodes**: One per unique extracted triple (stored in `fact_embedding_store`)
  - Each fact is embedded as a triple text string: `"subject predicate object"`
  - Facts have their own embedding store and are used for query-to-fact similarity scoring

**How fact nodes participate in seeding (`graph_search_with_fact_entities`):**
1. At query time, the query embedding is compared against ALL fact embeddings (`query_fact_scores = dot(fact_embeddings, query_embedding)`)
2. Top-K facts are selected and optionally reranked (recognition memory)
3. For each surviving fact, its subject and object entities receive seed weight = `fact_score / num_chunks_entity_appears_in`
4. This weighted score is assigned to the entity's vertex index in the PPR graph

**Key difference from Route 7:** Upstream uses the fact_score (a cosine similarity, 0-1 range) divided by the entity's document frequency as the entity seed weight. Route 7 uses a simple +1.0 accumulator and then normalises to sum=1.0, which:
- Loses the relevance signal (a 0.9-scoring fact and a 0.3-scoring fact contribute equally)
- Loses the IDF signal (entities appearing in many docs get the same weight as rare entities)
- Forces the entity sum to 1.0, dominating the passage seeds (see Gap 2)

**Fact nodes in the graph itself:** Although fact nodes are tracked separately (`fact_node_keys`, `fact_embedding_store`), in the **default** graph type (`facts_and_sim_passage_node_unidirectional`), the edges from facts are added as **entity-to-entity** edges with weight based on co-occurrence count (via `add_fact_edges`). The fact nodes themselves are NOT separate graph vertices in the PPR walk — rather, their extracted entity pairs create weighted entity-entity edges. Route 7's RELATED_TO edges serve the same purpose, so this particular aspect is approximately equivalent. The main gap is in the **seeding logic** (raw fact scores vs normalised counts), not in the graph topology.

### 2.3 Route 7-Only Parameters (No Upstream Equivalent)

| Parameter | Default | Purpose |
|---|---|---|
| `ROUTE7_DPR_TOP_K` | 20 | Sentence-level DPR passage count |
| `ROUTE7_DPR_SENTENCE_TOP_K` | 60 | Vector search candidate pool before DPR top-K |
| `ROUTE7_STRUCTURAL_SEEDS` | off | Tier 2 structural seeds (section matching) |
| `ROUTE7_COMMUNITY_SEEDS` | off | Tier 3 community seeds |
| `ROUTE7_SENTENCE_SEARCH` | off | Parallel sentence vector search |
| `ROUTE7_SECTION_GRAPH` | off | Include Section nodes in PPR graph |
| `ROUTE7_ENTITY_DOC_MAP` | on | Entity exhaustive enumeration for listing queries |
| `ROUTE7_W_STRUCTURAL` | 0.2 | Structural seed weight |
| `ROUTE7_W_COMMUNITY` | 0.1 | Community seed weight |
| `ROUTE7_SENTENCE_TOP_K` | 30 | Sentence search result count |
| `ROUTE7_SENTENCE_THRESHOLD` | 0.2 | Sentence search score threshold |

---

## 3. Why Passage Nodes Can't Bridge Documents (Quantified)

With the current implementation:

1. **Seed imbalance**: Entity seeds hold 95% of personalization, passages hold 5%.
2. **Edge weight asymmetry**: At a typical entity node (3 RELATED_TO + 2 SIMILAR + 10 MENTIONS), the walker has 90% probability of staying in entity-space, 10% of stepping to any passage. Per-passage probability: ~1%.
3. **Cross-document bridge path** requires 2 MENTIONS hops: `Passage_DocA →(0.05)→ Entity →(0.05)→ Passage_DocB`. Net attenuation: 0.05² = 0.25%.
4. **Damping α=0.5** means 50% of rank teleports back to the entity-dominated seed vector each iteration, preventing long-distance exploration.

Result: Passage nodes from unseeded documents receive near-zero PPR score.

---

## 4. Benchmark History

| File | Score | Notes |
|---|---|---|
| `route7_hipporag2_r3questions_20260222T122103Z.json` | 50/57 | Pre-merge baseline |
| `route7_hipporag2_r3questions_20260223T080528Z.json` | 53/57 | Pre-merge |
| `route7_hipporag2_r3questions_20260224T125539Z.json` | 55/57 | Best score, 18 chunks |
| `route7_hipporag2_r3questions_20260224T141339Z.json` | 55/57 | Post-merge baseline, 13 chunks |
| `route7_hipporag2_r3questions_20260224T191522Z.json` | 53/57 | char_cap=7000, sent_cap=0 (best latency) |

Q-D3 typical timings: embed=216ms, parallel=751ms, seed=0ms, PPR=6ms, synthesis=3931ms, **total=4906ms**

---

## 5. TODO: Improvement Plan

### Fix 1: Seed ALL Passages (Align with Upstream) — HIGH PRIORITY

**File:** `src/worker/hybrid_v2/routes/route_7_hipporag2.py` lines 376-382  
**What:** Instead of seeding only top-20 DPR hits, compute embedding similarity for ALL Sentence nodes and seed each with `sim × passage_node_weight`.  
**Trade-off:** Requires embedding similarity computation against entire corpus. Could use the existing `sentence_embeddings_v2` vector index with a high top-K, or pre-compute all similarities in batch.  
**Alternative:** Seed top-100 or top-200 DPR hits instead of 20, as an approximation. Less accurate than upstream but much cheaper.  
**Test:** Run Q-D3 specifically — expect 4 documents in citations. Run full benchmark for regression.

### Fix 2: Use Raw Fact Scores for Entity Seeds (Not +1 Accumulator) — HIGH PRIORITY

**File:** `src/worker/hybrid_v2/routes/route_7_hipporag2.py` lines 342-374  
**What:** Currently, each surviving triple adds +1.0 to its subject/object entity seeds, then the entire dict is normalised to sum=1.0. This discards two important signals:
1. **Relevance**: a fact scoring 0.9 cosine similarity should weigh more than one scoring 0.3
2. **IDF**: entities appearing in many documents should be down-weighted (upstream divides by `len(ent_node_to_chunk_ids)`)

**Fix:** Pass the triple's cosine similarity score from `TripleEmbeddingStore.search()` through to the seed building step. Weight each entity by `fact_score / entity_doc_frequency` (matching upstream). Do NOT pre-normalise entity seeds to sum=1.0 — let PPR's internal normalisation handle the combined vector.  
**Test:** Check entity:passage seed ratio in logs. Target ~30:70 (not 95:5).

### Fix 3: Increase PPR Passage Top-K — MEDIUM PRIORITY

**File:** `src/worker/hybrid_v2/routes/route_7_hipporag2.py` line 251  
**What:** Change `ROUTE7_PPR_PASSAGE_TOP_K` default from 20 to at least 50, ideally 100-200.  
**Trade-off:** More chunks to fetch and potentially synthesise. May need corresponding adjustment to synthesis token budget.  
**Test:** Measure document diversity in top-K passages. Expect 4+ unique documents for cross-document queries.

### Fix 4: Verify Fact Node Graph Equivalence — LOW PRIORITY (DOWNGRADED)

**File:** `src/worker/hybrid_v2/retrievers/hipporag2_ppr.py`  
**What:** After investigation of upstream `add_fact_edges()`, fact nodes do NOT appear as separate PPR graph vertices. Instead, `add_fact_edges()` creates entity↔entity edges weighted by co-occurrence count — functionally equivalent to Route 7's RELATED_TO edges. **No graph topology change needed.** However, verify:
1. RELATED_TO edge weights match upstream's co-occurrence counting semantics
2. Edges are undirected (both directions have equal weight)  
**Test:** Compare graph statistics (# nodes, # edges, avg degree) with upstream on same corpus.

### Fix 5: Validate Damping Factor (α=0.5) for Small Corpus — LOW PRIORITY

**What:** α=0.5 is upstream's default, tuned for large multi-hop QA benchmarks (HotpotQA, MuSiQue). For our small 5-PDF corpus, the high teleport rate (50%) may prevent PPR from exploring beyond the immediate seed neighbourhood. Consider testing α=0.7 or α=0.85 for more graph exploration.  
**Test:** Ablation study: run full benchmark with α ∈ {0.5, 0.7, 0.85}. Measure Q-D3 document diversity.

---

## 6. Test Plan

### Phase 1: Fix Seeding (Fixes 1+2)
1. Implement Fix 1 (seed all/many passages) and Fix 2 (raw entity scores)
2. Run `Q-D3` with `include_context=true` to verify:
   - Passage seed count (expect >> 20)
   - Entity:passage seed ratio (expect ~30:70)
   - Unique documents in citations (expect 4)
3. Run full R3 benchmark (57 questions, 3 repeats) — target ≥ 55/57

### Phase 2: Passage Top-K (Fix 3)
1. Increase `ROUTE7_PPR_PASSAGE_TOP_K` to 100
2. Run full benchmark — check for regressions from extra context
3. Monitor latency (synthesis with more chunks may be slower)

### Phase 3: Ablation Studies (Fixes 4+5)
1. Test fact nodes in PPR graph — compare scores with/without
2. Damping factor sweep {0.5, 0.7, 0.85} — 3 full benchmark runs
3. Document findings in benchmark JSON files

### Regression Guards
- All existing 55/57 passing questions must continue to pass
- Latency p50 must stay under 10,000ms
- No negative detection regressions (Q-N questions)

---

## 7. Files Reference

| File | Role |
|---|---|
| `src/worker/hybrid_v2/routes/route_7_hipporag2.py` | Main Route 7 handler — seeding, PPR invocation, synthesis |
| `src/worker/hybrid_v2/retrievers/hipporag2_ppr.py` | PPR engine — graph loading, power iteration |
| `src/worker/hybrid_v2/retrievers/triple_store.py` | Triple embedding store + recognition memory filter |
| `scripts/benchmark_route7_hipporag2.py` | Benchmark harness |
| `scripts/debug_qd3_retrieval.py` | Q-D3 specific debug script |

**Upstream reference:**
- `OSU-NLP-Group/HippoRAG` → `src/hipporag/HippoRAG.py` (retrieval + PPR)
- `OSU-NLP-Group/HippoRAG` → `src/hipporag/utils/config_utils.py` (defaults)
- Paper: [arXiv:2502.14802](https://arxiv.org/abs/2502.14802) — HippoRAG 2 (ICML '25)
