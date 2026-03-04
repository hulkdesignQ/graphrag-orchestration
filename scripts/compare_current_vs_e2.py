#!/usr/bin/env python3
"""Compare current production entities/triples with E2 extraction output.

Pulls existing entities + RELATED_TO triples from Neo4j, then runs E2
extraction on the same sentences and produces a detailed quality comparison.

Usage:
    PYTHONPATH=. python3 scripts/compare_current_vs_e2.py [--group-id test-5pdfs-v2-fix2]
"""
import asyncio
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from src.core.config import settings
from src.worker.hybrid_v2.services.neo4j_store import Neo4jStoreV3
from src.worker.services.llm_service import LLMService
from src.worker.hybrid_v2.indexing.lazygraphrag_pipeline import (
    LazyGraphRAGIndexingPipeline,
    LazyGraphRAGIndexingConfig,
)


def pull_current_production(neo4j_store: Neo4jStoreV3, group_id: str) -> dict:
    """Pull all entities and RELATED_TO triples from Neo4j."""
    # All entities
    with neo4j_store.get_retry_session() as session:
        result = session.run(
            "MATCH (e:Entity {group_id: $gid}) "
            "RETURN e.id AS id, e.name AS name, e.type AS type, "
            "       e.description AS description, e.importance_score AS importance",
            gid=group_id,
        )
        entities = [dict(r) for r in result]

    # All RELATED_TO triples
    triples = neo4j_store.fetch_all_triples(group_id)

    # MENTIONS edges (sentence → entity)
    with neo4j_store.get_retry_session() as session:
        result = session.run(
            "MATCH (s:Sentence {group_id: $gid})-[m:MENTIONS]->(e:Entity {group_id: $gid}) "
            "RETURN s.id AS sentence_id, e.name AS entity_name, m.weight AS weight",
            gid=group_id,
        )
        mentions = [dict(r) for r in result]

    return {"entities": entities, "triples": triples, "mentions": mentions}


async def run_e2_extraction(
    pipeline: LazyGraphRAGIndexingPipeline,
    group_id: str,
    content_sentences: list,
) -> dict:
    """Run E2 (section + deterministic) extraction."""
    pipeline._openie_batching = "section"
    pipeline._structured_extraction = "deterministic"

    entities, relationships = await pipeline._extract_openie_triples(
        group_id=group_id,
        content_sentences=content_sentences,
    )

    return {
        "entities": [{"name": e.name, "type": e.type, "mentions": len(e.text_unit_ids)} for e in entities],
        "triples": [
            {"source": e.name, "predicate": r.description, "target": next(
                (ent.name for ent in entities if ent.id == r.target_id), r.target_id
            )}
            for r in relationships
            for e in entities if e.id == r.source_id
        ],
        "raw_entities": entities,
        "raw_relationships": relationships,
    }


def print_section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def compare_entity_sets(current_names: set, e2_names: set):
    """Detailed entity comparison."""
    common = current_names & e2_names
    only_current = current_names - e2_names
    only_e2 = e2_names - current_names

    print(f"\n  Common entities: {len(common)}")
    print(f"  Only in CURRENT (lost in E2): {len(only_current)}")
    print(f"  Only in E2 (new): {len(only_e2)}")

    if only_current:
        print(f"\n  ── Entities LOST in E2 ({len(only_current)}) ──")
        for name in sorted(only_current):
            print(f"    - {name}")

    if only_e2:
        print(f"\n  ── Entities NEW in E2 ({len(only_e2)}) ──")
        for name in sorted(only_e2):
            print(f"    + {name}")


