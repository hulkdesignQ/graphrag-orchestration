# Handover: Route 6 vs Route 7 Benchmark Comparison

**Date:** 2026-03-06

## Objective

Run Route 6 (Concept Search) benchmark tests against the deployed Route 7 (HippoRAG 2) endpoint and compare results across both routes' native question sets.

## Benchmark Setup

| Parameter | Value |
|-----------|-------|
| Deployed endpoint | `https://graphrag-api.salmonhill-df6033f3.swedencentral.azurecontainerapps.io` |
| Group ID | `test-5pdfs-v2-fix2` |
| Benchmark script | `scripts/benchmark_route7_hipporag2.py` (with `--force-route concept_search` for Route 6) |
| LLM judge | `scripts/evaluate_route4_reasoning.py` using `gpt-5.1` |
| Question bank | `docs/archive/status_logs/QUESTION_BANK_5PDFS_2025-12-24.md` |
| Auth | AAD token via `az account get-access-token` (deployed), `--no-auth` (local) |

## Results Summary

### Q-D Questions (Route 4/7 drift questions — 19 positive + 9 negative)

| Metric | Route 6 | Route 7 |
|--------|---------|---------|
| **Score** | **53/57 (93.0%)** | **55/57 (96.5%)** |
| Negative tests | 9/9 | 9/9 |
| Avg latency | ~9.2s | ~5.5s |
| Avg response length | ~1,780 chars | ~870 chars |

### Q-G Questions (Route 6/3 global questions — 19 positive + 9 negative)

| Metric | Route 6 | Route 7 |
|--------|---------|---------|
| **Score** | **52/57 (91.2%)** | **53/57 (93.0%)** |
| Negative tests | 9/9 | 9/9 |
| Avg latency | ~15s | ~7.5s |
| Avg response length | ~1,780 chars | ~870 chars |

### Key Takeaway

Route 7 beats or ties Route 6 on **both** question sets while being **40–50% faster** and producing **2× shorter** responses.

## Per-Question Overlap Analysis

### Q-G Set (19 questions)

| Category | Count | Questions |
|----------|-------|-----------|
| Both pass | 18 | Q-G1–G5, G7–G9, G11–G19 |
| Both fail | 1 | **Q-G6** |
| Route 6 only | 0 | — |
| Route 7 only | 0 | — |

### Q-D Set (19 questions)

| Category | Count | Questions |
|----------|-------|-----------|
| Both pass | 17 | Q-D1–D2, D4–D6, D8–D19 |
| Both fail | 0 | — |
| Route 6 only | 0 | — |
| Route 7 only | 2 | **Q-D3**, **Q-D7** |

**Zero questions where Route 6 passes and Route 7 fails.**

## Deep Dive: Interesting Questions

### Q-G6 — "List all named parties/organizations across the documents and which document(s) they appear in."

Both routes score **1/3**. Shared blind spot:

- **Route 6** lists 9 entities (includes County of Washburn, AAA, State of Idaho, Bayfront Animal Clinic) — richer enumeration but some are borderline per ground truth; misses holding tank party roles.
- **Route 7** lists 7 entities — misses holding tank parties, adds "John Doe" (a person, not org).
- Root cause: neither route's retrieval surfaces the holding-tank contract's signatory details adequately.

### Q-G10 — "Summarize each document's main purpose in one sentence."

Route 6 scores **3/3**, Route 7 scores **2/3**. Route 6's only advantage:

- **Route 6** produces richer per-document summaries with arbitration/exclusion details and nuanced contractual framing. Community summaries provide thematic context that PPR-retrieved chunks lack.
- **Route 7** gives correct but shallower summaries — misses nuances like warranty arbitration binding provisions.

### Q-D3 — Time windows (Route 7 rescues: 2/3 vs 1/3)

PPR graph traversal surfaces more cross-document temporal detail that cosine-only retrieval misses.

### Q-D7 — Latest date (Route 7 rescues: 3/3 vs 1/3)

Entity-linked PPR finds the purchase contract date through entity graph edges, while Route 6's sentence search misses it.

## Architecture Notes

### Route 7 does NOT use community summaries in synthesis

Route 7's synthesis context consists of:
1. **PPR-retrieved raw sentence chunks** — main evidence
2. **Entity-Document Map** — optional graph structural header for enumeration queries
3. **Document overviews** — sparse-retrieval fallback only (< 3 chunks)

The default `v3_keypoints` prompt (line 2545, `synthesis.py`) explicitly instructs: _"no summary paragraph, no headers, no preamble"_. Community summaries are a Route 6/Route 3 retrieval feature via `community_matcher`, not used in Route 7's synthesis path.

Route 7 does have an optional `ROUTE7_COMMUNITY_SEEDS` env var (default `"0"` / disabled) that uses community embeddings as **PPR seed nodes** — but this only influences graph traversal weighting, not the synthesis prompt content.

## Benchmark Artifacts

| File | Description |
|------|-------------|
| `benchmarks/route6_concept_r4questions_20260306T165608Z.json` | Route 6 on Q-D — raw results |
| `benchmarks/route6_concept_r4questions_20260306T165608Z.eval.md` | Route 6 on Q-D — eval (53/57) |
| `benchmarks/route7_hipporag2_r3questions_20260306T175720Z.json` | Route 7 on Q-G — raw results |
| `benchmarks/route7_hipporag2_r3questions_20260306T175720Z.eval.md` | Route 7 on Q-G — eval (53/57) |
| `benchmarks/route6_concept_r3questions_20260222T125043Z.eval.md` | Route 6 best Q-G baseline (52/57) |
| `benchmarks/route7_hipporag2_r4questions_20260305T185112Z.eval.md` | Route 7 deployed Q-D baseline (55/57) |

## Conclusion

Route 7 (HippoRAG 2) dominates Route 6 (Concept Search) across all metrics — higher accuracy, lower latency, and more concise output. The only marginal advantage Route 6 holds is on broad "summarize all documents" queries (Q-G10) where community summaries provide thematic framing. This single-question edge does not justify the 2× latency cost. Route 7 should remain the primary route for both drift and global question types.
