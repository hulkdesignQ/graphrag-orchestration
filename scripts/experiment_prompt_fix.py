#!/usr/bin/env python3
"""Experiment: Test improved OpenIE prompt for section batching.

Compares current prompt vs improved prompt on SECTION batches,
specifically checking whether critical missing entities appear.

Known missing entities from E2 regression analysis:
- "implied warranties" / "other warranties" (warranty doc sent_31)
- "non-transferable" / "first purchaser" (warranty doc sent_44)
- "indemnify" / "gross negligence" (prop mgmt sent_43)
- "10 business days" (holding tank sent_17)

Usage:
    PYTHONPATH=. python3 scripts/experiment_prompt_fix.py
"""
import asyncio
import json
import os
import sys
import time
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
from llama_index.core.llms import ChatMessage

# ── Current prompt (from pipeline) ──────────────────────────────────
CURRENT_PROMPT = """Extract knowledge graph triples from each sentence below.
For each sentence, identify (subject, predicate, object) triples where:
- subject and object are named entities, key concepts, dates, or amounts
- predicate is the exact relationship phrase from the text
- Extract ALL factual relationships, not just the most obvious one
- Use the entity names exactly as they appear in the text

{sentences}

Return ONLY valid JSON (no markdown fences):
{{"triples": [
  {{"sid": "<sentence_id>", "s": "<subject>", "p": "<predicate>", "o": "<object>"}},
  ...
]}}"""

# ── Improved prompt ─────────────────────────────────────────────────
IMPROVED_PROMPT = """Extract knowledge graph triples from the sentences below.

Rules:
1. Process EACH sentence [ID] independently — extract 2-5 triples per sentence.
2. Predicates MUST be short verb phrases (1-5 words). Examples: "warrants for", "is not transferable", "holds risk until", "disclaims", "shall indemnify".
3. Do NOT use the full sentence as a predicate.
4. Subjects and objects are named entities, key concepts, legal terms, dates, or amounts.
5. Include abstract concepts as entities when present: warranties, liabilities, rights, obligations, limitations, conditions.
6. Extract ALL factual relationships from each sentence, not just the most obvious one.

{sentences}

Return ONLY valid JSON (no markdown fences):
{{"triples": [
  {{"sid": "<sentence_id>", "s": "<subject>", "p": "<predicate>", "o": "<object>"}},
  ...
]}}"""

# Sentences we know are critical (from regression analysis)
CRITICAL_SENTENCE_IDS = {
    "doc_b0b39088b0174518a76c490b11191112_sent_44",  # non-transferable
    "doc_b0b39088b0174518a76c490b11191112_sent_31",  # disclaimer
    "doc_ad9e3442392543748bd815bacbab8be3_sent_43",   # indemnify
    "doc_ad9e3442392543748bd815bacbab8be3_sent_22",   # 5 business days
    "doc_3b9cf0f384354c2faee0daf3997dd7d9_sent_17",   # 10 business days
    "doc_01c4b90de1ab4f4295f4cf156117c9d7_sent_20",   # 90 days
    "doc_01c4b90de1ab4f4295f4cf156117c9d7_sent_23",   # 3 business days
}

# Entities we expect to see (from baseline that E2 lost)
EXPECTED_ENTITIES = {
    "implied warranties", "other warranties", "any warranty",
    "non-transferable", "first purchaser", "transferable",
    "gross negligence", "willful misconduct", "indemnify",
    "bodily injury", "loss or damage", "damage",
    "10 business days", "5 business days",
    "liability", "limitation",
}


def build_section_batches(pipeline, sentences):
    """Use the pipeline's section batching to create batches."""
    pipeline._openie_batching = "section"
    return pipeline._build_section_batches(sentences)


async def run_prompt_test(llm, batches, prompt_template, label):
    """Run extraction with a specific prompt template on section batches."""
    all_triples = []
    sem = asyncio.Semaphore(4)

    async def extract_batch(batch, context):
        sentence_block = context + "\n".join(
            f"[{s['id']}]: {s['text']}" for s in batch
        )
        prompt = prompt_template.format(sentences=sentence_block)
        async with sem:
            try:
                response = await llm.achat(
                    [ChatMessage(role="user", content=prompt)]
                )
                text = response.message.content.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3].rstrip()
                if text.startswith("json"):
                    text = text[4:].lstrip()
                parsed = json.loads(text)
                return parsed.get("triples", [])
            except Exception as e:
                print(f"  Batch failed: {e}")
                return []

    tasks = [extract_batch(batch, ctx) for batch, ctx in batches]
    results = await asyncio.gather(*tasks)
    for batch_triples in results:
        all_triples.extend(batch_triples)

    # Collect entities and stats
    entities = set()
    predicates = []
    critical_triples = []
    for t in all_triples:
        s, p, o = t.get("s", ""), t.get("p", ""), t.get("o", "")
        sid = t.get("sid", "")
        entities.add(s.lower().strip())
        entities.add(o.lower().strip())
        predicates.append(p)
        if sid in CRITICAL_SENTENCE_IDS:
            critical_triples.append(t)

    entities.discard("")

    return {
        "label": label,
        "total_triples": len(all_triples),
        "unique_entities": len(entities),
        "entities": sorted(entities),
        "predicates": predicates,
        "critical_triples": critical_triples,
        "all_triples": all_triples,
    }


