#!/usr/bin/env python3
"""Experiment: Compare OpenIE triple extraction across 4 configurations.

Evaluates quality of generated triples/entities without full pipeline.

Configurations:
  E0 (baseline):  sequential batching + LLM for all
  E1:             section batching + LLM for all
  E2 (new default): section batching + deterministic for structured
  E3:             sequential batching + deterministic for structured

Usage:
    PYTHONPATH=. python3 scripts/experiment_section_context_openie.py \
        [--group-id test-5pdfs-v2-fix2] [--sample N]
"""
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Ensure project root on path
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


EXPERIMENTS = {
    "E0_sequential_llm": ("sequential", "llm"),
    "E1_section_llm": ("section", "llm"),
    "E2_section_deterministic": ("section", "deterministic"),
    "E3_sequential_deterministic": ("sequential", "deterministic"),
}


def classify_sentence(pipeline, s):
    """Classify sentence using the pipeline's internal classifier."""
    return pipeline._classify_sentence(s)


async def run_experiment(
    pipeline: LazyGraphRAGIndexingPipeline,
    group_id: str,
    content_sentences: list,
    name: str,
    batching: str,
    structured: str,
) -> dict:
    """Run one extraction experiment."""
    # Override flags on the instance
    pipeline._openie_batching = batching
    pipeline._structured_extraction = structured

    t0 = time.time()
    entities, relationships = await pipeline._extract_openie_triples(
        group_id=group_id,
        content_sentences=content_sentences,
    )
    elapsed = time.time() - t0

    # Collect raw info
    entity_names = sorted(set(e.name for e in entities))
    rel_summaries = [
        {"src": r.source_id[:12], "desc": r.description, "tgt": r.target_id[:12]}
        for r in relationships
    ]

    return {
        "experiment": name,
        "batching": batching,
        "structured_extraction": structured,
        "elapsed_sec": round(elapsed, 2),
        "entity_count": len(entities),
        "relationship_count": len(relationships),
        "entity_names": entity_names,
        "relationships": rel_summaries,
        "unique_predicates": sorted(set(r.description for r in relationships)),
    }


async def main():
    parser = argparse.ArgumentParser(description="Section-context OpenIE experiment")
    parser.add_argument("--group-id", default="test-5pdfs-v2-fix2")
    parser.add_argument("--sample", type=int, default=0,
                        help="Limit to first N content sentences (0=all)")
    parser.add_argument("--experiments", nargs="+", default=list(EXPERIMENTS.keys()),
                        help="Which experiments to run")
    args = parser.parse_args()

    # ── Setup ─────────────────────────────────────────────────────────
    print(f"Connecting to Neo4j...")
    neo4j_store = Neo4jStoreV3(
        uri=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
    )

    print(f"Fetching sentences for group_id={args.group_id}...")
    raw_sentences = neo4j_store.get_sentences_by_group(args.group_id)
    print(f"  Total sentences: {len(raw_sentences)}")

    llm_service = LLMService()
    config = LazyGraphRAGIndexingConfig(
        chunk_size=1500, chunk_overlap=50, embedding_dimensions=2048,
    )
    pipeline = LazyGraphRAGIndexingPipeline(
        neo4j_store=neo4j_store,
        llm=llm_service.get_indexing_llm(),
        embedder=None,  # Not needed for extraction
        config=config,
    )

    # Filter to content sentences
    content_sentences = [
        s for s in raw_sentences if classify_sentence(pipeline, s) == "content"
    ]
    print(f"  Content sentences: {len(content_sentences)}")

    # Show source distribution
    source_counts: dict = {}
    for s in content_sentences:
        src = s.get("source", "unknown")
        source_counts[src] = source_counts.get(src, 0) + 1
    print(f"  Source distribution: {json.dumps(source_counts, indent=2)}")

    # Show section distribution
    section_counts: dict = {}
    for s in content_sentences:
        sp = s.get("section_path", "(none)")
        section_counts[sp] = section_counts.get(sp, 0) + 1
    print(f"  Sections: {len(section_counts)}")
    for sp, cnt in sorted(section_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    {sp}: {cnt} sentences")

    if args.sample > 0:
        content_sentences = content_sentences[: args.sample]
        print(f"  Sampled to {len(content_sentences)} sentences")

    # ── Run experiments ──────────────────────────────────────────────
    results = []
    for exp_name in args.experiments:
        if exp_name not in EXPERIMENTS:
            print(f"  Unknown experiment: {exp_name}, skipping")
            continue
        batching, structured = EXPERIMENTS[exp_name]
        print(f"\n{'='*60}")
        print(f"Running {exp_name} (batching={batching}, structured={structured})")
        print(f"{'='*60}")
        result = await run_experiment(
            pipeline, args.group_id, content_sentences,
            exp_name, batching, structured,
        )
        results.append(result)

        # Print summary
        print(f"  Time: {result['elapsed_sec']}s")
        print(f"  Entities: {result['entity_count']}")
        print(f"  Relationships: {result['relationship_count']}")
        print(f"  Unique predicates: {len(result['unique_predicates'])}")
        print(f"  Entity names ({len(result['entity_names'])}): {result['entity_names'][:15]}...")

    # ── Comparison ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    print(f"{'Experiment':<30} {'Entities':>8} {'Rels':>8} {'Predicates':>10} {'Time':>8}")
    print("-" * 70)
    for r in results:
        print(
            f"{r['experiment']:<30} {r['entity_count']:>8} "
            f"{r['relationship_count']:>8} {len(r['unique_predicates']):>10} "
            f"{r['elapsed_sec']:>7.1f}s"
        )

    # ── Entity overlap analysis ──────────────────────────────────────
    if len(results) >= 2:
        print(f"\nEntity overlap (vs E0 baseline):")
        baseline_set = set(results[0]["entity_names"]) if results else set()
        for r in results[1:]:
            other_set = set(r["entity_names"])
            common = baseline_set & other_set
            only_baseline = baseline_set - other_set
            only_other = other_set - baseline_set
            print(f"  {r['experiment']}:")
            print(f"    Common: {len(common)}, Only in E0: {len(only_baseline)}, Only in {r['experiment']}: {len(only_other)}")
            if only_other:
                print(f"    New entities: {sorted(only_other)[:10]}")
            if only_baseline:
                print(f"    Lost entities: {sorted(only_baseline)[:10]}")

    # ── Save results ─────────────────────────────────────────────────
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    out_path = Path(__file__).resolve().parent.parent / f"experiment_section_context_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")

    neo4j_store.close()


if __name__ == "__main__":
    asyncio.run(main())
