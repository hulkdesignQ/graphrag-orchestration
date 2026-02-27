# Architecture: Community-Guided Route 7 Concept Search

**Date:** 2026-02-27
**Status:** Proposed
**Scope:** Extend Route 7 (HippoRAG 2) to handle concept/exhaustive queries via community-guided retrieval with N-loss verification

---

## Problem Statement

Route 7 (HippoRAG 2) scores 56/57 on local/drift questions (Q-D) but has not been optimized for concept/exhaustive questions (Q-G), where Route 6 scores 50/57. The core insight: after adding the cross-encoder reranker (commits 5562a18, e720c65), Route 7 can now find high-quality passage seeds for concept queries. The missing piece is **community-guided scoping** — using Louvain communities as a GPS to focus retrieval on the right neighborhood of the graph.

## Key Insight

> The community node is a **GPS**, not a PPR graph vertex.

Community nodes already exist in Neo4j (materialized by GDS Louvain, Step 9 of indexing). They should NOT be added to the PPR adjacency graph. Instead, they serve as a **parallel retrieval channel** with a quality gate (N-loss check). If the community-scoped path delivers high-fidelity results, use them. If not, fall back to the existing passage-only PPR path.

## Architecture: Two Parallel Paths

```
                                ┌─────────┐
                                │  QUERY  │
                                └────┬────┘
                                     │
                    ┌────────────────┼────────────────────┐
                    │                                      │
                    ▼                                      ▼
    ════════════════════════════════       ════════════════════════════════
     PATH A: Community-Guided (GPS)        PATH B: Passage-Only (Existing)
    ════════════════════════════════       ════════════════════════════════
                    │                                      │
                    ▼                                      ▼
        ┌───────────────────────┐             ┌────────────────────────┐
        │ 1. Community Match    │             │ 1. Triple Linking      │
        │    (embedding sim)    │             │    → entity seeds      │
        │    top-3 communities  │             │                        │
        └───────────┬───────────┘             │ 2. Reranker ALL sents  │
                    │                         │    → passage seeds     │
                    ▼                         │                        │
        ┌───────────────────────┐             │ 3. PPR walk            │
        │ 2. Fetch passages     │             │    (entity + passage   │
        │    UNDER community    │             │     seeds → expand)    │
        │                       │             │                        │
        │ Community → Entity    │             │ 4. Rerank top-k        │
        │  (BELONGS_TO)         │             └──────────┬─────────────┘
        │ Entity → Sentence     │                        │
        │  (MENTIONS)           │                        │
        │ = scoped passages     │                        │
        └───────────┬───────────┘                        │
                    │                                    │
                    ▼                                    │
        ┌───────────────────────┐                        │
        │ 3. Rerank scoped      │                        │
        │    passages against   │                        │
        │    query              │                        │
        └───────────┬───────────┘                        │
                    │                                    │
                    ▼                                    │
        ┌───────────────────────┐                        │
        │ 4. N-LOSS CHECK       │                        │
        │    (LLM Auditor)      │                        │
        │                       │                        │
        │ "Does community       │                        │
        │  summary capture the  │                        │
        │  details in these     │                        │
        │  passages for this    │                        │
        │  query?"              │                        │
        └───────┬───────┬───────┘                        │
                │       │                                │
             PASS     FAIL                               │
                │       │                                │
                │       └──────── ABANDON Path A ────────┤
                │                 Fall back to            │
                ▼                 Path B results          ▼
        ┌───────────────────────┐             ┌────────────────────────┐
        │ ✅ USE Community-     │             │ ✅ USE Passage-only    │
        │    scoped passages    │             │    PPR results         │
        │    (concept answer)   │             │    (detail answer)     │
        └───────────┬───────────┘             └──────────┬─────────────┘
                    │                                    │
                    └──────────────┬─────────────────────┘
                                   ▼
                          ┌────────────────┐
                          │   SYNTHESIS    │
                          │   (LLM)       │
                          └────────────────┘
```

## Path A: Community-Guided (GPS) — Detailed

### Step A1: Community Matching

Use existing `community_matcher.match(query, top_k=3)` to find the most relevant Louvain communities by embedding similarity against community summaries.

**Already implemented:** `_resolve_community_seeds()` at line 1280 of `route_7_hipporag2.py`.

### Step A2: Fetch Scoped Passages

Traverse the graph from matched communities down to sentences:

```
Community ←[:BELONGS_TO]─ Entity ←[:MENTIONS]─ Sentence
```

This yields the set of passages that belong to the community's topic cluster. The Cypher:

```cypher
UNWIND $community_ids AS cid
MATCH (e:Entity {group_id: $group_id})-[:BELONGS_TO]->(c:Community {id: cid})
MATCH (s:Sentence {group_id: $group_id})-[:MENTIONS]->(e)
RETURN DISTINCT s.id AS sentence_id, s.text AS text, c.id AS community_id,
       c.summary AS community_summary
```

**Delta from current code:** The existing `_resolve_community_seeds()` stops at entities. We need one more MENTIONS hop to reach the actual sentences.

### Step A3: Rerank Scoped Passages

Run the Voyage rerank-2.5 cross-encoder on the community-scoped passages against the query. This filters the scoped set down to the most relevant passages within the community.

**Already available:** The reranker infrastructure exists (`_rerank_all_passages()`). We just need to call it on the scoped passage set instead of all passages.

### Step A4: N-Loss Check (LLM Auditor)

The critical quality gate. Ask a fast LLM:

> "Does the community summary accurately represent the specific details (numbers, exceptions, dates, technical constraints) found in these reranked passages that are relevant to the query? If it generalizes too much, respond is_lossy: true."

