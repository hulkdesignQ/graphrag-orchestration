# Handover: Route 6 & Route 8 — MAP-REDUCE Experiments & Benchmark Progress

**Date:** 2026-03-16  
**Branch:** `fix/git-flow-cleanup`  
**Status:** Route 6 at 156/171 (91.2%); Route 8 at 51/57 (89.5%); next steps documented

---

## Context

Route 8 (dedicated global/cross-document search) was built this session with per-document **map-reduce synthesis**, achieving:

- **Q-D3:** 2/6 → **6/6** (consistent)
- **Q-G avg containment:** 0.58 → **0.79**
- **Negative tests:** **9/9 PASS**
- **LLM eval (GPT-5.1):** **51/57 (89.5%)**

The one failure: **Q-G6 scored 1/3** — "List all named parties/organizations across all documents."

---

## Root Cause Analysis (Q-G6)

### Missing entities
| Entity | Doc | Root Cause | Status |
|--------|-----|------------|--------|
| **Bayfront Animal Clinic** | purchase_contract | PPR only retrieved 2 chunks from this doc; the "Job Name: Bayfront Animal Clinic" sentence wasn't among them | ✅ **FIXED** by min_chunks_per_doc |
| **Building Contractors Association of South East Idaho** | WARRANTY footer | Sentence is at index 83/85 (page footer). WARRANTY has 36+ PPR chunks, but this footer isn't one of them. Entity typed as `CONCEPT` not `ORGANIZATION` so entity-doc-map skips it. | ❌ Still missing |

### Why PPR misses these
- PPR ranks by structural importance (edges, PageRank). Peripheral entities in under-represented docs get low scores.
- `purchase_contract` only got 2 PPR chunks; warranty has 36 but the footer wasn't included.
- Entity-doc-map query filters by `e.type IN ['ORGANIZATION', 'PERSON']` — both missing entities are typed `CONCEPT` in Neo4j.

---

## Changes Made (UNCOMMITTED on `fix/git-flow-cleanup`)

### 1. Min chunks per document guarantee (Step 45d)
**File:** `src/worker/hybrid_v2/routes/route_8_hipporag2_community.py`

- **Config toggle:** `min_chunks_per_doc` / `ROUTE8_MIN_CHUNKS_PER_DOC` (default 0, preset `community_search` sets 5)
- **Logic:** After all injection steps (community, entity), counts chunks per document. For under-represented docs (fewer than N chunks), fetches evenly-spaced sentences from Neo4j and appends to `pre_fetched_chunks`.
- **Result:** Bayfront Animal Clinic now appears in answer ✅

### 2. Graph structural header passed to map-reduce REDUCE step
- `graph_structural_header` (entity-doc map) now flows into `_map_reduce_synthesize()` 
- Appended to REDUCE prompt with instruction to supplement answer with entities from knowledge graph
- **Result:** Currently returns 0 rows because entity types don't match (see bugs below)

---

## Known Bugs to Fix

### Bug 1: min_chunks_per_doc counts ALL documents as having 0 chunks
**Symptom:** Log shows `"under_represented": [["doc_439e...", 0], ["doc_5bc4...", 0], ...]` — all 10 docs show 0 existing chunks even though 117 PPR chunks were fetched.

**Root cause:** Document ID mismatch. The `pre_fetched_chunks` list has `document_id` fields from `_fetch_sentences_by_ids()`, but they may be stored under a different key or the format differs from what the Sentence nodes store in `s.document_id`. 

**How to debug:**
```python
# Add logging right after _doc_counts is built:
logger.info("debug_doc_counts", 
    sample_chunk_doc_ids=[c.get("document_id","") for c in pre_fetched_chunks[:5]],
    neo4j_doc_ids=[d["doc_id"] for d in _all_docs[:5]])
```

**Likely fix:** Check if `_fetch_sentences_by_ids()` returns `document_id` in a metadata sub-dict (`chunk.get("metadata", {}).get("document_id")`) rather than top-level. The MAP grouping code already handles this with the fallback chain (lines 3194-3201).

### Bug 2: Entity-doc-map returns 0 rows for ORGANIZATION/PERSON types
**Symptom:** Log shows `"entity_types": ["ORGANIZATION", "PERSON"], "rows_found": 0`

**Root cause:** The entity type values in Neo4j may use a different casing or format than what the query expects. The query uses `e.type IN $entity_types` with `["ORGANIZATION", "PERSON"]`, but entities may be stored with different type values.

**How to debug:**
```cypher
MATCH (e:Entity)
WHERE e.group_id IN ['test-5pdfs-v2-fix2', '__global__']
RETURN DISTINCT e.type, count(e)
ORDER BY count(e) DESC
```

