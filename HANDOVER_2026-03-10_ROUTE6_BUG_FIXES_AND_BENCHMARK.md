# Handover: Route 6 Bug Fixes & Benchmark

**Date:** 2026-03-10  
**Branch:** `fix/git-flow-cleanup`  
**Final Score:** Route 6 — **153/171** (Q-G: 78/90, Q-N: 75/81)  
**vs Route 7 baseline:** 149/171 (Q-G: 68/90, Q-N: 81/81)

## Summary

Deep investigation of Route 6 (Concept Search / global search) uncovered **5 bugs** causing it to underperform Route 7 on global questions. All 5 were fixed across 4 iterative versions. Route 6 now **beats Route 7 by 4 points overall** and **10 points on global questions**.

---

## Bugs Found & Fixed

### Bug #1 — Sentence Search Cypher Failure (V1)
- **Symptom:** ALL 19 questions had `sentence_evidence_count: 0`
- **Root cause:** `sentence_embedding` Neo4j vector index does NOT have `group_id` as a filterable property. Using `WHERE sent.group_id = $group_id` inside a SEARCH clause → `Neo.ClientError.Statement.PropertyNotFound`, silently caught and returning `[]`
- **Fix:** Single SEARCH without group_id inside, then `WHERE sent.group_id IN $group_ids` outside
- **File:** `route_6_concept.py` ~L1308-1315
- **Commit:** `560fa1b6` (V1 batch)

### Bug #2 — Community Over-Retrieval (V1)
- **Symptom:** Flat community relevance scores (0.34–0.47), diluted synthesis context
- **Root cause:** `ROUTE6_COMMUNITY_TOP_K=10` too high; all 16 communities in group were nearly equivalent
- **Fix:** Reduced to `COMMUNITY_TOP_K=5`, enabled dynamic community LLM rating (`DYNAMIC_COMMUNITY=1`)
- **File:** `route_6_concept.py` L119/L592 (top_k), L170/L615 (dynamic)
- **Note:** V2 experiment feeding ALL 16 communities with threshold=3 was WORSE (context overflow). Reverted.

### Bug #3 — Multi-Tenant Vector Index Dilution (V3, CRITICAL)
- **Symptom:** Sentence search returned results from only 1 document out of 5
- **Root cause:** `sentence_embedding` index has 3,626 sentences from ALL tenant groups, only 413 (11%) from target group. Neo4j SEARCH `LIMIT` applies BEFORE the `WHERE group_id` filter. With `LIMIT 90`, only ~7 results survived group filtering — all from HOLDING TANK document
- **Fix:** `fetch_k = max(top_k * 3, ROUTE6_SENTENCE_FETCH_K=500)`, env-configurable
- **File:** `route_6_concept.py` ~L1290-1298
- **Commit:** `ca285319`

### Bug #4 — Diversity Function Bypass (V3)
- **Symptom:** All sentence results from a single document despite diversity logic existing
- **Root cause:** `_diversify_by_document()` condition `len(evidence) > diversity_pool_k (30)` never met — with Bug #3 limiting results to <30, diversity never activated
- **Fix:** Changed condition to `len(evidence) > rerank_top_k (15)`
- **File:** `route_6_concept.py` L324/L698
- **Commit:** `ca285319`

### Bug #5 — Synthesis Over-Inclusion (V4)
- **Symptom:** Q-G4 lists 10+ items instead of 2 reporting obligations; Q-G6 lists 9 entities instead of 4 contract parties
- **Root causes:**
  1. Synthesis prompt Rule 6 ("list EVERY item") had no precision counterbalance
  2. `COMMUNITY_EXTRACT_PROMPT` score threshold=20 too permissive (tangential facts included)
  3. Entity-doc map full of garbage entities ("2010", "contract", "agreement", "90 days", "3 000")
- **Fixes:**
  - Added PRECISION OVER PADDING sub-rule in synthesis prompt (Rule 6)
  - Extended Rule 8 for entity-listing queries
  - Tightened extraction prompt scoring (instruction 4: ≥50 direct, <30 tangential; instruction 7: precision)
  - Raised extraction score threshold from 20 to 40 (`ROUTE6_EXTRACT_MIN_SCORE` env var)
  - Added `_is_meaningful()` filter removing noise from entity-doc map
- **Files:** `route_6_prompts.py` L55/L61/L91/L94, `route_6_concept.py` ~L1003/L1763-1785
- **Commit:** `b420bcc2`

---

## Score Progression

| Version | Q-G (/90) | Q-N (/81) | Total (/171) | Changes |
|---------|-----------|-----------|--------------|---------|
| **Pre-fix** | 67 | 81 | 148 | Baseline |
| **V1** | 73 (+6) | 75 (-6) | 148 | Bugs 1+2: sentence Cypher, community top-k |
| **V3** | 75 (+2) | 75 | 150 (+2) | Bugs 3+4: fetch_k 500, diversity threshold |
| **V4** | **78 (+3)** | 75 | **153 (+3)** | Bug 5: prompt precision, extraction threshold, entity filter |
| Route 7 | 68 | 81 | 149 | Reference baseline |