```python
async def verify_community_integrity(
    query: str,
    community_summary: str,
    reranked_passages: List[str],
) -> dict:
    """Returns {"is_lossy": bool, "missing_detail": str|null}"""
    prompt = f"""
User Query: {query}

Community Summary: {community_summary}

Source Passages:
{chr(10).join(f"- {p}" for p in reranked_passages)}

Audit Task: Does the community summary omit specific numbers, technical
constraints, or 'unless/except' conditions found in the passages that
are relevant to the query?

Respond with JSON: {{"is_lossy": true/false, "missing_detail": "description or null"}}
"""
    # Use a fast, cheap model (e.g., gpt-4o-mini)
    response = await call_fast_llm(prompt)
    return response
```

**Branching logic:**
- `is_lossy == false` → **PASS**: Use Path A's community-scoped passages for synthesis
- `is_lossy == true` → **FAIL**: Abandon Path A, use Path B's PPR results instead

## Path B: Passage-Only PPR (Existing Route 7)

This is the current Route 7 pipeline, unchanged:

1. **Triple Linking** → extract (S, P, O) from query → match entities → entity seeds
2. **Reranker** → score ALL cached sentences → passage seeds (× passage_node_weight=0.05)
3. **PPR Walk** → power iteration over Entity + Sentence graph (damping=0.5)
4. **Rerank top-k** → final passage selection

Path B runs in **parallel** with Path A. If Path A passes the N-loss check, Path B results are discarded. If Path A fails, Path B is the fallback — no wasted latency.

## Why This Works for Concept Queries

| Query Type | Path A (Community GPS) | Path B (PPR Walk) |
|---|---|---|
| Concept ("What are all the safety requirements?") | Community scopes to the right topic cluster, finds exhaustive passages | PPR may scatter across unrelated entities |
| Detail ("What is the exact voltage on page 5?") | N-loss check fails (community too broad) → falls back | PPR finds the specific sentence via entity linking |
| Hybrid ("Explain voltage requirements across all systems") | Community scopes the topic, reranker finds specifics | PPR provides cross-document bridging |

## What Already Exists (No Re-indexing Needed)

| Component | Status | Location |
|---|---|---|
| Community nodes in Neo4j | ✅ Materialized | GDS Louvain Step 9 (`lazygraphrag_pipeline.py`) |
| BELONGS_TO edges (Entity → Community) | ✅ Materialized | `neo4j_store.py:824` |
| PARENT_COMMUNITY hierarchy | ✅ Materialized | `neo4j_store.py:943` |
| Community summaries | ✅ Stored | Community node `summary` property |
| Community matcher (embedding search) | ✅ Implemented | `community_matcher.match()` |
| `_resolve_community_seeds()` | ✅ Implemented | `route_7_hipporag2.py:1280` |
| Cross-encoder reranker | ✅ Implemented | `_rerank_all_passages()` |
| PPR engine | ✅ Implemented | `hipporag2_ppr.py` |

## What Needs To Be Built (Code-Only Changes)

| Component | Effort | Description |
|---|---|---|
| Community → Sentence traversal | Small | Extend `_resolve_community_seeds()` with one more MENTIONS hop |
| Scoped reranking | Small | Call reranker on community-scoped passages instead of all passages |
| N-loss LLM check | Medium | New async method `_verify_community_integrity()` |
| Path A/B branching logic | Medium | Parallel execution, N-loss gate, fallback logic |
| `query_mode="concept"` preset | Small | New entry in `QUERY_MODE_PRESETS` to enable community path |

**Total: ~200-300 lines of code changes in `route_7_hipporag2.py`. Zero re-indexing.**

## Latency Considerations

| Step | Estimated Latency | Notes |
|---|---|---|
| Community matching | ~50ms | Embedding similarity (already cached) |
| Community → Sentence traversal | ~30ms | Single Cypher query |
| Scoped reranking | ~200ms | Voyage rerank-2.5 on scoped set (smaller than all-sentence) |
| N-loss LLM check | ~300-500ms | Fast model (gpt-4o-mini) |
| **Path A total overhead** | **~600-800ms** | Only for concept queries identified by router |

Path B (existing PPR) runs in parallel, so the overhead is only the N-loss check latency if Path A wins, or zero if Path A fails (Path B was already running).

**Production optimization:** The router already classifies query types. Only run Path A for concept/exhaustive queries (the ~20% that need it). For local/drift questions, Path B alone is sufficient (56/57).

## Comparison: Route 6 vs Route 7 + Community GPS

| Aspect | Route 6 (Current) | Route 7 + Community GPS (Proposed) |
|---|---|---|
| Concept score | 50/57 | TBD (target: >50/57) |
| Detail score | Not optimized | 56/57 (existing Path B) |
| Architecture | Flat: community + sentence search → rerank | Hierarchical: community GPS → scoped passages → N-loss verify → fallback to PPR |
| Graph utilization | None (no PPR walk) | Full (PPR walk as fallback) |
| Self-correction | No | Yes (N-loss check triggers fallback) |
| Latency | ~2-3s | ~2-3s (Path B) or ~3-4s (Path A with N-loss check) |

## Summary

The community is a **GPS, not a graph vertex**. It scopes the search to the right neighborhood. The N-loss check ensures we only use community-scoped results when they're precise enough. If the community is too broad or lossy for the specific query, we abandon it entirely and rely on the proven PPR passage-only path. This "Verify-then-Revert" pattern makes Route 7 capable of handling both concept and detail queries in a single unified route.
