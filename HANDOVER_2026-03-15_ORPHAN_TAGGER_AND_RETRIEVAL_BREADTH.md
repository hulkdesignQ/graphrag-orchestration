# Handover: Orphan Sentence Tagger & Retrieval Breadth Gap

**Date:** 2026-03-15  
**Branch:** `fix/git-flow-cleanup`  
**Score:** 168/171 (98.2%) — Golden target: 169/171 (98.8%)

---

## What Was Done

### 1. Orphan Entity Fix (committed `c8bbcabb`)
- **Root cause:** `get_sentences_by_group()` included `__global__` sentences during indexing, creating entities with broken `text_unit_ids` pointing to non-existent sentence IDs.
- **Fix:** Scoped all 4 calls to `group_ids=[group_id]` (not `build_group_ids`).

### 2. PPR Text Dedup (committed `3da0ad7a`)
- Same PDFs indexed in both `test-5pdfs-v2-fix2` and `__global__` → PPR returned duplicate passages (24 passages = only 12 unique texts).
- **Fix:** Text-based dedup in `_fetch_sentences_by_ids()` using first 200 chars as key.
- **Impact:** 159 → 162/171 (+3 points)

### 3. v10_comprehensive Prompt (committed `21794a20`)
- Previous prompts had conflicting rules ("be exhaustive" vs "answer precisely what was asked").
- v10_comprehensive adds: "Be EXHAUSTIVE within scope", "Completeness over brevity".
- **Impact:** 162 → 168/171 (+6 points)

### 4. Orphan Sentence Concept Tagger (committed `99952be9` + `f7d10ae2`)
- **Problem:** Some sentences (procedural clauses like "3 business days cancellation") had zero entity MENTIONS — NER/triple extraction never extracted any entity from them. PPR can't reach them.
- **Solution (Step 4b in pipeline):** After triple extraction + co-occurrence edges:
  1. Detect sentences with no entity in `text_unit_ids`
  2. Send orphan sentences to LLM asking for 1-2 concept labels
  3. Creates/reuses Entity nodes with type="CONCEPT" and adds text_unit_ids
  4. **Deterministic keyword fallback** for any sentences LLM misses
