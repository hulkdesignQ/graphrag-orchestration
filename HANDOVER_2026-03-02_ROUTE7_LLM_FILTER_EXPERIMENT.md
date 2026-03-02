# Handover: Route 7 — Corpus-Wide Reranking (57/57) & LLM Filter Experiment — 2026-03-02

**Date:** 2026-03-02  
**Status:** Route 7 Q-D score at **57/57 (100%)** via step 4.6 corpus-wide reranking. LLM relevance filter (step 4.7) prototyped and benchmarked — **net negative**, disabled by default. Q-G (global/thematic) questions remain at 24/30 baseline.  
**Previous handover:** `HANDOVER_2026-03-01_ROUTE7_GAP1_PPR_TOP_K_100.md`  
**Architecture doc:** `ARCHITECTURE_DESIGN_LAZY_HIPPO_HYBRID.md` §39 (10 subsections)  
**Current HEAD:** `fed123b7` (docs: add reranker clarifications, latency details, instruction param, LLM filter proposal)

---

## 1. What Was Done Today

### 1.1 Step 4.6: Corpus-Wide Cross-Encoder Reranking — 57/57

Added `_rerank_all_passages()` as a parallel retrieval channel in Route 7:

1. After PPR (step 4), run Voyage `rerank-2.5` cross-encoder on **ALL ~202 sentences** in the corpus
2. Take the top-K (default 50) reranked passages
3. Merge into PPR results, deduplicating against PPR's top passages
4. ~35 new passages injected on average

**Critical bug fixed:** PPR returns non-zero probability for ALL passages (Markov chain property). The dedup set was built from `passage_scores` (all 202 IDs) instead of `passage_scores[:ppr_passage_top_k]` (top 20 IDs), so zero passages were ever injected. Fix: `ppr_top_set = {cid for cid, _ in passage_scores[:ppr_passage_top_k]}`.

**Score progression:**
| Config | Q-D Score | Notes |
|--------|-----------|-------|
| Baseline (no rerank-all) | 53/57 | PPR + DPR only |
| Rerank-all top_k=10 | 54/57 | Insufficient coverage |
| Rerank-all top_k=20 | 56/57 | Getting close |
| **Rerank-all top_k=50** | **57/57** | **Perfect score** |

**LLM eval confirmed:** All 19 Q-D questions scored 3/3, all 9 Q-N (negative) tests PASS.

**Commits:**
- `203b3e9b` — feat(route7): add corpus-wide cross-encoder reranking (step 4.6)
- `6601f944` — docs: Route 7 rerank-all journey and exhaustive vs conceptual architecture
- `fed123b7` — docs: add reranker clarifications, latency details, instruction param, LLM filter proposal

### 1.2 Architecture Documentation — §39

Wrote comprehensive §39 in `ARCHITECTURE_DESIGN_LAZY_HIPPO_HYBRID.md` (10 subsections):

- **§39.2** Journey from failure (upstream alignment → 39/57) to success (rerank-all → 57/57)
- **§39.3** Pipeline architecture — rerank-all is NOT seeding, it's a post-PPR parallel channel
- **§39.4** Origin — rerank-all is **our innovation**, not upstream HippoRAG 2 (upstream uses DSPy LLM filter on triples)
- **§39.5** Exhaustive vs Conceptual retrieval insight:
  - **PPR** = graph traversal → good for conceptual/entity-linked queries
  - **Rerank-all** = cross-encoder on all passages → essential for exhaustive/enumerative queries
  - They're **complementary**: the 53→57 improvement was entirely exhaustive-type gaps
- **§39.6** Performance metrics: mean latency 4,753ms, mean length 1,201 chars, rerank step ~407ms
- **§39.7** Cross-route Q-G benchmark: Route 7 = 24/30, Route 6 = 25/30

### 1.3 Step 4.7: LLM Relevance Filter Experiment — NET NEGATIVE

**Hypothesis:** Route 7 over-includes for thematic (Q-G) questions because ~55 passages are too many — the synthesis LLM extracts facts beyond the question's scope. An LLM filter between retrieval and synthesis could reduce over-inclusion.

**Implementation:**
- Added `_llm_relevance_filter()` method using gpt-4.1-mini
- Sends all candidate passages in one batch prompt asking LLM to return indices of directly relevant passages
- Controlled by `ROUTE7_LLM_FILTER` env var (default: `"0"` = disabled)
- Model configurable via `ROUTE7_LLM_FILTER_MODEL` (default: `gpt-4.1-mini`)

**Benchmark results (Q-G + Q-N combined):**

| Config | Q-G | Q-N | Total | Notes |
|--------|-----|-----|-------|-------|
| **No filter (baseline)** | **24/30** | **27/27** | **51/57** | Best overall |
| Filter v1 (no safety guard) | 24/30 | 9/27 | 33/57 | Catastrophic Q-N regression |
| Filter v2 (20% safety guard) | 22/30 | 27/27 | 49/57 | Guard too conservative |
| Filter v3 (empty-only guard) | 21/30 | 27/27 | 48/57 | Q-G hurt, Q-N protected |

