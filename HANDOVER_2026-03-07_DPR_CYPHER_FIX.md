# Handover — 2026-03-07: DPR Cypher Fix, Cross-Encoder Discovery & Parameter Sweep

## Summary

Fixed a silent Cypher syntax bug that had broken DPR (Dense Passage Retrieval) in all prior Route 7 benchmarks. Discovered that enabling DPR with the current cross-encoder seed architecture causes score degradation. Ran a 4-config parameter sweep. Key open question: **what is DPR's real contribution and how should it interact with cross-encoder seeds?**

## What Was Done

### 1. NER Duration Prompt Fix (committed earlier)
- Added "time periods, deadlines, durations" to NER extraction prompts
- This alone fixed Q-D3 from 2/3 → 3/3 (confirmed via isolation test with max_facts=4)
- Architecture doc §50

### 2. IDF + Min-Max + Mean-Norm Implementation (committed 0dba3437)
- Upstream-aligned normalization in PPR seed weights
- Toggle: `ROUTE7_IDF_ENABLED=1` (default ON)
- No measurable quality impact at 5-doc scale (72% of entities have mention_count=1)
- Architecture doc §52

### 3. DPR Cypher Syntax Fix (committed 8afaa52e)
- **Root cause:** `CALL (...) {}` (Cypher 25 spread import) is NOT supported on Neo4j Aura 5.27
- **Three affected queries** in `route_7_hipporag2.py`:
  - `_dpr_passage_search()` — line ~1353
  - `_retrieve_sentence_evidence()` — line ~1711
  - `_semantic_expansion()` — line ~1934
- **Fix:** Changed `CALL (...) {` → `CALL {`
- Added `top_k < 0` early-return sentinel to allow disabling DPR via `ROUTE7_DPR_TOP_K=-1`

### 4. DPR + Cross-Encoder Sweep (committed c0024cf0)

| Config | DPR Seeds | CE Seeds | Total Seeds | Score |
|--------|-----------|----------|-------------|-------|
| Pure upstream (DPR=all, no CE) | 405 | 0 | 405 | **51/57** |
| DPR=50 + CE=20 | ~50 | ~8 | ~58 | **53/57** |
| DPR=20 + CE=20 | 20 | ~16 | ~36 | **55/57** |
| CE only (DPR=-1) | 0 | 20 | 20 | **56/57** |

Benchmark files (all in `benchmarks/`):
- `T172224Z` — pre-fix baseline (DPR broken): 57/57 (lenient judge) / 56/57 (honest)
- `T204915Z` — DPR=50 + CE: 53/57
- `T211055Z` — CE only (DPR=-1): 56/57
- `T214046Z` — Pure upstream (DPR=all, no CE): 51/57
- `T214805Z` — DPR=20 + CE: 55/57

### 5. Section-Path Enrichment Experiment (reverted)
- Prepended `[section_path]` to cross-encoder passage texts
- Result: 55/57 (worse) — noise in rankings globally
- Architecture doc §54

### 6. Q-D3 Root Cause Analysis (architecture doc §55)
- Target passage `sent_33` (180-day rental threshold) is never retrieved
- Entity "leases of more than 180 days" has ZERO synonymy edges — graph-isolated
- Passage text is semantically about "fees", not "timeframes"
- This is a retrieval ceiling at current architecture

## Current State

### Code defaults (committed)
```
ROUTE7_DPR_TOP_K=50       # upstream-aligned
ROUTE7_IDF_ENABLED=1      # upstream-aligned
```

### Local .env overrides (not committed, gitignored)
```
ROUTE7_DPR_TOP_K=20       # best hybrid balance for small corpus
```

### Architecture
The cross-encoder "semantic passage seeds" feature (`ROUTE7_SEMANTIC_PASSAGE_SEEDS=1`) reranks ALL 202 sentences against the query using voyage-rerank-2.5, then injects the top-20 as passage seeds into PPR with weight 0.05. This is **not in upstream HippoRAG 2** — it's our addition that replaces DPR's role more precisely at small corpus scale.

