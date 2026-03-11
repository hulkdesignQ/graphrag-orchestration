# Architecture: Indexing Pipeline Optimization (2026-03-11)

## Problem Statement

The indexing pipeline for 5 small PDF files took 5–10 minutes end-to-end. After a deep
audit of every pipeline stage, cloud resource configuration, and concurrency setting,
we identified **6 major bottlenecks** accounting for ~80% of wall-clock time. This
document records the architectural changes made to cut pipeline time to ~2.5–3 minutes.

## Summary of Changes

| # | Optimization | Before | After | Savings |
|---|-------------|--------|-------|---------|
| 1 | **GDS → In-process graph algorithms** | Aura GDS session: 60–120s | numpy + networkx: ~3s | **~60–120s** |
| 2 | **OpenIE semaphore 4→8 + fix double-acquire** | Semaphore(4), 2× acquire/batch | Semaphore(8), 1× acquire/batch | **~30–45s** |
| 3 | **Parallelize section enrichment** | Sequential steps 4.6/4.7/4.8 | asyncio.gather() | **~10–18s** |
| 4 | **Foundation edges: remove sleeps + parallelize** | Sequential + 2×sleep(1) | asyncio.gather(), no sleeps | **~10–12s** |
| 5 | **DI concurrency 3→5** | 2 batches for 5 PDFs | 1 batch | **~5–15s** |
| | **Total estimated savings** | | | **~115–210s** |

---

## Change 1: GDS → In-Process Graph Algorithms (Step 8)

### Background

Step 8 ran KNN, Louvain community detection, and PageRank via an **Aura Serverless GDS
session** — a separate 2GB container provisioned per pipeline run. For small graphs
(~50–200 entities from 5 PDFs), the overhead dwarfed the computation:

| Phase | Time |
|-------|------|
| Session provisioning | 15–45s |
| Pre-cleanup of stale sessions | 5–10s |
| Graph projection (entities → GDS) | 10–20s |
| Algorithm execution (KNN + Louvain + PageRank) | 5–10s |
| Write-back (100-item batches with 0.3s sleep) | 5–10s |
| Session deletion | 5–10s |
| **Total** | **60–120s** |

The actual computation for <500 entities is trivially fast (< 1 second).

### Architecture

New method `_run_local_graph_algorithms()` in `lazygraphrag_pipeline.py`:

```
                    ┌──────────────────────┐
                    │ _run_gds_graph_algo() │
                    └───────────┬──────────┘
                                │
                    ┌───────────▼──────────┐
                    │  Count entities       │
                    │  (Neo4j read query)   │
                    └───────────┬──────────┘
                                │
               ┌────────────────┼────────────────┐
               │ < GDS_LOCAL_THRESHOLD (500)      │ >= threshold
               ▼                                  ▼
    ┌──────────────────────┐          ┌──────────────────────┐
    │ _run_local_graph_    │          │  Existing GDS path   │
    │   algorithms()       │          │  (Aura Serverless)   │
    │                      │          │                      │
    │ 1. Fetch embeddings  │          │ Session create/retry │
    │    from Neo4j        │          │ Graph projection     │
    │ 2. numpy cosine KNN  │          │ gds.knn/louvain/     │
    │ 3. networkx Louvain  │          │   pageRank           │
    │ 4. networkx PageRank │          │ Write-back + cleanup │
    │ 5. Batch write-back  │          └──────────────────────┘
    │    (500-item, no     │
    │     sleep pacing)    │
    └──────────────────────┘
```

### Algorithm Equivalence

| Algorithm | GDS Implementation | Local Implementation | Notes |
|-----------|-------------------|---------------------|-------|
| **KNN** | `gds.knn.stream()` with COSINE metric | `numpy` cosine similarity matrix (`X_norm @ X_norm.T`) | Same top-k + cutoff logic. Dedup via `min(i,j), max(i,j)` pairs |
| **Louvain** | `gds.louvain.stream()` | `networkx.algorithms.community.louvain_communities()` | `resolution=1.0` matches GDS default. `seed=42` for determinism |
| **PageRank** | `gds.pageRank.stream()` | `networkx.pagerank()` | `alpha=0.85`, `tol=1e-6` match GDS defaults |

### Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `GDS_LOCAL_THRESHOLD` | `500` | Entities below this → in-process. Set to `0` to always use GDS |

### Cost Impact

- **GDS session eliminated** for typical workloads: saves $0.035/hr/GB × 2GB × ~2 min ≈ $0.002/run
- For high-volume indexing (1000s of runs/month), this adds up to meaningful savings
- GDS Aura Serverless credentials (`AURA_DS_CLIENT_ID`, `AURA_DS_CLIENT_SECRET`) are
  still required as fallback for large graphs

### Files Changed

- `src/core/config.py` — Added `GDS_LOCAL_THRESHOLD: int = 500`
- `src/worker/hybrid_v2/indexing/lazygraphrag_pipeline.py`:
  - New method: `_run_local_graph_algorithms()`
  - Modified: `_run_gds_graph_algorithms()` — added dispatch logic at top

---

## Change 2: OpenIE Semaphore + Double-Acquire Fix (Step 5)

### Background

Step 5 (`_extract_openie_triples`) is the other largest bottleneck. Two-step extraction
(NER → Triple) acquired `Semaphore(4)` **twice per batch** — once for NER, once for
Triple extraction. With 4 permits and 2 acquires per batch, only **2 complete batches**
could run concurrently.

### Changes

1. **Increased semaphore from 4 → 8**: gpt-4.1 at 50K TPM can handle 8 concurrent calls
   (each ~500–1500 tokens). Roughly doubles throughput.