def analyse(result, label):
    """Print analysis of extraction result."""
    preds = result["predicates"]
    long50 = [p for p in preds if len(p) > 50]
    long20 = [p for p in preds if len(p) > 20]

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Total triples: {result['total_triples']}")
    print(f"  Unique entities: {result['unique_entities']}")
    print(f"  Predicates > 50 chars: {len(long50)} ({100*len(long50)//max(len(preds),1)}%)")
    print(f"  Predicates > 20 chars: {len(long20)} ({100*len(long20)//max(len(preds),1)}%)")

    if long50:
        print(f"\n  Worst predicates:")
        for p in sorted(long50, key=len, reverse=True)[:3]:
            print(f"    len={len(p)}: {p[:100]}...")

    # Check for expected entities
    ent_set = set(result["entities"])
    found = EXPECTED_ENTITIES & ent_set
    # Also do fuzzy matching (substring)
    fuzzy_found = set()
    for expected in EXPECTED_ENTITIES:
        for actual in ent_set:
            if expected in actual or actual in expected:
                fuzzy_found.add(expected)

    missing = EXPECTED_ENTITIES - found - fuzzy_found
    print(f"\n  Expected entities found (exact): {sorted(found)}")
    print(f"  Expected entities found (fuzzy): {sorted(fuzzy_found - found)}")
    print(f"  Expected entities MISSING: {sorted(missing)}")

    # Show critical sentence triples
    print(f"\n  Critical sentence triples ({len(result['critical_triples'])}):")
    for t in result["critical_triples"]:
        print(f"    [{t['sid'][-10:]}] ({t['s']}) --[{t['p'][:50]}]--> ({t['o']})")


async def main():
    print("Connecting to Neo4j...")
    neo4j_store = Neo4jStoreV3(
        uri=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
    )

    print("Fetching sentences...")
    raw_sentences = neo4j_store.get_sentences_by_group("test-5pdfs-v2-fix2")

    llm_service = LLMService()
    config = LazyGraphRAGIndexingConfig(
        chunk_size=1500, chunk_overlap=50, embedding_dimensions=2048,
    )
    pipeline = LazyGraphRAGIndexingPipeline(
        neo4j_store=neo4j_store,
        llm=llm_service.get_indexing_llm(),
        embedder=None,
        config=config,
    )

    # Filter to content sentences (excluding structured)
    content_sentences = [
        s for s in raw_sentences
        if pipeline._classify_sentence(s) == "content"
        and s.get("source") not in ("signature_party", "letterhead")
    ]
    print(f"Content sentences (LLM path): {len(content_sentences)}")

    # Build section batches (same for both prompts)
    batches = build_section_batches(pipeline, content_sentences)
    print(f"Section batches: {len(batches)}")
    for i, (batch, ctx) in enumerate(batches):
        has_critical = any(s["id"] in CRITICAL_SENTENCE_IDS for s in batch)
        marker = " ★" if has_critical else ""
        print(f"  Batch {i+1}: {len(batch)} sentences, ctx='{ctx[:40]}'{marker}")

    # Run both prompts
    print("\n" + "="*60)
    print("Running CURRENT prompt on section batches...")
    t0 = time.time()
    current_result = await run_prompt_test(
        pipeline.llm, batches, CURRENT_PROMPT, "CURRENT"
    )
    print(f"  Done in {time.time()-t0:.1f}s")

    print("\nRunning IMPROVED prompt on section batches...")
    t0 = time.time()
    improved_result = await run_prompt_test(
        pipeline.llm, batches, IMPROVED_PROMPT, "IMPROVED"
    )
    print(f"  Done in {time.time()-t0:.1f}s")

    # Analyse both
    analyse(current_result, "CURRENT PROMPT (section batching)")
    analyse(improved_result, "IMPROVED PROMPT (section batching)")

    # Direct comparison
    cur_ents = set(current_result["entities"])
    imp_ents = set(improved_result["entities"])
    only_improved = imp_ents - cur_ents
    only_current = cur_ents - imp_ents

    print(f"\n{'='*60}")
    print(f"  COMPARISON")
    print(f"{'='*60}")
    print(f"  Entities only in IMPROVED ({len(only_improved)}):")
    for e in sorted(only_improved):
        marker = " ★" if any(exp in e or e in exp for exp in EXPECTED_ENTITIES) else ""
        print(f"    {e}{marker}")
    print(f"\n  Entities only in CURRENT ({len(only_current)}):")
    for e in sorted(only_current):
        marker = " ★" if any(exp in e or e in exp for exp in EXPECTED_ENTITIES) else ""
        print(f"    {e}{marker}")

    # Save results
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    outpath = f"experiment_prompt_fix_{ts}.json"
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": ts,
            "current": {
                "total_triples": current_result["total_triples"],
                "unique_entities": current_result["unique_entities"],
                "entities": current_result["entities"],
                "critical_triples": current_result["critical_triples"],
                "long_predicates_50": len([p for p in current_result["predicates"] if len(p) > 50]),
            },
            "improved": {
                "total_triples": improved_result["total_triples"],
                "unique_entities": improved_result["unique_entities"],
                "entities": improved_result["entities"],
                "critical_triples": improved_result["critical_triples"],
                "long_predicates_50": len([p for p in improved_result["predicates"] if len(p) > 50]),
            },
        }, f, indent=2)
    print(f"\nResults saved to {outpath}")

    neo4j_store.close()


if __name__ == "__main__":
    asyncio.run(main())