Upstream HippoRAG 2 uses DPR to seed ALL passages into PPR (dot product + min-max normalize). No cross-encoder pre-step.

## Open Questions for Tomorrow

### 1. What is DPR's real contribution?
The sweep shows more DPR seeds → lower score, but this is at 202 sentences. We need to understand:
- Is the score drop caused by **DPR seeds themselves** (low quality), or by the **interaction** between DPR and CE seeds competing?
- Would DPR alone with proper tuning (no CE) outperform pure upstream (51/57)?
- At what corpus size does DPR become essential (CE over all passages too slow)?

### 2. Should we remove the cross-encoder seed feature entirely?
It's not in upstream HippoRAG 2. If DPR can be tuned to match CE quality, the architecture would be cleaner and more scalable. Test ideas:
- DPR=20 without CE seeds (isolate DPR contribution)
- DPR with contextual embeddings (voyage-context-3 already used) — are the embeddings good enough?
- Check if DPR failure is due to embedding quality or the seed-count dilution

### 3. Q-D3 retrieval ceiling
The honest score is 56/57. Potential approaches (not yet tested):
- Query decomposition for "list all X" queries
- Section-level sibling expansion after PPR
- Better entity extraction: "180 days" as standalone entity (not "leases of more than 180 days")

## TODO List

1. **Isolate DPR contribution**: Run DPR=20 with CE disabled (`SEMANTIC_PASSAGE_SEEDS=0`) — compare to pure upstream (51/57) to see if DPR top-k filtering helps
2. **Analyze DPR seed quality**: For Q-D3/Q-D8/Q-D10 (the questions that fail with DPR), inspect which passages DPR ranks in top-20 vs what CE ranks — understand the quality gap
3. **Test DPR-only configs**: DPR=10, DPR=20, DPR=30 without CE to find DPR's own quality curve
4. **Document the cross-encoder seed feature**: It's a significant deviation from upstream — needs clear justification in architecture doc (why it exists, when it's needed, scalability limits)
5. **Consider deployment strategy**: Code default=50 (upstream), but production needs tuning. Should `deploy-graphrag.sh` set an explicit `ROUTE7_DPR_TOP_K`?
6. **Push to remote**: Current commits are local only

## Commits This Session

| Hash | Description |
|------|-------------|
| `0dba3437` | feat: IDF + min-max + mean-norm with toggle |
| `8afaa52e` | fix: Cypher CALL syntax + DPR disable sentinel |
| `0505455c` | docs: §53-§55 DPR fix, section-path, Q-D3 root cause |
| `c0024cf0` | fix: restore DPR upstream default + full sweep in §53 |

## Known Issue: All Sentences Have `chunk_id = NULL`

Confirmed: all 202 Sentence nodes in `test-5pdfs-v2-fix2` have `chunk_id=NULL`. The `id` field (e.g., `doc_xxx_sent_33`) is used for identification. The DPR Cypher queries reference `s.id` not `s.chunk_id`. This may be relevant when investigating DPR's contribution — need to check if any DPR queries rely on `chunk_id` for joins or lookups.

## Environment Notes

- API runs on port 8001 with `REQUIRE_AUTH=false ALLOW_LEGACY_GROUP_HEADER=true`
- `.env` values override code defaults via `load_dotenv()` in main.py — always check .env first
- Benchmark: `python3 scripts/benchmark_route7_hipporag2.py --no-auth --group-id test-5pdfs-v2-fix2 --url http://localhost:8001 --repeats 3`
- LLM eval: `python3 scripts/evaluate_route4_reasoning.py <benchmark.json>`
- Neo4j Aura 5.27: `CALL {}` works, `CALL (...) {}` does NOT
- Test group: `test-5pdfs-v2-fix2` (403 entities, 2555 relationships, 202 sentences, all `chunk_id=NULL`)
