#!/usr/bin/env python3
"""Diagnostic: trace Q-D3 through every stage of the triple funnel.

Shows exactly which triples survive/die at each stage:
  Stage 0: ALL triples in the graph (with cosine score)
  Stage 1: Instructed cosine top-50
  Stage 1b: Baseline (non-instructed) cosine top-50 for comparison
  Stage 2: Voyage rerank-2.5 top-15
  Stage 3: LLM recognition memory filter
"""

import asyncio
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("LOG_LEVEL", "WARNING")

from dotenv import load_dotenv
load_dotenv()

QUERY = 'Compare "time windows" across the set: list all explicit day-based timeframes.'
GROUP_ID = os.getenv("DIAG_GROUP_ID", "test-5pdfs-v2-fix2")

# Target triples we're tracking (substrings to match in triple_text)
TARGETS = [
    "180",          # 180-day rental threshold / arbitration
    "3 business",   # 3 business days cancel window
    "10 business",  # 10 business days holding tank
    "60 day",       # 60-day warranty
    "90 day",       # 90 days labor
    "five (5)",     # 5 business days
    "5 business",   # 5 business days
    "one (1) year", # 1-year warranty
    "twelve (12)",  # 12 months
    "termina",      # termination notice
]


def is_target(triple_text: str) -> bool:
    t = triple_text.lower()
    return any(tgt.lower() in t for tgt in TARGETS)


def fmt(triple_text: str, score: float, rank: int) -> str:
    marker = " <<<< TARGET" if is_target(triple_text) else ""
    return f"  [{rank:3d}] {score:.4f}  {triple_text[:100]}{marker}"


