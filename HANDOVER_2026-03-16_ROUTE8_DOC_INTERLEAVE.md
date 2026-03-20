# Handover: Route 8 Community-Guided Global Search — Doc Interleave

**Date:** 2026-03-16
**Branch:** fix/git-flow-cleanup (uncommitted Route 8 changes)
**Test Group:** test-5pdfs-v2-fix2

## Summary

Route 8 (fork of Route 7) is designed as a "fast global search" route for
cross-document thematic queries like Q-D3 ("list all explicit day-based
timeframes"). This session systematically tested PPR parameter tuning,
community injection, entity embedding seeds, and document-interleaved
passage selection to overcome PPR's structural bias toward high-degree
entity clusters (warranty documents).

**Key breakthrough: Document-interleaved passage selection (step 4.9)**
consistently improves Q-D3 from 2/6 → 3/6 by guaranteeing all documents
get representation in the synthesis context.

## Experiment Results (Q-D3)

| # | Configuration | Score | Chunks | Notes |
|---|--------------|-------|--------|-------|
| 1 | Route 7 baseline | 2/6 | 55 | PPR concentrates on warranty cluster |
| 2 | Breadth PPR (d=0.3 hub_deval self_loops dangling) | 2/6 | 55 | Params alone don't overcome structural bias |
| 3 | Community inject (step 4.3) | 2-5/6 | 55-137 | High variance from LLM non-determinism |
| 4 | Entity embed → PPR seeds (step 3e) | 2/6 | 55 | PPR dilutes new seeds |
| 5 | Entity embed → direct inject (step 45c) | 3/6 | 65 | Picks up some targets |
| 6 | Community diversity boost (step 4.55) | 2/6 | 55 | All communities already ≥3 items — not the bottleneck |
| 7 | Per-doc cap (chunk level) | 2/6 | 15-25 | Cuts warranty but missing docs still absent |
| 8 | **Doc interleave (passage level, cap=5)** | **3/6** | **19** | **Consistent: 10bd, 90d, 60d always hit** |
| 9 | Doc interleave + entity inject | 3/6 | 31 | LLM attention budget is the remaining bottleneck |
| 10 | No dynamic cutoff + interleave (cap=5) | 3/6 | 19 | Deterministic, all 9 docs represented |

## Root Cause Analysis

### PPR Structural Bias (fundamental)
- Entity `builder` has 50+ edges; `90 days` has 9 → PPR probability drains to warranty cluster
- Damping, hub devaluation, self-loops, dangling redistribution — none overcome this
- PPR converges in 7 iterations (breadth) vs 15 (default) but same passage distribution

### Reranker Dynamic Cutoff
- Warranty sentences score 0.28-0.40 on Cohere rerank-2.5
- Minority doc sentences (holding tank, rental mgmt) score 0.19-0.24
- Dynamic cutoff finds natural break at ~0.26 → cuts ALL minority docs
- **Fix: disable dynamic cutoff + use doc interleave** to force representation

### Document Distribution (without interleave)
```
doc_071af (warranty 1):  40 of 55 chunks (73%)
doc_ac0d  (warranty 2):  10 of 55 chunks (18%)
doc_39a7  (elevator):     3 of 55 chunks ( 5%)
doc_6d73  (elevator 2):   1 of 55 chunks ( 2%)
doc_439e  (rental mgmt):  1 of 55 chunks ( 2%)
— holding tank, rental mgmt duplicate: ABSENT
```

### Document Distribution (with interleave, cap=5)
```
doc_071af (warranty 1):  5 of 27 passages
doc_ac0d  (warranty 2):  5 of 27 passages
doc_39a7  (elevator):    5 of 27 passages
doc_c82b  (rental mgmt): 4 of 27 passages
doc_439e  (rental mgmt): 3 of 27 passages
doc_d58f  (holding tank): 2 of 27 passages
doc_6d73  (elevator 2):  1 of 27 passages
doc_4cbb  (holding tank): 1 of 27 passages
doc_3e75  (elevator 3):  1 of 27 passages
```

### LLM Synthesis Bottleneck (remaining gap: 3/6 → 6/6)
- Context contains all 6 Q-D3 targets after doc interleave + entity inject
- LLM spends 5 bullets on "60 days" (warranty) and drops brief mentions
- "3 business days for full refund" and "5 business days for listing" are 1-line mentions
- v10_comprehensive prompt instruction "give each item its own bullet" ENCOURAGES verbosity

## Implementation Details

### Step 4.9: Document-Interleaved Passage Selection
Location: `route_8_hipporag2_community.py` ~line 1115
- Extracts doc_id from sentence_id pattern (`sid.split("_sent_")[0]`)
- Groups reranked passages by document
- Round-robin interleave: 1 from each doc per round, up to `max_per_doc`
- Config: `max_chunks_per_doc` / `ROUTE8_MAX_CHUNKS_PER_DOC` (default 0 = disabled)
- Best setting for Q-D3: `max_chunks_per_doc=5` with `rerank_dynamic_cutoff=0`

### Step 4.55: Community Diversity Check
Location: ~line 975
- Returns `per_community` mapping from `_resolve_community_seeds`
- Counts community representation in reranked output
- Finding: NOT the bottleneck — all communities already have ≥3 items

### `_resolve_community_seeds` Return Type Change
- Added 4th return value: `Dict[str, List[str]]` (per_community mapping)
- All callers updated to unpack 4-tuple

### Config Overrides for Best Q-D3 Settings
```json
{
  "community_passage_seeds": "1",
  "ppr_passage_top_k": "100",
  "entity_embedding_seeds": "1",
  "entity_context_inject": "0",
  "community_context_inject": "0",
  "rerank_dynamic_cutoff": "0",
  "rerank_top_k": "260",
  "max_chunks_per_doc": "5"
}
```

## Files Modified (uncommitted)

- `src/worker/hybrid_v2/routes/route_8_hipporag2_community.py`
  - Step 4.9: doc-interleaved passage selection (~1115)
  - Step 4.55: community diversity check (~975)
  - `_resolve_community_seeds` 4-tuple return (~2247)
  - Per-community round-robin interleaving (~2340)

## TODO (next session)

### Priority 1: LLM Synthesis Optimization
- [ ] Create v11_enumeration prompt: "deduplicate by unique value, 1 bullet per unique timeframe"
- [ ] Or: per-document extraction → merge (Route 6 pattern for Route 8)
- [ ] Target: Q-D3 consistently 5/6 or 6/6

### Priority 2: Route 8 Default Configuration
- [ ] Set `max_chunks_per_doc=5` as Route 8 default for community_search mode
- [ ] Set `rerank_dynamic_cutoff=0` with high `rerank_top_k` as Route 8 default
- [ ] Add `community_search` preset override for these settings

### Priority 3: Full Benchmark
- [ ] Run 19-question benchmark on Route 8 to check for regressions
- [ ] Compare Route 7 vs Route 8 on entity-focused questions
- [ ] Ensure Route 8 doesn't break local_search / factual queries

### Priority 4: Commit & Deploy
- [ ] Commit Route 8 changes
- [ ] Router classification: send cross-doc thematic queries to Route 8
- [ ] Deploy to production

## Technical Notes

### Server
```bash
PYTHONUNBUFFERED=1 nohup python -m uvicorn src.api_gateway.main:app \
  --host 0.0.0.0 --port 8888 --timeout-keep-alive 300 > /tmp/server.log 2>&1 &
```

### Test Q-D3
```bash
curl -s http://localhost:8888/hybrid/query \
  -H 'Content-Type: application/json' \
  -H 'X-Group-ID: test-5pdfs-v2-fix2' \
  -d '{
    "query": "Compare \"time windows\" across the set: list all explicit day-based timeframes.",
    "response_type": "summary",
    "force_route": "hipporag2_community",
    "config_overrides": {
      "community_passage_seeds": "1",
      "ppr_passage_top_k": "100",
      "entity_embedding_seeds": "1",
      "rerank_dynamic_cutoff": "0",
      "rerank_top_k": "260",
      "max_chunks_per_doc": "5"
    }
  }'
```

### Key Log Events
- `step_4.9_doc_interleave` — doc distribution after interleaving
- `step_4.55_community_representation` — per-community counts in reranked output
- `step_3e_entity_embedding_seeds` — entity embedding hits used as PPR seeds
- `step_45c_entity_context_inject` — entity-derived chunks injected into context
