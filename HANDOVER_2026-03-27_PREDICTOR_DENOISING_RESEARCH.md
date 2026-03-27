# Handover — 2026-03-27: Predictor Score Distribution Analysis & Denoising Research

## Status
Research phase — no production changes made. Uncommitted code in route_8 (context predictor experiment) should be reviewed before committing.

## Objective
Fix the last missing GT phrase (Washburn, Q-MH10) without regressing the 158/159 baseline.

## Root Cause Analysis

### Why Washburn is missed
- **Query**: "What is the total contract price on the invoice and how is the payment structured in installments?"
- **Washburn passage**: "The owner agrees to file a copy of this contract with the County of Washburn, WI Code SPS 383.21(2)5"
- The passage has **zero lexical overlap** with the query's surface question — it's only relevant because the contract it references IS the invoice document. This is a **multi-hop** relevance signal.

### Reranker noise floor (the core problem)
The reranker (voyage rerank-2.5) score distribution for Q-MH10's 156 APPNP passages:

```
Band         Count    Pct   
─────────────────────────────
0.60-1.00        1   0.6%   ← only the top passage has clear signal
0.50-0.55        1   0.6%
0.40-0.45        3   1.9%
0.35-0.40        8   5.1%
0.30-0.35        9   5.8%   ← top ~22 passages (14%) have meaningful scores
0.25-0.30       51  32.7%   ┐
0.20-0.25       80  51.3%   ┘ 131 passages (84%) in noise floor
0.15-0.20        3   1.9%
```

- **Max: 0.9297, Min: 0.1953, Mean: 0.2627, Std: 0.0730**
- **Washburn: rank 57/156, score 0.2578** — buried in the noise floor
- When APPNP teleports with α=0.65, every passage gets ~65% of its noisy reranker score as a floor, drowning out graph-based signal for multi-hop passages

### voyage-context-3 cosine distribution (for comparison)

```
Band         Count    Pct
─────────────────────────────
0.68-0.69        9   5.8%
0.67-0.68       17  10.9%
0.66-0.67       30  19.2%
0.65-0.66       40  25.6%   ← 69% in 0.64-0.67 noise band
0.64-0.65       37  23.7%
0.63-0.64        9   5.8%
0.62-0.63       11   7.1%
0.61-0.62        3   1.9%
```

- **Range: 0.6127–0.6891, Span: 0.076, Std: 0.0155**
- **Washburn: rank 17/156, score 0.6753** — ranks much higher than reranker (17 vs 57)
- But absolute discrimination is even worse (0.076 span vs 0.73 for reranker)
- Cosine captures topical/document-level relatedness; reranker captures direct QA relevance

## Experiments Tried This Session

| Approach | Washburn Rank | Full Benchmark | Notes |
|---|---|---|---|
| **Baseline** (reranker predictor, α=0.65) | 127/156 | **158/159** | Production config |
| Reranker + instruction prepend | — | 153/159 (-5) | Compresses top scores, net regression |
| APPNP α=0.50 (more graph weight) | — | 156/159 (-2) | Spreads score to noise |
| Context predictor: [query, passage] top_k=90 | 91 | 152/159 (-6) | Washburn just outside |
| Context predictor: [query, passage] top_k=95 | inside | 155/159 (-3) | Captures Washburn, other regressions |
| Context predictor: grouped by doc | inside | 148/159 (-10) | Loses query awareness |
| LLM score predictor | — | — | GPT-4.1 gave Washburn 0.0; user rejected |
| Reranker batch size (1/3/8) | — | — | Scores identical; reranker is pairwise |

## Key Findings

1. **Reranker batch size doesn't matter** — voyage rerank-2.5 scores each query-passage pair independently. Tested with 1, 3, 8 documents: Washburn always gets 0.2285 (later run: 0.2578).

2. **Reranker instruction** (prepend to query) marginally helps Washburn (+0.02) but globally compresses top scores, causing net regressions. The formal `instruction` API parameter is NOT supported by our MongoDB-proxied endpoint.

3. **Context predictor** (voyage-context-3 with query as context) ranks Washburn much higher (rank 17 vs 57) but doesn't improve the full benchmark because it has even less absolute score discrimination.

4. **The APPNP predictor in the original paper is query-free** — it's an MLP on node features, not a query-conditioned scorer. HippoRAG2 introduced query-dependence via the reranker.

5. **User rejected**: LLM-generated scores ("creation, not reliable"), LLM can only rank sequences.

## Next Steps: Reranker Score Denoising

The agreed direction is to **denoise the reranker scores** before feeding them to APPNP, rather than replacing the predictor. Four approaches to evaluate:

### 1. Threshold → Zero
Set reranker scores below a cutoff (e.g., 0.30) to 0. Only the top ~22 passages get non-zero predictions. Graph propagation spreads signal from these to neighbors (including Washburn via entity chains).

**Pros**: Simple, preserves reranker ordering for strong passages, lets graph do multi-hop.  
**Cons**: Threshold is a hyperparameter; may vary across queries.

### 2. Score Sharpening (Exponentiation)
Apply `score^n` (e.g., n=4): 0.93→0.75, 0.35→0.015, 0.25→0.004. Crushes the noise floor while preserving top-passage ordering.

**Pros**: Continuous (no hard cutoff), single hyperparameter (n).  
**Cons**: Still assigns small non-zero mass to noise passages.

### 3. Top-K Mask
Keep only the top K reranker scores, zero the rest. Rank-based rather than score-based.

**Pros**: Robust to absolute score shifts between queries.  
**Cons**: Fixed K may not suit all queries.

### 4. Z-Score + ReLU
Normalize to mean=0/std=1, then zero negatives. Only above-average passages survive.

**Pros**: Adaptive threshold per query.  
**Cons**: If distribution is highly skewed, threshold may be too aggressive.

### Recommendation
Start with **#1 (threshold)** at 0.30 — this zeroes the 84% noise floor and is simplest to test. If too query-sensitive, try **#2 (sharpening, n=3-4)** as a continuous alternative.

The key hypothesis: with the noise floor zeroed, APPNP propagation from strong passages will reach Washburn through entity chains (multi-hop), instead of Washburn being anchored to its own noisy 0.25 teleportation score.

## Uncommitted Changes

File: `src/worker/hybrid_v2/routes/route_8_hipporag2_community.py`
- `context_predictor` config option (~line 437)
- Step 3.6 context predictor block (~lines 1256-1275)
- `_context_predictor_scores()` method (~lines 3897-3960) — currently has grouped-by-doc approach (148/159 regression)
- These are experimental; **do not deploy**. Revert or gate behind config before committing.

## Server Notes
- Port 8888, started via `/tmp/start_srv.py` with `REQUIRE_AUTH=false`
- Must use `X-Group-ID: test-5pdfs-v2-enhanced-ex` header
- Route 8 via `force_route: hipporag2_community`
- Test group: `test-5pdfs-v2-enhanced-ex`
- Benchmark script: `scripts/test_ppr_retrieval.py --url http://localhost:8888 --group-id test-5pdfs-v2-enhanced-ex --question-set all`