- **Critical bug found & fixed (`f7d10ae2`):** The LLM call used `ainvoke()` (doesn't exist on `AzureOpenAI`). Fixed to `_achat_with_retry()` with `ChatMessage`. Tagger was silently failing the entire time.
- **Result:** 0 orphan sentences (was 15-19 with broken call). All Q-D3 target sentences (3/5/10 business days, 180-day rental, 60-day arbitration demand) now have entity connections.

---

## Current State

### Score Progression
| Change | Score | Δ |
|--------|-------|---|
| Pre-fixes baseline | 154/171 | — |
| Co-occurrence + NER + dedup fixes | 159/171 | +5 |
| + PPR text dedup | 162/171 | +8 |
| + v10_comprehensive prompt | **168/171** | +14 |
| + Orphan tagger (zero orphans) | **168/171** | +14 |
| Golden target | 169/171 | +15 |

### Q-D3 Remaining Gap (6/9, -3 points)
**Question:** `Compare "time windows" across the set: list all explicit day-based timeframes.`

**What's in the answer:** 60-day warranty, 60 days repair, 180 days arbitration, 90 days labor, 60 days notice, 12-month term.

**What's missing:** 10 business days (holding tank contract changes), 5 business days (notify agent), 3 business days (cancellation), 180-day rental threshold (short-term vs long-term), 60 days after service of complaint.

**Root cause diagnosed:** This is NOT an orphan/indexing problem anymore. All target sentences have entity connections (verified: 0 orphans). The issue is **PPR retrieval breadth**:
- The query seeds into warranty-focused entities (`90 days`, `repair`, `builder`, `warranty`)
- PPR traverses the warranty entity neighborhood
- The holding tank, property management, and purchase contract sentences are connected to DIFFERENT concept entities with no graph bridge
- PPR never reaches these entity clusters

**Evidence:** A fresh API call with a longer query ("What are all explicit day-based time windows or deadlines across all documents?") DID retrieve all items including 3/5/10 business days. The benchmark's shorter query doesn't generate broad enough seeds.

### Neo4j State (test-5pdfs-v2-fix2)
- 205 sentences, 408 entities, 827 MENTIONS, 6 communities
- 0 orphan sentences ✅
- All entities have MENTIONS edges ✅

---

## TODO List

### Priority 1: Fix Q-D3 Retrieval Breadth (168 → 171 target)
- [ ] **Enable community passage seeds for cross-doc queries** — Community summaries should mention timeframes from all documents. Seeding community-level passages would give PPR a cross-document bridge.
- [ ] **Increase PPR top_k** — Currently PPR returns 24-30 passages. Increasing could include more peripheral entity neighborhoods. Check if holding tank/PM sentences appear at lower PPR ranks.
- [ ] **Broader semantic passage seeds** — The 9 semantic seeds added are all warranty-focused. Consider adding DPR/sentence-embedding seeds that cover all documents regardless of entity graph.
- [ ] **Evaluate if the benchmark query itself should be expanded** — The golden answer might use a different retrieval approach; compare golden's retrieval metadata.

### Priority 2: Validate & Deploy
- [ ] **Run full benchmark 3x** to confirm 168/171 is stable (not variance)
- [ ] **Deploy to production** — The 4 committed fixes (orphan entities, PPR dedup, v10_comprehensive prompt, orphan tagger) are all production-ready
- [ ] **Reindex production groups** after deployment

### Priority 3: Future Improvements
- [ ] **Cross-document bridging edges** — Create entity relationships between concept entities across documents (e.g., "business days deadline" in holding tank ↔ "warranty period" in warranty)
- [ ] **Query expansion for global questions** — Detect cross-doc queries and auto-expand the query to mention each document
- [ ] **Tagger prompt quality** — Current prompt produces generic concepts. Could be improved with document-aware context.

---

## Key Files Changed
- `src/worker/hybrid_v2/indexing/lazygraphrag_pipeline.py` — Orphan entity fix (4 call sites), orphan sentence tagger (Step 4b + `_tag_orphan_sentences()`)
- `src/worker/hybrid_v2/routes/route_7_hipporag2.py` — PPR text dedup (`_fetch_sentences_by_ids`), default prompt → v10_comprehensive
- `src/worker/hybrid_v2/pipeline/synthesis.py` — v10_comprehensive prompt definition

## Commits (branch: fix/git-flow-cleanup)
```
f7d10ae2 Fix orphan tagger: use _achat_with_retry + keyword fallback
99952be9 Add orphan sentence concept tagger (Step 4b)
21794a20 Switch Route 7 default prompt to v10_comprehensive
3da0ad7a Add text dedup to PPR sentence fetch for multi-group overlap
c8bbcabb Fix orphan entities: scope indexing to own group_id only
```

## Commands
```bash
# Server
PYTHONUNBUFFERED=1 nohup python -m uvicorn src.api_gateway.main:app --host 0.0.0.0 --port 8888 --timeout-keep-alive 300 > /tmp/server.log 2>&1 &

# Reindex
GROUP_ID=test-5pdfs-v2-fix2 PYTHONPATH=. python3 scripts/index_5pdfs_v2_local.py

# Benchmark
python3 scripts/benchmark_route7_hipporag2.py --url http://localhost:8888 --no-auth --config-override rerank_dynamic_cutoff=1 --config-override rerank_relevance_threshold=0.25

# LLM eval
python3 scripts/evaluate_route4_reasoning.py benchmarks/<file>.json

# Check orphan sentences
# Direction: (Sentence)-[:MENTIONS]->(Entity), NOT reverse
MATCH (sent:Sentence {group_id: 'test-5pdfs-v2-fix2'})
WHERE NOT EXISTS { MATCH (sent)-[:MENTIONS]->(:Entity) }
RETURN count(sent) AS orphan_count
```

## Key Learnings
1. **LLM API:** Pipeline uses `self._achat_with_retry([ChatMessage(role="user", content=...)])`, NOT `ainvoke()` or `achat()` directly.
2. **MENTIONS direction:** `(Sentence)-[:MENTIONS]->(Entity)`, not reverse. Previous verification queries had wrong direction.
3. **Cache awareness:** After reindexing, always flush cache AND restart server. In-memory cache survives flush endpoint.
4. **Entity types:** All entities (OpenIE + concept) have `type="CONCEPT"` — this is the default, not a bug.