**Possible causes:**
- Entity types might be lowercase (`organization` vs `ORGANIZATION`)
- Entity types might use different labels (`ORG` vs `ORGANIZATION`)
- The `IN_DOCUMENT` relationship might not exist (the Cypher uses `(tc:Sentence)-[:IN_DOCUMENT]->(d:Document)`)

### Bug 3: "Building Contractors Association" typed as CONCEPT
Even after fixing Bug 2, this entity is typed `CONCEPT` not `ORGANIZATION`. Options:
- **Option A:** Broaden entity-doc-map to include `CONCEPT` type for org-related queries
- **Option B:** Accept the limitation — it's a page footer watermark, arguably not a "party" to any agreement
- **Option C:** Fix entity types during indexing (entity extraction prompt improvement)

---

## TODO List (Priority Order)

### Must Do
- [ ] **Fix Bug 1:** Debug document_id mismatch in min_chunks_per_doc. The supplementation logic works (adds 41 chunks) but targets wrong docs because matching fails. This is the highest-priority fix — once working, will ensure every doc has proper representation.
- [ ] **Fix Bug 2:** Debug entity-doc-map returning 0 rows. Run the diagnostic Cypher above to check actual entity type values. Fix casing/format mismatch in the query.
- [ ] **Commit the current Route 8 changes** (min_chunks_per_doc + graph_structural_header in REDUCE)

### Should Do
- [ ] **Re-run full Q-G benchmark** after fixing Bugs 1 & 2 to measure Q-G6 improvement
- [ ] **Run LLM eval** to see if Q-G6 goes from 1/3 → 2/3 or 3/3
- [ ] **Bake default config** into Route 8 preset: `map_reduce_synthesis=1`, `rerank_dynamic_cutoff=0`, `rerank_top_k=260`, `max_chunks_per_doc=5`, `min_chunks_per_doc=5`

### Nice to Have
- [ ] **Improve 2/3 scores** (Q-G5, Q-G7, Q-G8, Q-G9) — mostly minor retrieval gaps
- [ ] **Router integration** — teach auto-router to send global/cross-doc queries to Route 8
- [ ] **Push to remote** and create PR

---

## Key Files

| File | Purpose |
|------|---------|
| `src/worker/hybrid_v2/routes/route_8_hipporag2_community.py` | Route 8 implementation (3400+ lines). Key sections: preset at line 198, config at line 432, min_chunks_per_doc at step 45d (~line 1384), MAP prompt at ~line 3108, REDUCE prompt at ~line 3140, `_map_reduce_synthesize()` at ~line 3181 |
| `scripts/benchmark_route7_hipporag2.py` | Benchmark runner. Usage: `--force-route hipporag2_community --config-override map_reduce_synthesis=1 --positive-prefix Q-G` |
| `scripts/evaluate_route4_reasoning.py` | LLM-as-Judge evaluator (gpt-5.1) |
| `benchmarks/hipporag2_community_r3questions_20260316T180253Z.json` | Latest benchmark (v5) |
| `benchmarks/hipporag2_community_r3questions_20260316T180253Z.eval.md` | LLM eval report: 51/57 (89.5%) |

## Testing Commands

```bash
# Server
PYTHONUNBUFFERED=1 nohup python -m uvicorn src.api_gateway.main:app --host 0.0.0.0 --port 8888 --timeout-keep-alive 300 > /tmp/server.log 2>&1 &

# Single Q-G6 test
curl -s http://localhost:8888/hybrid/query \
  -H 'Content-Type: application/json' \
  -H 'X-Group-ID: test-5pdfs-v2-fix2' \
  -d '{"query": "List all named parties/organizations across the documents and which document(s) they appear in.", "group_id": "test-5pdfs-v2-fix2", "force_route": "hipporag2_community", "config_overrides": {"map_reduce_synthesis": "1", "rerank_dynamic_cutoff": "0", "rerank_top_k": "260", "max_chunks_per_doc": "5", "min_chunks_per_doc": "5"}}'

# Full benchmark
PYTHONPATH=. python3 scripts/benchmark_route7_hipporag2.py \
  --force-route hipporag2_community \
  --config-override map_reduce_synthesis=1 rerank_dynamic_cutoff=0 rerank_top_k=260 max_chunks_per_doc=5 min_chunks_per_doc=5 \
  --positive-prefix Q-G

# LLM eval
PYTHONPATH=. python3 scripts/evaluate_route4_reasoning.py benchmarks/<file>.json
```

## Committed Changes (3 commits on `fix/git-flow-cleanup`)

1. `81ad4c25` — feat(route8): per-document map-reduce synthesis — Q-D3 from 2/6 → 6/6
2. `b7e04f95` — feat(route8): improve map-reduce prompts — broad MAP + strict REDUCE  
3. `3ab59213` — feat(route8): quote validation + refined REDUCE refusal logic

## Uncommitted Changes (Route 8 only)

