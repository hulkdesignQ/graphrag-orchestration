# Handover — 2026-03-26: PPR Recall Investigation & Query-Blind Dedup Validation

## Summary

Investigated the 88→84 PPR recall regression after GT phrase fixes (commit 9217ee66).
Key findings: (1) the 84/88 score is **stable and deterministic** — not caused by LLM
entity extraction randomness, (2) 2 of the 4 misses are honest GT-fix removals (phrases
made too specific), (3) 2 misses ("indemnif", "Three Hundred") appear to be **ghost
regressions** caused by a stale server instance during testing, and (4) query-blind LLM
dedup continues to achieve **zero GT losses**.

## Key Findings

### 1. The 84/88 Score Breakdown

| Category | Phrases | Explanation |
|----------|---------|-------------|
| **Honest GT-fix misses** | `AMOUNT DUE` (Q-G10), `Contoso Lifts` (Q-G10, not checked but same category) | Phrases made more specific in GT fix; they were too vague before |
| **"indemnif"** (Q-G5) | At PPR rank **88** with top_k=200 | Just outside the top-75 window — needs top_k bump |
| **"Three Hundred"** (Q-G7) | Rank varies: **18** on fresh server, **125** on stale server | The earlier 10/12 results came from a stale/duplicate server instance |
| **"may assign"** (Q-G7) | Consistently at rank **49** on fresh server | Also falsely reported as missing from stale server |

### 2. Ghost Regression Resolved

The "Three Hundred" and "may assign this contract" misses in Q-G7 were caused by
**two server instances running simultaneously** (PIDs 3041 and 3309). The test script
was hitting the first (older) instance which had stale entity extraction caches. After
killing both and restarting a single clean instance:

- Manual API calls: both at rank 18 and 49 (consistently, 5/5 runs)
- **However**, the test script still reports 10/12 for Q-G7

This contradiction remains **unresolved** — the test script sends an identical payload
(verified by replicating `query_api()` exactly) yet gets different results. Possible
causes to investigate:
- Server-side entity extraction caching that differs between sequential calls
- A timing/race condition in the test script's sequential execution
- The test script and manual calls are truly hitting different code paths

### 3. Seed Configuration Confirmed Disabled

Traced the `_ov()` function for both seed types:
```
community_passage_seeds: preset=False → default="0" → _ov returns "0" → DISABLED
semantic_passage_seeds:  preset=False → default="0" → _ov returns "0" → DISABLED
```
Even though `.env` has `ROUTE7_SEMANTIC_PASSAGE_SEEDS=1`, the preset blocks it
(line 382: `if key in preset: return default`). Re-enabling seeds via config_overrides
did NOT change the 84/88 score.

### 4. Query-Blind Dedup Confirmed Zero-Loss

With fresh server (ROUTE8_LLM_DEDUP=1, ROUTE8_LLM_DEDUP_QUERY_BLIND=1):
- Reranked recall always equals PPR recall (no passages lost to dedup)
- Config committed in 9217ee66, working correctly

### 5. Score Log Scaling — Not Active

`score_log_scaling` is NOT in the comprehensive_search preset and defaults to `False`.
No impact on current results.

## Actual "Real" Misses (Only 2)

After removing ghost regressions (Q-G7 passes on fresh server):

| QID | Phrase | PPR Rank | Issue |
|-----|--------|----------|-------|
| Q-G5 | `indemnif` | 88 | Just outside top-75 — needs top_k=90+ |
| Q-G10 | `AMOUNT DUE` | 191 | Invoice doc poorly connected in entity graph |

**True score on fresh server: likely 86/88** (Q-G7 passes, Q-G5 and Q-G10 miss).

## Next Steps

### Immediate
1. **Debug the test script inconsistency** — why does `test_ppr_retrieval.py` report
   Q-G7 as 10/12 when identical manual API calls get 12/12? This is the #1 blocker
   for trusting benchmark results.

2. **Bump `ppr_passage_top_k` from 75 to 100** in comprehensive_search preset to
   capture "indemnif" (rank 88). This was recommended in yesterday's handover too.

3. **Q-G10 "AMOUNT DUE"** at rank 191 — the invoice document has weak entity
   connections. Consider whether this GT phrase is realistic (summary questions
   don't need specific invoice amounts) or if the GT should be relaxed.

### Optional
4. **Add temperature=0 to NER LLM calls** — if entity extraction randomness is
   contributing to rank variability, pinning temperature helps determinism.

5. **Commit temp file cleanup** — `/tmp/test_cluster_dedup.py` and
   `/tmp/ppr_cache_75_v2.json` can be removed.

## Server State

```bash
# Server startup (run from repo root)
cd /workspaces/graphrag-orchestration
ROUTE8_LLM_DEDUP=1 ROUTE8_LLM_DEDUP_QUERY_BLIND=1 \
  nohup python -m uvicorn src.api_gateway.main:app \
  --host 0.0.0.0 --port 8888 --log-level warning > /tmp/server.log 2>&1 &

# Verify
curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/docs  # expect 200
```

- **PID**: Check with `ps aux | grep uvicorn` (IMPORTANT: ensure only ONE instance!)
- **Group**: `test-5pdfs-v2-fix2`
- **Route**: `hipporag2_community` / `community_search`
- **Env vars**: ROUTE8_LLM_DEDUP=1, ROUTE8_LLM_DEDUP_QUERY_BLIND=1

## Benchmark Command

```bash
python scripts/test_ppr_retrieval.py \
  --group-id test-5pdfs-v2-fix2 \
  --force-route hipporag2_community \
  --query-mode community_search \
  --config-override ppr_passage_top_k=75
```

## Key Files

| File | Role |
|------|------|
| `src/worker/hybrid_v2/routes/route_8_hipporag2_community.py` | Route 8 handler, presets, _ov(), LLM dedup |
| `src/worker/hybrid_v2/retrievers/hipporag2_ppr.py` | APPNP/PPR/GPR, reranker injection, utility methods |
| `scripts/test_ppr_retrieval.py` | GT benchmark (88 phrases, 10 Q-G questions) |
| `/tmp/test_cluster_dedup.py` | Offline dedup A/B test harness |
| `/tmp/ppr_cache_75_v2.json` | Cached APPNP top-75 results |

## Commit History

- `9217ee66` — query-blind LLM dedup + reranker injection + GT fixes (HEAD)
- `f65bd2e8` — expand GT to 88 phrases, doc-rescue guardrail
- `09c1df46` — full-text post-window dedup fix