def compare_triple_sets(current_triples: list, e2_triples: list):
    """Detailed triple comparison."""

    def triple_key(t):
        return (t.get("source_name", t.get("source", "")).lower().strip(),
                t.get("description", t.get("predicate", "")).lower().strip(),
                t.get("target_name", t.get("target", "")).lower().strip())

    current_set = set(triple_key(t) for t in current_triples)
    e2_set = set(triple_key(t) for t in e2_triples)

    common = current_set & e2_set
    only_current = current_set - e2_set
    only_e2 = e2_set - current_set

    print(f"\n  Common triples: {len(common)}")
    print(f"  Only in CURRENT: {len(only_current)}")
    print(f"  Only in E2: {len(only_e2)}")

    # Show predicate distribution
    current_preds = Counter(t[1] for t in current_set)
    e2_preds = Counter(t[1] for t in e2_set)

    print(f"\n  ── Predicate distribution ──")
    print(f"  {'Predicate':<40} {'Current':>8} {'E2':>8} {'Delta':>8}")
    print(f"  {'-'*64}")
    all_preds = sorted(set(current_preds.keys()) | set(e2_preds.keys()))
    for p in all_preds:
        c = current_preds.get(p, 0)
        e = e2_preds.get(p, 0)
        delta = e - c
        marker = "  " if delta == 0 else (" +" if delta > 0 else " ")
        print(f"  {p[:40]:<40} {c:>8} {e:>8} {marker}{delta:>6}")

    if only_current:
        print(f"\n  ── Sample triples LOST in E2 (first 20) ──")
        for s, p, o in sorted(only_current)[:20]:
            print(f"    - ({s}, {p}, {o})")

    if only_e2:
        print(f"\n  ── Sample triples NEW in E2 (first 20) ──")
        for s, p, o in sorted(only_e2)[:20]:
            print(f"    + ({s}, {p}, {o})")


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--group-id", default="test-5pdfs-v2-fix2")
    args = parser.parse_args()

    neo4j_store = Neo4jStoreV3(
        uri=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
    )

    # ── Step 1: Pull current production data ─────────────────────────
    print_section("STEP 1: Current Production Data (from Neo4j)")
    current = pull_current_production(neo4j_store, args.group_id)
    print(f"  Entities: {len(current['entities'])}")
    print(f"  Triples (RELATED_TO): {len(current['triples'])}")
    print(f"  MENTIONS edges: {len(current['mentions'])}")

    # Entity type distribution
    type_counts = Counter(e.get("type", "?") for e in current["entities"])
    print(f"  Entity types: {dict(type_counts)}")

    # Sample current entities
    print(f"\n  ── Current entity names (sorted, first 30) ──")
    current_names = sorted(set((e.get("name") or "").lower().strip() for e in current["entities"]))
    for name in current_names[:30]:
        print(f"    {name}")
    print(f"    ... ({len(current_names)} total)")

    # Sample current triples
    print(f"\n  ── Current triples (first 15) ──")
    for t in current["triples"][:15]:
        print(f"    ({t['source_name']}, {t['description']}, {t['target_name']})")

    # ── Step 2: Run E2 extraction ────────────────────────────────────
    print_section("STEP 2: E2 Extraction (section + deterministic)")

    raw_sentences = neo4j_store.get_sentences_by_group(args.group_id)
    llm_service = LLMService()
    config = LazyGraphRAGIndexingConfig(chunk_size=1500, chunk_overlap=50, embedding_dimensions=2048)
    pipeline = LazyGraphRAGIndexingPipeline(
        neo4j_store=neo4j_store,
        llm=llm_service.get_indexing_llm(),
        embedder=None,
        config=config,
    )

    content_sentences = [s for s in raw_sentences if pipeline._classify_sentence(s) == "content"]
    print(f"  Content sentences: {len(content_sentences)}")

    # Show structured sentences that will go to deterministic path
    structured = [s for s in content_sentences if s.get("source") in ("signature_party", "letterhead")]
    print(f"  Structured sentences (deterministic): {len(structured)}")
    for s in structured:
        print(f"    [{s['source']}] {s['text'][:80]}...")

    t0 = time.time()
    e2 = await run_e2_extraction(pipeline, args.group_id, content_sentences)
    elapsed = time.time() - t0
    print(f"\n  E2 extraction time: {elapsed:.1f}s")
    print(f"  E2 entities: {len(e2['entities'])}")
    print(f"  E2 triples: {len(e2['triples'])}")

    # Sample E2 entities
    print(f"\n  ── E2 entity names (sorted, first 30) ──")
    e2_names = sorted(set(e["name"] for e in e2["entities"]))
    for name in e2_names[:30]:
        print(f"    {name}")
    print(f"    ... ({len(e2_names)} total)")

    # Sample E2 triples
    print(f"\n  ── E2 triples (first 15) ──")
    for t in e2["triples"][:15]:
        print(f"    ({t['source']}, {t['predicate']}, {t['target']})")

    # ── Step 3: Compare ──────────────────────────────────────────────
    print_section("STEP 3: ENTITY COMPARISON")
    current_name_set = set((e.get("name") or "").lower().strip() for e in current["entities"])
    e2_name_set = set(e["name"] for e in e2["entities"])
    compare_entity_sets(current_name_set, e2_name_set)

    print_section("STEP 4: TRIPLE COMPARISON")
    compare_triple_sets(current["triples"], e2["triples"])

    # ── Summary ──────────────────────────────────────────────────────
    print_section("SUMMARY")
    print(f"  {'Metric':<30} {'Current':>10} {'E2':>10} {'Delta':>10}")
    print(f"  {'-'*60}")
    print(f"  {'Entities':<30} {len(current['entities']):>10} {len(e2['entities']):>10} {len(e2['entities'])-len(current['entities']):>+10}")
    print(f"  {'Triples':<30} {len(current['triples']):>10} {len(e2['triples']):>10} {len(e2['triples'])-len(current['triples']):>+10}")
    common_ents = len(current_name_set & e2_name_set)
    print(f"  {'Common entities':<30} {common_ents:>10}")
    print(f"  {'Entity overlap %':<30} {100*common_ents/max(len(current_name_set),1):>9.1f}%  {100*common_ents/max(len(e2_name_set),1):>9.1f}%")

    # Save full output
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out = {
        "timestamp": ts,
        "group_id": args.group_id,
        "current": {
            "entity_count": len(current["entities"]),
            "triple_count": len(current["triples"]),
            "mention_count": len(current["mentions"]),
            "entity_names": current_names,
        },
        "e2": {
            "entity_count": len(e2["entities"]),
            "triple_count": len(e2["triples"]),
            "entity_names": e2_names,
        },
        "comparison": {
            "common_entities": len(current_name_set & e2_name_set),
            "only_current": sorted(current_name_set - e2_name_set),
            "only_e2": sorted(e2_name_set - current_name_set),
        },
    }
    out_path = Path(__file__).resolve().parent.parent / f"comparison_current_vs_e2_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n  Full comparison saved to {out_path}")

    neo4j_store.close()


if __name__ == "__main__":
    asyncio.run(main())