2. **Single semaphore acquire per two-step batch**: Both NER and Triple calls now run
   within a single `async with sem:` block. This eliminates the "double-booking" problem
   where a batch holds one permit for NER, releases it, then competes for another permit
   for Triple extraction.

### Before vs After

```
BEFORE (Semaphore(4), double-acquire):
  Batch 1: [acquire→NER→release] ... [acquire→Triple→release]
  Batch 2: [acquire→NER→release] ... [acquire→Triple→release]
  Batch 3: [waiting...] [waiting...]
  → Only 2 complete batches at a time, 4 permits ÷ 2 = 2

AFTER (Semaphore(8), single-acquire):
  Batch 1: [acquire→NER→Triple→release]
  Batch 2: [acquire→NER→Triple→release]
  ...
  Batch 8: [acquire→NER→Triple→release]
  → 8 complete batches at a time
```

### Files Changed

- `lazygraphrag_pipeline.py`:
  - Line ~1985: `Semaphore(4)` → `Semaphore(8)`
  - `_extract_batch_two_step()`: restructured to single `async with sem:` block

---

## Change 3: Parallel Section Enrichment (Steps 4.6–4.8)

### Background

Steps 4.6 (`_embed_section_nodes`), 4.7 (`_generate_section_summaries`), and 4.8
(`_embed_keyvalue_keys`) ran **strictly sequentially** with the comment: "Run section
enrichment sequentially to avoid overwhelming Neo4j Aura."

These three operations have **no data dependencies** between them:
- 4.6: Embeds section text via Voyage
- 4.7: Generates LLM summaries per section
- 4.8: Embeds KVP keys via Voyage

### Change

Replaced sequential `await` calls with `asyncio.gather()`:

```python
# Before:
section_embed_stats = await self._embed_section_nodes(group_id)
section_summary_stats = await self._generate_section_summaries(group_id)
kvp_embed_stats = await self._embed_keyvalue_keys(group_id)

# After:
section_embed_stats, section_summary_stats, kvp_embed_stats = await asyncio.gather(
    self._embed_section_nodes(group_id),
    self._generate_section_summaries(group_id),
    self._embed_keyvalue_keys(group_id),
)
```

Wave 2 (4.8b structural embed + 4.8c similarity edges) still runs after wave 1, as
4.8b depends on section summaries from 4.7.

### Files Changed

- `lazygraphrag_pipeline.py` lines ~457–465

---

## Change 4: Foundation Edges — Remove Sleeps + Parallelize (Step 7)

### Background

`_create_foundation_edges()` created 3 edge types **sequentially** with
`asyncio.sleep(1)` between each phase:

```
APPEARS_IN_SECTION  → 3-5s → sleep(1) → APPEARS_IN_DOCUMENT → 3-5s → sleep(1) → HAS_HUB_ENTITY → 3-5s
Total: ~11–17s (9–15s queries + 2s sleep)
```

### Change

- **Removed** both `asyncio.sleep(1)` calls (Neo4j Aura Professional handles concurrent
  writes without issues)
- **Parallelized** all 3 edge types via `asyncio.gather()` — they operate on different
  relationship types and don't conflict

```
Before: 11–17s (sequential + 2s sleep)
After:  3–5s  (parallel, slowest query dominates)
```

### Files Changed

- `lazygraphrag_pipeline.py`: `_create_foundation_edges()` refactored to use inner
  async functions + `asyncio.gather()`

---

## Change 5: DI Concurrency 3→5 (Step 1)

### Background

Document Intelligence extraction used `DI_CONCURRENCY = 3`, even though the DI service
itself supports `DEFAULT_CONCURRENCY = 5`. For 5 PDFs, this meant 2 batches (3+2)
instead of 1 batch (all 5 concurrent).

### Change

```python
DI_CONCURRENCY = 3  →  DI_CONCURRENCY = 5
```

### Files Changed

- `lazygraphrag_pipeline.py` line ~771

---

## Estimated Timeline Impact

```
BEFORE (5 small PDFs, typical case):
┌──────────────────────────────────────────────────────────────────────────┐
│ DI(3)  │ Sent │ KNN │ Sect(seq) │  OpenIE(sem4×2) │ GDS(session) │ Comm│
│ 15-30s │ 20s  │  5s │   30-45s  │    60-90s       │   60-120s    │ 25s │
│                                                              Total: ~5-8min
└──────────────────────────────────────────────────────────────────────────┘

AFTER (all optimizations applied):
┌──────────────────────────────────────────────────────────────────────────┐
│ DI(5)  │ Sent │ KNN │Sect(par)│  OpenIE(sem8×1) │Local│ Comm│
│ 5-10s  │ 20s  │  5s │ 12-20s  │    20-40s       │ 3s │ 25s │
│                                               Total: ~1.5-3min
└──────────────────────────────────────────────────────────────────────────┘
```

## Future Optimization Opportunities (Not Yet Implemented)

| Opportunity | Impact | Effort |
|-------------|--------|--------|
| **Merge Voyage embedding calls** — Combine steps 4.6/4.8/4.8b into a single API call | ~5–8s | Medium |
| **Increase gpt-4.1 TPM 50K→100K** — Enables higher OpenIE parallelism | Enables sem=12+ | Config |
| **Pre-pipeline sentence embedding** — Start Voyage while DI processes later PDFs | ~5–10s | High |
| **Voyage retry/backoff** — Add resilience to embedding calls | Reliability | Low |
| **Batch small OpenIE groups** — Merge 2–3 sentence batches to reduce LLM calls | ~10–15s | Medium |