**Per-question detail (Q-G, no filter → filter v1):**
| QID | No Filter | Filter v1 | Delta | Root Cause |
|-----|-----------|-----------|-------|------------|
| Q-G1 | 3 | 2 | -1 | Filter removed passages needed for cross-doc termination rules |
| Q-G4 | 1 | 2 | +1 | ✅ Filter correctly scoped reporting obligations |
| Q-G5 | 3 | 2 | -1 | Filter removed dispute resolution passages |
| Q-G8 | 2 | 3 | +1 | ✅ Filter helped focus insurance/liability answer |
| Q-G10 | 3 | 1 | -2 | Filter removed passages needed for doc summaries |

**Root cause of failure:**
1. **Q-N hallucination:** When the filter removes all/most passages (e.g., "bank account number" → 0 kept), the synthesis LLM fabricates answers. Safety guard (skip if 0 kept) fixes Q-N but blocks Q-G improvements too.
2. **Precision vs recall tradeoff:** The filter can't distinguish "tangentially related" (should remove) from "relevant but from a different document" (should keep). For exhaustive Q-G questions that span all 5 documents, aggressive filtering removes needed content.
3. **Fundamental mismatch:** Q-G questions ARE exhaustive — they need comprehensive multi-document coverage. The filter's precision gains are offset by recall losses.

**Conclusion:** The LLM filter approach doesn't work for this corpus/question mix. The code remains in the codebase (disabled by default) for future experimentation. Better approaches for Q-G improvement would be synthesis prompt tuning or Route 6's community MAP-REDUCE.

### 1.4 Key Architectural Insight: Exhaustive vs Conceptual Retrieval

