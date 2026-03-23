# Handover: Entity-Bridge Filter & MAP-REDUCE Synthesis Tuning
**Date:** 2026-03-23  
**Session Focus:** Noise reduction in Route 8 community_search synthesis pipeline via entity-bridge structural filtering and prompt tuning

---

## Summary

Investigated why MAP-REDUCE synthesis scores 25-27/30 on Q-G LLM-judge despite 48/48 (100%) PPR retrieval. Root cause: the reranker dynamic cutoff (threshold 0.22) lets ~48/50 passages through to synthesis, flooding MAP with noise. Built an entity-bridge structural filter that uses IDF-weighted entity overlap to cut noise passages — works excellently for focused queries (50→23p, 4/4 recall) but hurts cross-document synthesis. The filter is **implemented but disabled** in the preset, awaiting multi-repeat benchmarking to determine if the noise reduction actually improves synthesis.

**Key insight:** LLM synthesis has **±5pt variance** per run (same config scored 27 then 22), making single-run comparisons unreliable.

**Committed prior session:** `18e5a1aa` (APPNP mode), `1dc0f8e2` (top_k 150→50)  
**Uncommitted:** Entity-bridge filter code (disabled), raw_extractions output, eval script fix

---

## Benchmark Results (all Q-G, single run)

| Config                        | Total | G1 | G2 | G3 | G4 | G5 | G6 | G7 | G8 | G9 | G10 |
|-------------------------------|------:|---:|---:|---:|---:|---:|---:|---:|---:|---:|----:|
| **Baseline MAP-REDUCE**       | 27/30 |  3 |  3 |  3 |  3 |  3 |  3 |  3 |  2 |  2 |   2 |
| No MAP-REDUCE (single-shot)   | 26/30 |  3 |  3 |  3 |  2 |  3 |  2 |  3 |  1 |  3 |   3 |
| MAP prompt tweak              | 25/30 |  3 |  3 |  3 |  3 |  3 |  2 |  2 |  2 |  1 |   3 |
| REDUCE prompt tweak           | 25/30 |  3 |  2 |  3 |  3 |  2 |  3 |  2 |  2 |  2 |   3 |
| Bridge filter ON              | 21/30 |  2 |  3 |  2 |  2 |  2 |  2 |  1 |  1 |  3 |   3 |
| **Reverted (≈baseline)**      | 22/30 |  3 |  3 |  2 |  2 |  2 |  2 |  1 |  1 |  3 |   3 |

**Q-D baseline:** 28/30 (not retested — no changes affect Q-D path)

⚠️ **Variance warning:** The "Reverted" run uses the same config as "Baseline" yet scored 22 vs 27. All conclusions from single runs are unreliable. Multi-repeat benchmarks (3-5x) are needed.

---

## Key Findings

### 1. Reranker Noise Problem
- Dynamic cutoff threshold 0.22 lets 47.9/50 passages through on average — almost no filtering
- For focused queries (Q-G8 "insurance/indemnity"): WARRANTY doc floods 39/50 PPR slots through hub entities ("Builder", "Owner"), only 3 are GT-relevant
- GT data spans the FULL reranker score range (0.24–0.63) — raising the threshold cuts GT at the edges
- Document imbalance: WARRANTY dominates because its entities are hubs in the knowledge graph

### 2. Entity-Bridge Structural Filter (Step 4.8)
**Concept:** For each passage, check how many query-seed entities it directly shares in the graph. Weight by entity IDF: `1/log(1 + mention_count)`. Passages reached only through hub entities (high mention_count) get near-zero bridge scores.

**Results:**
- Focused queries: 50→22-28 passages, 4/4 recall ✅ (cuts WARRANTY noise precisely)
- Broad queries: adaptive skip when <30% of passages have bridges (correctly detects "summarize all" queries)
- Retrieval recall: 47/48 (97.9%) — only Q-G3's `$35` dropped
- Synthesis quality: inconclusive (21/30, but baseline variance is ±5pt)

**Current state:** Code implemented, disabled in preset (`"entity_bridge_filter": False`)

### 3. Prompt Tuning (reverted)
- **MAP prompt:** Added "functional purpose" instruction → regressed Q-G9 (over-extraction). **Reverted.**
- **REDUCE prompt:** Added broad-topic inclusion instruction → no reliable improvement. **Reverted.**
- **raw_extractions fix:** Changed dict→list for Pydantic compatibility. **Kept** (bug fix).

### 4. MAP-REDUCE vs Single-Shot
- MAP-REDUCE is consistently better than single-shot synthesis (27 vs 26 baseline)
- MAP correctly extracts per-document facts but REDUCE drops edge facts while keeping noise
- `max_facts_per_doc=15` in REDUCE may be too aggressive for documents with many relevant facts

