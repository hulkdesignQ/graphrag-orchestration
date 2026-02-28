# Handover: Sentence Source Tagging — Signature, Header/Footer, Letterhead — 2026-02-28

**Date:** 2026-02-28  
**Status:** All source types working. Reindexed 197 sentences across 5 PDFs. Committed & pushed.  
**Previous handover:** `HANDOVER_2026-02-27_DENOISE_FILTER_AND_DEPLOYMENT.md`  
**Current deployed commit:** `b8fb85d fix: letterhead detection now works in section-aware DI path`

---

## 1. What Was Done Today

### 1.1 Signature Block — Raw Lines Format (`c0a37ad`, `b6e969a`)
- Replaced the brittle LLM-style synthesized signature sentence with joined raw lines
- Raw lines from `_detect_signature_block_paragraphs()` are joined with ` | ` separator
- Creates one sentence per signature block with `source="signature_party"`
- Example: `"SELLER: | By: Fabrikam Inc. | Authorized representative | Date: 04/30/2025"`

### 1.2 Header/Footer First-Occurrence Extraction (`36d9e1a`)
- Page headers (`role="pageHeader"`) and page footers (`role="pageFooter"`) extracted as sentences
- Only the **first occurrence** is kept (headers/footers repeat on every page)
- `source="page_header"` / `source="page_footer"`, `section_path="[Page Header]"` / `"[Page Footer]"`
- Embedding prefix `[Page header]` / `[Page footer]` added to `_build_label_prefix()`
- Added to `_STRUCTURED_SOURCES` in route_5_unified.py for denoiser bypass

### 1.3 Letterhead Detection (`db54a44`)
- Heuristic: page 1 paragraphs before first title/sectionHeading, no role, max 5 paragraphs
- KVP stop regex detects label boundaries (e.g., "TO:", "Invoice #: 12345")
- Consolidated into single sentence with `source="letterhead"`, `section_path="[Letterhead]"`
- Embedding prefix `[Letterhead]` added

### 1.4 Figure Node Removal (`0037851`)
- Removed dead `:Figure` node pipeline from V2 indexing (−213 lines)
- No query route ever read Figure nodes; captions were already indexed as Sentences
- Legacy Figure nodes remain in graph but are inert

### 1.5 Table Caption Extraction (`8c1e12d`)
- Mirrored figure-caption pattern for `table.caption` from DI response
- Creates Sentence with `source="table_caption"` (+63 lines across 4 files)

### 1.6 Section-Aware DI Path Fix (`f12062a`, `b8fb85d`)
The most complex change — `_build_section_aware_documents()` was stripping paragraph roles:

**Problem:** When DI documents have sections (headings), all paragraphs are grouped into section-based DI units. Role metadata (`pageHeader`, `pageFooter`, etc.) is lost. Letterhead gets absorbed into section_0 body text.

**Three bugs found and fixed:**

| Bug | Symptom | Root Cause | Fix |
|-----|---------|------------|-----|
| Role propagation scope | 194→6 sentences (catastrophic) | ALL roles propagated to chunk metadata, including `title`/`sectionHeading` which hit `SKIP_ROLES` | Only propagate `_PROPAGATE_ROLES = {"letterhead","pageHeader","pageFooter"}` |
| De-dup key collision | 0 letterhead extracted | Letterhead + pageFooter both have `di_section_path=[]`, collide on `(url, path)` key | Added `role` to de-dup key: `(url, path, role)` |
| KVP stop regex | 0 letterhead detected | `"TO:"` (no content after colon) didn't match `Key: Value` pattern, letterhead collected 9 paragraphs past 5-max limit | Added standalone label branch: `^[A-Za-z]...:$` |

### 1.7 Token Tracking & Credit System (`2f8a42b`, `68fb054`, `a68bad6`)
- TrackedLLM wrapper intercepts all `acomplete()`/`complete()` calls for token counting
- TokenAccumulator per-request counter with USD-based credit normalization
- UsageTracker fire-and-forget Cosmos DB writes for all service types
- Dashboard API endpoints for credit visibility
- GDS session timing and cost estimation

---

## 2. Current State

### Reindex Results (test-5pdfs-v2-fix2, 5 PDFs)

| Source | Count | Change |
|--------|-------|--------|
| paragraph | 180 | −14 from 194 (denoise filter) |
| table_row | 12 | Unchanged |
| page_footer | 2 | **New** — builders warranty + contoso invoice |
| signature_party | 2 | Format changed (raw lines) |
| letterhead | 1 | **New** — contoso invoice |
| **Total** | **197** | +4 from 193 (27 handover) |

### Git Log (today's commits)
```
b8fb85d fix: letterhead detection now works in section-aware DI path
03c8505 docs: add §36 (indexing cleanup, token tracking, credit system, dashboard)
a68bad6 feat: GDS session tracking + credit-aware dashboard + API credit fields
f12062a fix: propagate paragraph roles through section-aware DI path
68fb054 feat: complete tracking gaps + USD-based credit system
2f8a42b feat: wire up LLM token tracking across all acomplete() call sites
8c1e12d Extract table captions as Sentence nodes (source=table_caption)
db54a44 feat: detect letterhead paragraphs and extract as dedicated sentence
0037851 Remove dead :Figure node pipeline from V2 indexing
36d9e1a feat: attach signature metadata, extract first-occurrence headers/footers
b6e969a fix: join signature raw lines into single sentence
c0a37ad fix: replace brittle signature sentence synthesis with raw lines
deedc99 feat: synthesize semantic sentences from signature blocks
```