| Capability | PPR | DPR | Rerank-all | LLM Filter |
|------------|-----|-----|------------|------------|
| **Exhaustive** ("list ALL X") | ✗ (seed-limited) | ✗ (conceptual gap) | ✓ (complete recall) | ✗ (removes needed passages) |
| **Conceptual** ("what if Y?") | ✓ (graph traversal) | ✓ (single-concept) | ✓ (supplementary) | Neutral |
| **Thematic** ("summarize theme X") | Partial | Partial | Over-includes | ✗ (can't distinguish scope) |

Route 6's community MAP-REDUCE remains structurally better for thematic queries (25/30 vs 24/30) because community summaries pre-digest content into thematic groups.

---

## 2. Current State

### Production Config (committed, pushed)
```
ROUTE7_RERANK_ALL=1          # Enable corpus-wide reranking
ROUTE7_RERANK_ALL_TOP_K=50   # Top-50 reranked passages merged into PPR
ROUTE7_LLM_FILTER=0          # LLM filter disabled (net negative)
```

### Scores
- **Q-D (multi-hop): 57/57 (100%)** — perfect, all 19 questions × 3 runs = 3/3
- **Q-N (negative): 27/27 (100%)** — all 9 negative tests PASS
- **Q-G (global/thematic): 24/30 (80%)** — unchanged from baseline

### Uncommitted Changes
```
src/worker/hybrid_v2/routes/route_7_hipporag2.py  (+130 lines)
  - Step 4.7 LLM filter code (disabled by default via ROUTE7_LLM_FILTER=0)
  - _llm_relevance_filter() method
  - Safety guard: skip filter if it returns 0 passages
  - json import added
```

### Running Server
- Shell 653 (async), port 8000
- Env: `ROUTE7_RERANK_ALL=1 ROUTE7_RERANK_ALL_TOP_K=50 ROUTE7_RETURN_TIMINGS=1`
- LLM filter OFF

---

## 3. TODO List

### Immediate — Commit & Deploy

- [ ] **Commit step 4.7 LLM filter code** — Disabled by default. Keep as experimental feature. Clean commit message documenting it's net negative for current corpus.
- [ ] **Deploy to cloud** — Push to main triggers CI/CD. Verify 57/57 on cloud.
- [ ] **Run cloud Q-D benchmark** — Confirm cloud deployment matches local 57/57.

### Q-G Improvement — Alternative Approaches

- [ ] **Synthesis prompt tuning** — Add instruction to synthesis LLM: "Only include information directly answering the specific question. Do not include tangentially related facts." This is lower-risk than passage filtering.
- [ ] **Voyage rerank-2.5 instruction parameter** — Use `instruction` kwarg in cross-encoder call to bias toward precision: `instruction="Select passages that directly answer the specific question asked"`. See §39.3.1 in architecture doc.
- [ ] **Dynamic passage_limit** — Instead of fixed top-50, use the reranker score distribution to set a natural cutoff (e.g., keep passages with score > 0.3).
- [ ] **Route selection optimization** — Route Q-G-style questions to Route 6 (community MAP-REDUCE) automatically via the hybrid router. Route 7 handles Q-D; Route 6 handles Q-G.

### Upstream Alignment — Carried Over from 2026-03-01

- [ ] **P0: Entity seed IDF + mean-normalization** — Upstream divides each entity's seed weight by `entity_doc_frequency` then by `num_facts`. Currently raw sum. (Tested Mar 1: net negative for our corpus — IDF penalizes cross-document entities.)
- [ ] **P1: Min-max normalize DPR passage scores** — Normalize to [0,1] range. (Tested Mar 1: neutral to negative.)
- [ ] **P2: Entity seed top-K=5 filter** — Zero out all but top-5 entities. (Already matching upstream ✅.)
- [ ] **Increase triple_top_k** — From 5 to 10-20 for broader entity seed coverage. (Tested Mar 1: Q-D8 regressed.)

> **Note:** All P0/P1/P2 upstream alignment changes were A/B tested and found neutral-to-negative for our 5-PDF corpus. Upstream was optimized for Wikipedia QA (1000s of passages); our corpus has fundamentally different statistics. **55/57 is the PPR ceiling; the 53→57 jump came entirely from rerank-all.**

### Sentence Extraction — Carried Over

- [ ] **Lower `SKELETON_MIN_SENTENCE_CHARS` 30→20** — Rescue short legal sentences.
- [ ] **Tighten ALL_CAPS word threshold 10→6** — Preserve binding legal statements.
- [ ] **`_is_kvp_label` word threshold 8→10** — Prevent false positives.
- [ ] **`numeric_only` alpha threshold 10→6** — Recover "Invoice #1256003", "Total: $29,900".
- [ ] **Whitespace-normalize dedup key** — `re.sub(r'\s+', ' ', text).strip().lower()`.

### Infrastructure — Carried Over

- [ ] **Investigate GDS Aura connectivity** — 0 communities and 0 KNN edges on cloud reindexes.
- [ ] **Cloud query 500 error investigation** — Intermittent.
- [ ] **Test CU (Content Understanding) page-level extraction** — CU is deployed; test quality.

---

## 4. Benchmark Files

| File | Config | Score |
|------|--------|-------|
| `route7_hipporag2_r4questions_20260302T170244Z.json` | Q-D, rerank-all top_k=50 | **57/57** |
| `route7_hipporag2_r3questions_20260302T174213Z.json` | Q-G, rerank-all, no filter | 24/30+27/27=51/57 |
| `route7_hipporag2_r3questions_20260302T183315Z.json` | Q-G, filter v1 (no guard) | 24/30+9/27=33/57 |
| `route7_hipporag2_r3questions_20260302T183955Z.json` | Q-G, filter v2 (20% guard) | 22/30+27/27=49/57 |
| `route7_hipporag2_r3questions_20260302T184413Z.json` | Q-G, filter v3 (empty guard) | 21/30+27/27=48/57 |

---

## 5. How to Resume

```bash
cd /workspaces/graphrag-orchestration

# 1. Check current state
git --no-pager log --oneline -5
git --no-pager diff --stat

# 2. Commit the LLM filter code (disabled by default)
git add src/worker/hybrid_v2/routes/route_7_hipporag2.py
git commit -m "feat(route7): add experimental LLM relevance filter (step 4.7, disabled)

Adds _llm_relevance_filter() as optional step between retrieval and
synthesis. Controlled by ROUTE7_LLM_FILTER env var (default: '0').

Benchmark result: net negative for current corpus.
- Q-G: 24/30 → 21-24/30 (no improvement, some regression)
- Q-N: 27/27 → 9-27/27 (hallucination risk without safety guard)

Root cause: filter cannot distinguish 'tangentially related' from
'relevant but from a different document'. Exhaustive queries need
comprehensive coverage that aggressive filtering destroys.

Code retained for future experimentation with improved prompts,
different models, or score-based thresholds.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

# 3. Start local API
find src -name '*.pyc' -delete
ROUTE7_RERANK_ALL=1 ROUTE7_RERANK_ALL_TOP_K=50 ROUTE7_RETURN_TIMINGS=1 \
  python3 -c "
import signal; signal.signal(signal.SIGTERM, lambda s,f: None)
import uvicorn; uvicorn.run('src.api_gateway.main:app', host='0.0.0.0', port=8000, log_level='info')
"

# 4. Run Q-D benchmark (should be 57/57)
python3 scripts/benchmark_route7_hipporag2.py \
  --url http://localhost:8000 --no-auth --repeats 1

# 5. LLM eval
python3 scripts/evaluate_route4_reasoning.py benchmarks/route7_hipporag2_r4questions_<timestamp>.json
```

---

## 6. Benchmark History (Route 7)

| Date | Config | Q-D | Q-G | Q-N | Notes |
|------|--------|-----|-----|-----|-------|
| Feb 24 | v7.0, 18 chunks | 55/57 | — | — | Pre-reranker best |
| Feb 26 | v7.2, rerank top_k=30 | 56/57 | — | — | All-time PPR+reranker best |
| Mar 1 | v7.4, MENTIONS=1.0, DPR_TOP_K=20, reranker ON | 54-55/57 | — | — | Edge fix only |
| **Mar 2** | **v7.4 + rerank-all top_k=50** | **57/57** | 24/30 | 27/27 | **Perfect Q-D** |
| Mar 2 | + LLM filter (v1, no guard) | — | 24/30 | 9/27 | Q-N catastrophe |
| Mar 2 | + LLM filter (v3, empty guard) | — | 21/30 | 27/27 | Q-G worse |

**Production config: rerank-all ON, LLM filter OFF.**