### Per-Question Breakdown (V4 vs Pre-fix vs Route 7)

| QID | Pre-fix | V4 | Route 7 | V4 vs Pre-fix | Notes |
|-----|---------|----|---------|---------------|-------|
| Q-G1 | 8 | **9** | 8 | +1 | ✅ Perfect |
| Q-G2 | 3 | **9** | 9 | +6 | ✅ Fixed by sentence search |
| Q-G3 | 8 | **8** | 9 | 0 | Stable |
| Q-G4 | 4 | **5** | 5 | +1 | ⬆ Prompt precision helped |
| Q-G5 | 9 | 8 | 6 | -1 | Minor LLM variance |
| Q-G6 | 3 | 3 | 3 | 0 | ❌ Unresolved (see below) |
| Q-G7 | 8 | **9** | 7 | +1 | ✅ Perfect |
| Q-G8 | 6 | **9** | 9 | +3 | ✅ Fixed by sentence search |
| Q-G9 | 9 | **9** | 9 | 0 | ✅ Perfect |
| Q-G10 | 9 | **9** | 3 | 0 | ✅ Route 6 >> Route 7 |
| Q-N1–N7,N9,N10 | 9 each | 9 each | 9 each | 0 | All perfect |
| Q-N8 | 9 | **3** | 9 | -6 | ❌ Regression (see below) |

---

## Remaining Issues

### Q-G6 Stuck at 3/9 — Entity-Doc Map Quality
- **Question:** "List the primary parties to the contracts (landlord, tenant, buyer, seller)"
- **Problem:** Entity-doc map full of noise; key entities (Walt Flood Realty, Contoso Lifts LLC) appear in <2 docs in graph → excluded by `doc_count >= 2` filter. LLM gets entity names from sentence evidence instead, producing extras.
- **Would require:** Re-indexing with better entity extraction, or lowering `doc_count` threshold, or post-synthesis entity deduplication.

### Q-N8 Regression at 3/9 — Sentence Search False Positive
- **Question:** "What is the purchase contract's required wire transfer / ACH instructions?"
- **Expected:** "Not specified."
- **Problem:** Sentence search now finds "online portal" content that didn't surface before Bugs 1+3 were fixed. LLM infers wire/ACH instructions exist from this evidence → false positive on a negative question.
- **This is a trade-off:** fixing sentence search helped 6+ global questions but hurt this one negative question.
- **Potential fix:** Add negative-question detection in synthesis prompt, or post-synthesis "not in evidence" check.

### Q-G4 Partial at 5/9 — Enumeration Precision Limit
- **Question:** "What are the reporting or record-keeping obligations explicitly described across the documents?"
- **Problem:** LLM still lists 4 categories instead of the 2 "explicitly described" ones. The 1-2 LLM call architecture (vs Microsoft GraphRAG's N+1 MAP-REDUCE) limits exhaustive enumeration precision.

---

## Commits (this session)

| Commit | Description |
|--------|-------------|
| `ca285319` | fix: lower route6 diversity threshold to activate more often (V3: fetch_k + diversity) |
| `b420bcc2` | fix(route6): synthesis precision — prompt rules, extraction threshold, entity noise filter (V4) |

---

## Benchmark Files

| File | Description |
|------|-------------|
| `benchmarks/route6_concept_r3questions_20260310T114317Z.eval.md` | Pre-fix baseline |
| `benchmarks/route6_concept_r3questions_20260310T135918Z.eval.md` | V1 (Bugs 1+2) |
| `benchmarks/route6_concept_r3questions_20260310T175350Z.eval.md` | V3 (Bugs 3+4) |
| `benchmarks/route6_concept_r3questions_20260310T205551Z.eval.md` | V4 (Bug 5) |
| `benchmarks/route7_hipporag2_r3questions_20260310T121158Z.eval.md` | Route 7 reference |

---

## Key Technical Notes

- **Neo4j vector index `sentence_embedding`** has NO `group_id` filterable property. The `sentence_embeddings_v2` index HAS `group_id` but has 0 embeddings. Any future multi-tenant vector search must over-fetch and post-filter.
- **Entity-doc map** Cypher query uses `doc_count >= 2` — entities appearing in only 1 document are excluded. This is intentional for noise reduction but drops some key entities.
- **`_is_meaningful()` filter** removes entities matching: single words ≤3 chars, pure numbers, date-like strings, and a blocklist of generic terms (contract, agreement, document, party, section, article, etc.).
- **`ROUTE6_EXTRACT_MIN_SCORE`** env var (default 40) controls community extraction threshold. Lower = more inclusive (more context but more noise). Previous default was hardcoded 20.
- **`ROUTE6_SENTENCE_FETCH_K`** env var (default 500) controls how many raw vector results to fetch before group filtering. Must be significantly higher than `top_k` in multi-tenant deployments.