- `min_chunks_per_doc` config toggle + Step 45d supplementation logic (~90 lines)
- `graph_structural_header` passed to `_map_reduce_synthesize()` REDUCE step
- `community_search` preset includes `min_chunks_per_doc: 5`

---

## Route 6 — EXTRACTION FIDELITY Rule & MAP-REDUCE Experiment

### Score Progression
| Change | Score | Key Deltas |
|--------|-------|-----------|
| Prior baseline | **156/171** | Q-G7: 4-6/9 variance |
| + EXTRACTION FIDELITY rule | **156/171** | Q-G7 isolated: 4→8/9 |
| + MAP-REDUCE synthesis | 141-142/171 | Q-G1 crash 9→3, Q-G9 crash 9→5 |
| Reverted MAP-REDUCE | **156/171** | Restored baseline |

### Key Discovery: Extraction Is Perfect, Synthesis Drops Items
- Debug logging at `_extract_one()` showed ALL missing Q-G7 items ("60 days notice," "$300 approval," "written consent," "changes in writing") present in extraction output with scores 80-100
- All 30 key points reaching synthesis contain all needed items
- **Root cause**: Synthesis LLM non-deterministically drops items from large context (30+ points)
- This is purely a synthesis attention problem, not retrieval or extraction

### EXTRACTION FIDELITY Rule (Committed: `adcda8e7`)
- Balances Q-G7 (broad: "written approval" = notice mechanism) with Q-G4 (narrow: "warranty notification" ≠ record-keeping)
- Positive examples: "written notice, written approval, written consent, agreement in writing all qualify as notice/delivery mechanisms"
- Negative examples: "warranty-defect notification is a notice mechanism, not a record-keeping obligation"
- Also softened PRECISION OVER PADDING by removing "do NOT conflate different obligation categories" example

### MAP-REDUCE Synthesis Experiment (Tested & Reverted: `a8b6a4d8`)
**Architecture:** Per-community MAP mini-answers → REDUCE merge (mirroring extraction pattern)

**Isolated results were spectacular:**
- Q-G7: **9/9 (3,3,3)** — perfect, up from 4/9 baseline
- Q-G8: **9/9 (3,3,3)** — perfect

**Full benchmark failed across 3 variants (all 141-142/171):**
- v1: Q-G1 crashed 9→3 (purchase contract cancellation not in any community's MAP)
- v2 (+ sentence evidence): Q-G1 restored 9/9, but Q-G9 still 5/9, Q-G7 only 4/9
- v3 (+ PRECISION rules): Still 141/171

**Why MAP-REDUCE doesn't work for synthesis:**
- Per-community MAP fragmenting cross-document context that synthesis needs
- Each MAP call independently over-includes borderline items (e.g., warranty limitations as "forfeiture terms")
- REDUCE step blindly merges, amplifying over-inclusion
- MAP works for extraction ("what facts exist?") but not synthesis ("how do these facts answer the query?")

### Remaining Route 6 Score Gaps (from 156/171)
| Q | Score | Root Cause |
|---|-------|-----------|
| Q-G7 | 4-6/9 | Synthesis drops items despite extraction finding them (variance) |
| Q-G4 | 5/9 | Missing inventory/furnishings detail; over-inclusion in 1/3 runs |
| Q-G3 | 7-8/9 | LLM non-determinism |
| Q-G5 | 7/9 | LLM non-determinism |
| Q-G6 | 7-8/9 | Individual names in 1/3 runs |
| Q-G8 | 6-8/9 | "No warranty clauses" hallucination in 1/3 runs |

---

## Combined TODO List (Priority Order)

### Route 6 — Next Steps
- [ ] **Self-consistency voting** — Run synthesis 2-3× and take union of items. Directly addresses LLM non-determinism. Would stabilize Q-G7, Q-G8, Q-G3.
- [ ] **Two-pass self-check** (alternative) — After synthesis, second LLM call: "What did you miss?" Cheaper than voting (2 calls vs 3).
- [ ] **Smarter extraction dedup** — Current first-60-chars dedup wastes slots on paraphrases. Semantic dedup could free 10+ slots for unique items.
- [ ] **Q-G4 targeted improvement** — Inventory/furnishings and media invoices are in extraction but synthesis inconsistently includes them.

### Route 8 — Bug Fixes
- [ ] **Fix Bug 1:** Debug document_id mismatch in min_chunks_per_doc (counts all docs as 0 chunks)
- [ ] **Fix Bug 2:** Debug entity-doc-map returning 0 rows (type casing/format mismatch)
- [ ] **Commit Route 8 changes** (min_chunks_per_doc + graph_structural_header)
- [ ] **Re-run Q-G benchmark** after bug fixes
- [ ] **Router integration** — teach auto-router to send global queries to Route 8

### Key Lesson
MAP-REDUCE works for extraction (per-file "what facts exist?") but NOT for synthesis (needs holistic cross-document context). Don't retry without a fundamentally different architecture.
