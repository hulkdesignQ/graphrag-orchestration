# Architecture: Azure DI+ (DI + Mistral Table Reconciliation)

**Date:** 2026-03-02  
**Status:** Proposed  
**Motivation:** Azure DI misclassifies some table rows as paragraphs, causing our denoising heuristics to incorrectly filter them. Mistral OCR detects these tables correctly. Combine both engines: DI for structure/polygons, Mistral for table detection oracle.

## Problem

Azure DI's `prebuilt-layout` sometimes fails to recognize table structures:

| Document | DI Tables | Mistral Tables | What DI Missed |
|----------|-----------|----------------|----------------|
| Holding Tank | 1 (signature block) | 2 (header fields + signature) | Header form fields are table rows, not paragraphs |
| Builders Warranty | 0 | 0 | — |
| Property Management | 0 | 0 | — |
| Contoso Invoice | 3 | 3 | — |
| Purchase Contract | 0 | 0 | — |

When DI classifies table rows as paragraphs, they flow into the denoising pipeline where heuristic filters (KVP regex, signature detection, short-text noise filter) may incorrectly discard them. Example:

```
DI paragraph P[3]: "Holding Tank Owner(s) Name(s): Contoso Ltd."
  → KVP regex matches "Name(s):" pattern → classified as "metadata" → filtered out
  → But it's actually a table data row with the owner name (important entity)
```

## Proposed Solution: Azure DI+

Run Azure DI (primary) + Mistral OCR (secondary) on each document. When Mistral detects a table that DI missed, reclassify the corresponding DI paragraphs as table content.

### Architecture

```
PDF Document
    │
    ├──────────────────┐
    ▼                  ▼
┌─────────┐     ┌──────────────┐
│ Azure DI│     │ Mistral OCR  │     (parallel HTTP calls)
│ prebuilt│     │ mistral-ocr  │
│ -layout │     │ -latest      │
└────┬────┘     └──────┬───────┘
     │                 │
     │  Full structure:│  Tables detected:
     │  - paragraphs   │  - OCRTableObject[]
     │    + polygons    │    (id, content, format)
     │  - tables       │  - inline markdown tables
     │    + cells      │    (when table_format=null)
     │  - sections     │
     │  - KVPs         │
     │                 │
     ▼                 ▼
┌────────────────────────────────────┐
│     Table Reconciliation Layer     │
│                                    │
│  1. Parse Mistral tables → rows    │
│  2. For each Mistral table row:    │
│     a. Fuzzy-match text against    │
│        DI paragraphs               │
│     b. If match found AND DI has   │
│        no table for this text:     │
│        → Reclassify DI paragraph   │
│          as table_row              │
│        → Create synthetic table    │
│          grouping                  │
│  3. Keep ALL DI metadata intact    │
│     (polygons, offsets, sections)  │
└──────────────┬─────────────────────┘
               │
               ▼
     DI Result + Enhanced Tables
     (existing pipeline continues)
```

### Key Design Decisions

1. **DI is primary, Mistral is oracle only.**  
   We never use Mistral's text or coordinates. We only use it to answer: "Is this text part of a table?"

2. **Text matching, not coordinate matching.**  
   Mistral provides NO per-cell bounding boxes (verified: `OCRTableObject` has only `id`, `content`, `format_`). We match by text similarity using `difflib.SequenceMatcher` with ratio ≥ 0.85.

3. **Match at row level, not cell level.**  
   A Mistral table row like `| Owner Name | Contoso Ltd. |` maps to one or more DI paragraphs. We concatenate DI paragraph texts and match against Mistral row text.

4. **DI polygons become cell polygons.**  
   When we reclassify DI paragraphs as table_row, their existing paragraph polygons serve as the bounding region. No new coordinates needed.

5. **Only run Mistral when beneficial.**  
   Could add a heuristic: only invoke Mistral if DI detected <N tables or if the document has many short paragraphs (indicating potential missed tables). Or always run both (cost is ~$0.001/page).

### Implementation Plan

**Location:** `src/worker/services/document_intelligence_service.py`  
**Insert point:** After DI returns, before `_build_section_aware_documents()`

```python
# New method: ~80 lines
async def _reconcile_tables_with_mistral(
    self,
    di_result: AnalyzeResult,
    document_url: str,
) -> AnalyzeResult:
    """
    Run Mistral OCR on same document and reconcile table detection.
    When Mistral finds tables that DI missed, reclassify corresponding
    DI paragraphs as table content.
    
    Returns: Modified DI result with enhanced table coverage.
    """
    # 1. Call Mistral OCR (table_format="html" for structured parsing)
    mistral_result = await self._call_mistral_ocr(document_url, table_format="html")
    
    # 2. For each page, extract Mistral table rows
    for mistral_page in mistral_result.pages:
        page_idx = mistral_page.index
        mistral_tables = mistral_page.tables or []
        
        if not mistral_tables:
            continue
        
        # 3. Parse HTML table content → list of row texts
        mistral_rows = self._parse_table_rows(mistral_tables)
        
        # 4. Find DI paragraphs on same page that aren't already in a DI table
        di_paras_on_page = [
            (i, p) for i, p in enumerate(di_result.paragraphs)
            if self._paragraph_on_page(p, page_idx)
            and not self._paragraph_in_table(p, di_result.tables)
        ]
        
        # 5. Fuzzy-match Mistral rows against DI paragraphs
        for row_text in mistral_rows:
            best_match, score = self._fuzzy_match_paragraph(
                row_text, di_paras_on_page
            )
            if best_match and score >= 0.85:
                # 6. Reclassify: add table_row role to DI paragraph
                best_match.role = "table_row"  # or add to synthetic table
```

