# Handover: Entity Embedding Contextual Bleed Fix & Two-Step NER Re-evaluation

**Date:** 2026-03-06
**Benchmark:** 55/57 × 3 consecutive (up from mean 54.0, range 53–56)

## Critical Bug Found & Fixed: Entity Embedding Contextual Bleed

### The Bug
`aget_text_embedding_batch()` → `embed_documents()` → `contextualized_embed(inputs=[[name1, name2, ..., name252]])`

Voyage-context-3's contextual embedding treats all inputs in a single inner list as co-occurring chunks of one document. For entity names (independent short strings), this **destroys pairwise cosine similarity** — each entity's vector becomes a mixture of all 252 entities.

**Evidence:**
- `cos("3 business days", "5 business days")` fresh = **0.93**, stored = **0.54**
- `cos("3 business days", "90 days")` fresh = **0.69**, stored = **0.59**
- Shorter entity names were most affected (least intrinsic signal to resist noise)

### The Fix (commit 72fde278)
Added `embed_independent_texts()` and `aembed_independent_texts()` to `VoyageEmbedService`:
- Wraps each entity name as its own single-chunk document: `[[name1], [name2], ...]`
- Eliminates cross-entity contextual interference
- Updated 3 entity embedding call sites in `lazygraphrag_pipeline.py`
- Added `voyage_service` parameter to pipeline constructor

**Files changed:**
- `src/worker/hybrid_v2/embeddings/voyage_embed.py` — new independent embedding methods
- `src/worker/hybrid_v2/indexing/lazygraphrag_pipeline.py` — 3 call sites + constructor
- `src/worker/hybrid_v2/indexing/pipeline_factory.py` — pass voyage_service
- `scripts/index_5pdfs_v2_local.py` — pass voyage_service

### Impact
- Synonym edges: ~48 (broken) → **918** (correct)
- Benchmark: mean 54.0 → **55/57 × 3 consecutive**
- Q-D3 improved from variable 1–2/3 to consistent 2/3

## Architecture Doc Updated (commit 60e3416d)
Added §49 to `ARCHITECTURE_DESIGN_LAZY_HIPPO_HYBRID.md` documenting the bug and fix.

## Other Commits This Session
| Commit | Description |
|--------|-------------|
| e856ebf0 | Code defaults + deploy cleanup (10 defaults fixed, 52→12 env vars) |
| 691827f6 | Pipeline cache invalidation + load_dotenv |
| 5c458474 | Synonym threshold 0.70→0.65 + double-space collapse |
| 60e8d420 | Architecture doc §47 |
| 89486b4a | Rule-based entity typing (reverted) |
| 1c0b6812 | Revert entity typing |
| cda8d644 | Auto-staleness cache invalidation (two-layer defense) |
| 1b1ef4fa | PPR_PASSAGE_TOP_K 20→30 + §48 + .env fix |
| 72fde278 | **Entity embedding contextual bleed fix** |
| 60e3416d | Architecture doc §49 |

## NEXT: Re-test Two-Step NER Extraction

### Why
Two-step NER was tested earlier (checkpoint 003) and scored **52/57**, leading us to conclude single-step was superior. However, that test was run **with the embedding bleed bug active**.

Two-step narrow NER produces shorter, more precise entity names — exactly the kind most corrupted by contextual bleed. The 52/57 may reflect the bug, not the extraction approach. Upstream HippoRAG 2 uses two-step NER→RE extraction.

### Steps
```bash
# 1. Load env
export $(grep -v '^#' .env | xargs)

# 2. Reindex with two-step NER
OPENIE_TWO_STEP=true GROUP_ID=test-5pdfs-v2-fix2 PYTHONPATH=. python3 scripts/index_5pdfs_v2_local.py

# 3. Start API
REQUIRE_AUTH=false ALLOW_LEGACY_GROUP_HEADER=true PYTHONPATH=. nohup python3 -m uvicorn src.api_gateway.main:app --host 0.0.0.0 --port 8000 > /tmp/api.log 2>&1 &

# 4. Benchmark (3 runs)
PYTHONPATH=. python3 scripts/benchmark_route7_hipporag2.py --url http://localhost:8000 --no-auth --group-id test-5pdfs-v2-fix2 --repeats 3 --response-type summary

# 5. LLM judge
PYTHONPATH=. python3 scripts/evaluate_route4_reasoning.py benchmarks/<output_file>.json
```

### Expected Outcome
If two-step NER improves beyond 55/57, it means:
- Denser entity graphs (1.32 rels/entity vs 0.91) create better PPR connectivity
- The Q-D3 timeframe sentences may become reachable via more synonym bridges
- Upstream HippoRAG 2's architecture choice was correct

## Remaining Gaps at 55/57
| Question | Score | Root Cause |
|----------|-------|------------|
| Q-D3 | 2/3 | Retrieval: "10 business days" at DPR rank #62 (outside top-50 seeds) |
| Q-D10 | 2/3 | Synthesis variance: LLM picks wrong clause from correct context |

## Key Operational Notes
- **Always use `--no-auth` for local benchmarks** (otherwise JWT group_id overrides header)
- **Kill API properly:** `lsof -i :8000 -t | xargs kill` (not `kill <parent_PID>`)
- **Check .env** when code default changes don't take effect (load_dotenv overrides)
- Cache auto-invalidation is now active — no need to manually restart after reindex