### Key Files Modified

| File | Changes |
|------|---------|
| `src/worker/services/sentence_extraction_service.py` | Letterhead handler, page_header/footer handlers, signature raw lines, KVP regex |
| `src/worker/services/document_intelligence_service.py` | Letterhead detection, role propagation, orphaned paragraph emission, de-dup fix |
| `src/worker/hybrid_v2/indexing/lazygraphrag_pipeline.py` | Figure removal, table caption, embedding prefixes, token tracking |
| `src/worker/hybrid_v2/routes/route_5_unified.py` | `_STRUCTURED_SOURCES` additions |
| `src/core/services/token_accumulator.py` | New — per-request token counter |
| `src/core/services/tracked_llm.py` | New — transparent LLM wrapper |
| `src/core/services/credit_schedule.py` | New — USD exchange rates |
| `src/core/services/usage_tracker.py` | New — Cosmos DB usage writes |

---

## 3. Architecture Design Reference

See `ARCHITECTURE_DESIGN_LAZY_HIPPO_HYBRID.md`:
- **§36.7** — Full three-layer sentence source tagging architecture
- **§36.1–36.6** — Figure removal, table captions, token tracking, credit system

---

## 4. TODO List

### Immediate — Benchmark on New Index

- [ ] **Run Route 7 benchmark on 197-sentence index** — Verify no regression from source tagging changes. Compare against 193-sentence baseline and original 207 pre-denoise baseline.
  ```bash
  python3 scripts/benchmark_route7_hipporag2.py \
    --url https://graphrag-api.salmonhill-df6033f3.swedencentral.azurecontainerapps.io \
    --group-id test-5pdfs-v2-fix2 --repeats 1
  ```
- [ ] **LLM eval if benchmark looks good** — Target: match or exceed 56/57 (98.2%) from pre-denoise baseline.

### Carried Over from 2026-02-27 — Route 7 Improvement Plan

#### High Priority — Upstream Alignment
- [ ] **Commit & deploy rerank_top_k=30** — Already in code (`e720c65`), validated locally at 56/57.
- [ ] **OpenIE triple extraction at indexing time** — Dedicated `subject predicate object` extraction. Stub: `_extract_triples()`.
- [ ] **Seed ALL passages in PPR (Gap 1)** — Currently only top-20 DPR hits seeded. `route_7_hipporag2.py` lines 446–454.
- [ ] **Use raw fact scores for entity seeds (Gap 2)** — `route_7_hipporag2.py` lines 414–416.

#### Medium Priority — Retrieval Quality
- [ ] **Sentence window expansion (±1 neighbors)** — Fetch adjacent sentences. `route_7_hipporag2.py` `_fetch_chunks_by_ids()`.
- [ ] **Increase PPR passage top-K (Gap 3)** — Raise from 20 to 50–100.

#### Low Priority — Ablation
- [ ] **Damping factor ablation (Gap 5)** — Sweep {0.5, 0.7, 0.85}.
- [ ] **Verify RELATED_TO edge weights (Gap 4)** — Check co-occurrence semantics.

### Carried Over — Sentence Extraction Thresholds
- [ ] **Lower `SKELETON_MIN_SENTENCE_CHARS` 30→20** — Rescue short legal sentences. `src/core/config.py:116`.
- [ ] **Tighten ALL_CAPS word threshold 10→6** — Preserve binding legal statements.
- [ ] **`_is_kvp_label` word threshold 8→10** — Prevent false positives on long KVP sentences.
- [ ] **`numeric_only` alpha threshold 10→6** — Recover "Invoice #1256003", "Total: $29,900".
- [ ] **Whitespace-normalize dedup key** — `re.sub(r'\s+', ' ', text).strip().lower()`.

### CU vs DI Migration (from 2026-02-26 analysis)
- [ ] **Test CU page-level extraction** — CU is deployed; test if paragraph/sentence quality matches DI.
- [ ] **Compare CU signature block** — Check if single polygon vs multiple; may simplify detection.
- [ ] **Evaluate CU sentence splitting** — CU may not provide sentence boundaries; may need wtpsplit.
- [ ] **KVP field usage** — Currently wired but unused in pipeline. Decide: use or remove.

### Infrastructure
- [ ] **Investigate GDS Aura connectivity** — 0 communities and 0 KNN edges on cloud reindexes.
- [ ] **Cloud query 500 error investigation** — Intermittent.

---

## 5. How to Resume

```bash
# 1. Run benchmark on current 197-sentence index
python3 scripts/benchmark_route7_hipporag2.py \
  --url https://graphrag-api.salmonhill-df6033f3.swedencentral.azurecontainerapps.io \
  --group-id test-5pdfs-v2-fix2 --repeats 1

# 2. Local reindex (if needed)
GROUP_ID=test-5pdfs-v2-fix2 PYTHONPATH=. python3 scripts/index_5pdfs_v2_local.py

# 3. Deploy (push to main triggers CI/CD)
git push origin main

# 4. Unit tests
PYTHONPATH=. python3 -m pytest tests/ -x --timeout=30 -q
```