### What This Fixes

| Before (DI only) | After (DI+) |
|-------------------|-------------|
| "Holding Tank Owner(s) Name(s): Contoso Ltd." → paragraph → KVP regex kills it | Same text → table_row → always content |
| "Job Name: Bayfront Animal Clinic" → paragraph → KVP regex kills it | Same text → table_row → always content |
| Short form fields → noise filter kills them | Same text → table_row → preserved |

### Pipeline Impact

The existing `_classify_sentence()` fix (2026-03-02) already handles `role=table_row`:
```python
# In _classify_sentence():
if di_role in ("paragraph", "table_row") and section not in _PSEUDO_SECTIONS:
    return "content"  # Trust DI classification
```

So DI+ automatically benefits from the classify_sentence fix — reclassified paragraphs flow through as content.

### Cost & Latency

| Metric | Value |
|--------|-------|
| Mistral OCR cost | ~$0.002/page ($2/1000 pages) |
| Mistral OCR latency | ~2-4s per document (parallel with DI) |
| Net latency impact | ~0s (runs in parallel with DI's 5-10s) |
| Net cost impact | +$0.002/page on top of DI's $0.01/page (+20%) |

### Mistral OCR Capabilities (Verified 2026-03-02)

From SDK v1.12.4 `OCRTableObject` class:
- **Table content:** ✅ HTML or markdown (structured rows/columns)
- **Table bbox:** ❌ Not available in basic OCR
- **Per-cell bbox:** ❌ Not available in basic OCR
- **Image bbox:** ✅ `top_left_x/y`, `bottom_right_x/y` (pixel coordinates)
- **Page dimensions:** ✅ `dpi`, `height`, `width`
- **BBox Annotation:** ✅ LLM-powered feature (extra cost) — can extract any field with bounding boxes using a custom schema. NOT part of basic OCR.

### Alternative: BBox Annotation for Table Coordinates

If we need per-cell bounding boxes from Mistral (e.g., for UI highlighting of reconciled tables), we could use the `bbox_annotation_format` parameter:

```python
ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={"type": "document_url", "document_url": url},
    bbox_annotation_format=ResponseFormat(
        type="json_schema",
        json_schema={
            "name": "table_cells",
            "schema": {
                "type": "object",
                "properties": {
                    "tables": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "cells": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "row": {"type": "integer"},
                                            "col": {"type": "integer"},
                                            "text": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    )
)
```

This would use the vision model to locate table cells with coordinates. Extra cost (~2x) but gives coordinates. **Not needed for the reconciliation approach** since we use DI's existing paragraph polygons.

### Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Text mismatch between OCR engines | Medium | Fuzzy match at ratio ≥ 0.85; normalize whitespace before matching |
| Mistral falsely detects table | Low | Only reclassify if DI paragraph exists at same location; conservative matching |
| Granularity mismatch (1 DI para = N Mistral cells) | Medium | Match at row level; allow 1:many mapping |
| Mistral API unavailable | Low | Graceful fallback: DI-only mode (current behavior) |
| Cost increase | Low | $0.002/page; can gate behind feature flag or only invoke for problem documents |

### Feature Flag

```python
# Environment variable to enable/disable
ENABLE_MISTRAL_TABLE_RECONCILIATION = os.getenv("ENABLE_MISTRAL_TABLE_RECONCILIATION", "0") == "1"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
```

### Dependencies

- `mistralai` Python SDK (already installed for testing: v1.12.4)
- `MISTRAL_API_KEY` environment variable
- No changes to Neo4j schema, PPR, or query-time pipeline

### Relation to Other Fixes

This fix is **orthogonal** to the `_classify_sentence()` fix:
- `_classify_sentence()` → fixes heuristic misclassification of DI-labeled paragraphs
- DI+ → fixes DI's structural misclassification (table vs paragraph)
- Together: both DI's label AND our heuristic are correct → maximum content preservation

### Open Questions

1. **Should we always run both engines, or only when DI table count is low?**  
   Always-run is simpler and adds negligible latency (parallel). Gate on `ENABLE_MISTRAL_TABLE_RECONCILIATION`.

2. **Should we create synthetic DI Table objects, or just add `role=table_row` to paragraphs?**  
   Role-only is simpler and sufficient for the pipeline. Synthetic tables would be needed for table-specific UI features.

3. **What about `table_format=null` (inline tables in markdown)?**  
   When `table_format=null`, Mistral embeds tables inline in the markdown. We'd need to parse pipe-delimited tables from the markdown text. Using `table_format="html"` is cleaner — tables are in a separate `tables[]` array with structured HTML.

4. **Should we use BBox Annotation instead of basic OCR for targeted extraction?**  
   Only if we need per-cell coordinates. For the reconciliation approach (text-matching), basic OCR is sufficient and cheaper.