async def main():
    import voyageai
    from neo4j import GraphDatabase
    from src.core.config import settings
    from src.worker.hybrid_v2.retrievers.triple_store import TripleEmbeddingStore
    from src.worker.hybrid_v2.embeddings.voyage_embed import get_voyage_embed_service

    vc = voyageai.Client(api_key=settings.VOYAGE_API_KEY)
    neo4j_driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    )
    voyage_svc = get_voyage_embed_service()

    # ---- Load triples ----
    print(f"Loading triples for group_id={GROUP_ID} ...")
    store = TripleEmbeddingStore()
    await store.load(neo4j_driver, GROUP_ID, voyage_svc)
    total = len(store._triples)
    print(f"  Total triples: {total}")

    # ---- Stage 0: Baseline cosine (no instruction) ----
    print("\n=== STAGE 0: Baseline cosine (ALL triples ranked) ===")
    t0 = time.perf_counter()
    baseline_result = vc.contextualized_embed(
        inputs=[[QUERY]], model=settings.VOYAGE_MODEL_NAME,
        input_type="query", output_dimension=settings.VOYAGE_EMBEDDING_DIM,
    )
    baseline_emb = np.array(baseline_result.results[0].embeddings[0], dtype=np.float32)
    baseline_emb /= np.linalg.norm(baseline_emb)
    baseline_scores = store._embeddings_matrix @ baseline_emb
    baseline_order = np.argsort(baseline_scores)[::-1]
    dt0 = time.perf_counter() - t0
    print(f"  Embed + search: {dt0*1000:.0f}ms")

    print("\n  Top-20 (baseline):")
    for rank, idx in enumerate(baseline_order[:20], 1):
        print(fmt(store._triples[idx].triple_text, float(baseline_scores[idx]), rank))

    print("\n  Target triples (baseline rank):")
    for idx in baseline_order:
        rank = int(np.where(baseline_order == idx)[0][0]) + 1
        if is_target(store._triples[idx].triple_text):
            print(fmt(store._triples[idx].triple_text, float(baseline_scores[idx]), rank))

    # ---- Stage 1: Instructed cosine ----
    instruction = os.getenv(
        "ROUTE7_TRIPLE_SEARCH_INSTRUCTION",
        "Identify every fact mentioning a numeric time period, duration, "
        "fee, obligation, condition, or named entity relevant to this query. "
        "Query: ",
    ).strip()
    instructed_text = f"{instruction}{QUERY}"
    print(f"\n=== STAGE 1: Instructed cosine (ALL triples ranked) ===")
    print(f"  Instruction: {instruction[:80]}...")
    t1 = time.perf_counter()
    instr_result = vc.contextualized_embed(
        inputs=[[instructed_text]], model=settings.VOYAGE_MODEL_NAME,
        input_type="query", output_dimension=settings.VOYAGE_EMBEDDING_DIM,
    )
    instr_emb = np.array(instr_result.results[0].embeddings[0], dtype=np.float32)
    instr_emb /= np.linalg.norm(instr_emb)
    instr_scores = store._embeddings_matrix @ instr_emb
    instr_order = np.argsort(instr_scores)[::-1]
    dt1 = time.perf_counter() - t1
    print(f"  Embed + search: {dt1*1000:.0f}ms")

    print("\n  Top-20 (instructed):")
    for rank, idx in enumerate(instr_order[:20], 1):
        print(fmt(store._triples[idx].triple_text, float(instr_scores[idx]), rank))

    print("\n  Target triples (instructed rank):")
    for idx in instr_order:
        rank = int(np.where(instr_order == idx)[0][0]) + 1
        if is_target(store._triples[idx].triple_text):
            print(fmt(store._triples[idx].triple_text, float(instr_scores[idx]), rank))

    # ---- Stage 1 cutoff: top-50 ----
    CANDIDATES_K = int(os.getenv("ROUTE7_TRIPLE_CANDIDATES_K", "50"))
    top50_indices = instr_order[:CANDIDATES_K]
    top50_triples = [(store._triples[i], float(instr_scores[i])) for i in top50_indices]

    print(f"\n=== STAGE 1 → STAGE 2 HANDOFF: top-{CANDIDATES_K} cutoff ===")
    targets_in = [(t, s) for t, s in top50_triples if is_target(t.triple_text)]
    targets_out = []
    for idx in instr_order[CANDIDATES_K:]:
        if is_target(store._triples[idx].triple_text):
            rank = int(np.where(instr_order == idx)[0][0]) + 1
            targets_out.append((store._triples[idx], float(instr_scores[idx]), rank))

    print(f"  Targets IN top-{CANDIDATES_K}: {len(targets_in)}")
    for t, s in targets_in:
        rank = int(np.where(instr_order == [i for i, tr in enumerate(store._triples) if tr is t][0])[0][0]) + 1
        print(f"    [{rank:3d}] {s:.4f}  {t.triple_text[:100]}")
    print(f"  Targets DROPPED by cutoff: {len(targets_out)}")
    for t, s, rank in targets_out:
        print(f"    [{rank:3d}] {s:.4f}  {t.triple_text[:100]}  *** LOST HERE ***")

    # ---- Stage 2: Reranker ----
    TRIPLE_TOP_K = int(os.getenv("ROUTE7_TRIPLE_TOP_K", "15"))
    print(f"\n=== STAGE 2: Voyage rerank-2.5 (top-{CANDIDATES_K} → top-{TRIPLE_TOP_K}) ===")

    rerank_model = os.getenv("ROUTE7_RERANK_MODEL", "rerank-2.5")
    documents = [t.triple_text for t, _ in top50_triples]
    instructed_query = (
        "Identify facts relevant to answering this query. "
        "Consider abstract category membership — e.g., specific durations "
        "like '3 business days' or '90 days' are relevant to 'timeframes'. "
        f"Query: {QUERY}"
    )
    t2 = time.perf_counter()
    rr = vc.rerank(
        query=instructed_query, documents=documents,
        model=rerank_model, top_k=min(TRIPLE_TOP_K, len(documents)),
    )
    dt2 = time.perf_counter() - t2
    print(f"  Rerank latency: {dt2*1000:.0f}ms")

    reranked = [(top50_triples[r.index][0], r.relevance_score) for r in rr.results]
    print(f"\n  Top-{TRIPLE_TOP_K} after reranking:")
    for rank, (t, s) in enumerate(reranked, 1):
        print(fmt(t.triple_text, s, rank))

    targets_after_rerank = [(t, s) for t, s in reranked if is_target(t.triple_text)]
    print(f"\n  Targets surviving rerank: {len(targets_after_rerank)}")

    # Show full rerank scores for all 50 (to see where targets land)
    print(f"\n  Full rerank scores for all {len(documents)} candidates:")
    rr_full = vc.rerank(
        query=instructed_query, documents=documents,
        model=rerank_model, top_k=len(documents),
    )
    for rank, r in enumerate(rr_full.results, 1):
        t_obj = top50_triples[r.index][0]
        print(fmt(t_obj.triple_text, r.relevance_score, rank))

    print("\n=== SUMMARY ===")
    print(f"  Total triples in graph: {total}")
    print(f"  Baseline cosine → targets in top-50: "
          f"{sum(1 for i in baseline_order[:50] if is_target(store._triples[i].triple_text))}")
    print(f"  Instructed cosine → targets in top-50: {len(targets_in)}")
    print(f"  Reranker → targets in top-{TRIPLE_TOP_K}: {len(targets_after_rerank)}")
    print(f"  Targets dropped at cosine cutoff: {len(targets_out)}")

if __name__ == "__main__":
    asyncio.run(main())