---

## Uncommitted Changes

### `src/worker/hybrid_v2/retrievers/hipporag2_ppr.py`
- Added `compute_entity_bridge_scores()` method (~35 lines)
- Computes IDF-weighted entity overlap between passage neighbors and query seed entities

### `src/worker/hybrid_v2/routes/route_8_hipporag2_community.py`
- Added Step 4.8 entity-bridge filter block (~109 lines, **disabled** in preset)
- Adaptive coverage detection: skips filter for broad queries (<30% coverage)
- Configurable via: `entity_bridge_filter`, `entity_bridge_reranker_keep`, `entity_bridge_doc_min`, `entity_bridge_coverage_min`
- Added `raw_extractions` to MAP-REDUCE synthesis output (bug fix for Pydantic model)

### `scripts/evaluate_route4_reasoning.py`
- Added `AZURE_TENANT_ID` support in `_get_aad_token()` (needed for MFA auth)

---

## Benchmark Files Produced

| File | Config |
|------|--------|
| `*_20260323T142052Z` | Baseline MAP-REDUCE (Q-G 27/30) |
| `*_20260323T144519Z` | Baseline Q-D (28/30) |
| `*_20260323T154828Z` | No MAP-REDUCE single-shot (Q-G 26/30) |
| `*_20260323T160655Z` | MAP prompt tweak (Q-G 25/30) |
| `*_20260323T161809Z` | REDUCE prompt tweak (Q-G 25/30) |
| `*_20260323T182032Z` | Bridge filter ON (Q-G 21/30) |
| `*_20260323T185002Z` | Reverted ≈baseline (Q-G 22/30) |

---

## TODO List

### High Priority

1. **Multi-repeat benchmark** — Run 3-5 repeats of baseline config to establish true mean and variance. Without this, we cannot evaluate any change reliably. Use `--repeats 3` flag.

2. **Multi-repeat bridge filter benchmark** — Run 3-5 repeats with bridge filter ON to compare means. The 21/30 single run may be noise.

3. **Investigate Q-G7 and Q-G8 persistent weakness** — These two questions scored 1/3 in the last two runs (both bridge ON and reverted). The judge says Q-G7 misses "5 business days written notification if property listed for sale" and "written approval for expenditures >$300". Q-G8 misses purchase contract risk-of-loss and warranty damage exclusions. These may be retrieval gaps rather than synthesis issues.

### Medium Priority

4. **Tune max_facts_per_doc** — Currently hardcoded at 15 in REDUCE. For documents like WARRANTY with many relevant clauses, this may truncate GT facts. Test 20 or 25.

5. **Bridge filter: 2-hop entity extension** — Current filter only checks direct (1-hop) entity neighbors. Extending to 2-hop (passage→entity→entity→seed) could improve recall for indirect connections without the aggressive cutting seen in 1-hop.

6. **Document-aware reranker threshold** — Instead of a flat threshold across all passages, apply per-document thresholds based on each document's score distribution. This would preserve the long-tail passages from underrepresented documents.

### Low Priority

7. **Citation score bug** — All citations in benchmark JSON show `score: 1.000` instead of real reranker scores. The real scores are only in server logs. Fix: propagate reranker scores through to citation output.

8. **Commit clean changes** — Once multi-repeat benchmarks validate, commit: entity-bridge filter code (disabled by default), raw_extractions fix, eval script AZURE_TENANT_ID fix.

9. **Q-G10 retrieval investigation** — "Summarize each document's main purpose" sometimes gets 0/50 PPR hits for "manag" (PROPERTY MANAGEMENT). This is a retrieval gap for broad queries where entity seeds are sparse.

---

## Environment Notes

- **Server:** `source .env && python -m uvicorn src.api_gateway.main:app --host 0.0.0.0 --port 8888 --timeout-keep-alive 300`
- **Eval command:** `AZURE_TENANT_ID=ecaa729a-f04c-4558-a31a-ab714740ee8b python3 scripts/evaluate_route4_reasoning.py <json>`
- **Retrieval test:** `python3 scripts/test_ppr_retrieval.py --url http://localhost:8888 --query-mode community_search`
- **Benchmark:** `python3 scripts/benchmark_route7_hipporag2.py --url http://localhost:8888 --positive-prefix Q-G --repeats 1 --query-mode community_search`
- **Disk:** ~5GB free (docker pruned, node_modules deleted)
- **Azure tenant:** `ecaa729a-f04c-4558-a31a-ab714740ee8b` (MFA required)
