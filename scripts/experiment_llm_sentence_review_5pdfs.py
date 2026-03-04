#!/usr/bin/env python3
"""4-way sentence splitting comparison on real 5-PDF corpus.

Compares: spaCy, spaCy+LLM, wtpsplit, wtpsplit+LLM
on actual text extracted from the 5 Microsoft test PDFs (via Neo4j).

Usage:
    # Quick: pull text from Neo4j, run all 4 approaches
    python scripts/experiment_llm_sentence_review_5pdfs.py

    # Specify model for LLM review
    python scripts/experiment_llm_sentence_review_5pdfs.py --model gpt-4.1

    # Use cached text (skip Neo4j fetch)
    python scripts/experiment_llm_sentence_review_5pdfs.py --cached
"""

import argparse
import json
import os
import re
import sys
import time
import threading
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GROUP_ID = os.getenv("TEST_GROUP_ID", "test-5pdfs-v2-fix2")
CACHE_FILE = Path(__file__).parent.parent / "experiment_5pdf_text_cache.json"

# ---------------------------------------------------------------------------
# spaCy setup (with legal abbreviation fix from the handover)
# ---------------------------------------------------------------------------
_nlp = None
_nlp_lock = threading.Lock()

LEGAL_ABBREVS = {
    'art', 'para', 'sec', 'cl', 'ref', 'no', 'inc', 'ltd', 'corp', 'co',
    'sr', 'jr', 'dr', 'mr', 'mrs', 'ms', 'prof', 'esq', 'dept', 'div',
    'approx', 'est', 'govt', 'intl', 'natl', 'supp', 'vol', 'pt', 'st',
    'subch', 'ch', 'app', 'exh', 'amdt', 'reg', 'par', 'chap',
}


def _get_nlp():
    """Lazy-load spaCy with legal abbreviation fix v2."""
    global _nlp
    if _nlp is not None:
        return _nlp
    with _nlp_lock:
        if _nlp is None:
            import spacy
            from spacy.language import Language

            @Language.component("legal_sent_boundary_fix_v2")
            def legal_sent_boundary_fix_v2(doc):
                for token in doc[:-1]:
                    if (token.text.endswith(".") and len(token.text) > 1 and
                            token.text[:-1].lower() in LEGAL_ABBREVS):
                        doc[token.i + 1].is_sent_start = False
                    elif (token.text == "." and token.i > 0 and
                          doc[token.i - 1].text.lower() in LEGAL_ABBREVS and
                          token.i + 1 < len(doc)):
                        doc[token.i + 1].is_sent_start = False
                return doc

            _nlp = spacy.load("en_core_web_sm")
            _nlp.add_pipe("legal_sent_boundary_fix_v2", before="parser")
            _nlp.max_length = 50_000
            print("  [spaCy loaded: en_core_web_sm + legal_fix_v2]")
    return _nlp


def spacy_split(text: str) -> List[str]:
    """Split text using spaCy + legal abbreviation fix v2."""
    nlp = _get_nlp()
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


# ---------------------------------------------------------------------------
# wtpsplit setup
# ---------------------------------------------------------------------------
def wtpsplit_split(text: str) -> List[str]:
    """Split text using wtpsplit sat-3l-sm."""
    from src.worker.services.sentence_extraction_service import _split_sentences
    return _split_sentences(text)


def wtpsplit_llm_split(text: str) -> List[str]:
    """Split text using wtpsplit + bundled LLM review (single section)."""
    from src.worker.services.sentence_extraction_service import (
        llm_review_sections_bundled,
    )
    sentences = wtpsplit_split(text)
    if not sentences:
        return sentences
    reviewed = llm_review_sections_bundled([("sec0", sentences)])
    return reviewed.get("sec0", sentences)


# ---------------------------------------------------------------------------
# Full LLM review (send ALL boundaries — now the only mode)
# ---------------------------------------------------------------------------
def spacy_llm_full_split(text: str) -> List[str]:
    """Split text using spaCy, then send ALL boundaries to LLM."""
    from src.worker.services.sentence_extraction_service import (
        llm_review_sections_bundled,
    )
    sentences = spacy_split(text)
    if not sentences:
        return sentences
    reviewed = llm_review_sections_bundled([("sec0", sentences)])
    return reviewed.get("sec0", sentences)


def wtpsplit_llm_full_split(text: str) -> List[str]:
    """Split text using wtpsplit, then send ALL boundaries to LLM."""
    return wtpsplit_llm_split(text)  # same as bundled review


# ---------------------------------------------------------------------------
# spaCy + LLM review (bundled, replaces selective)
# ---------------------------------------------------------------------------
def spacy_llm_split(text: str) -> List[str]:
    """Split text using spaCy + legal fix, then LLM review."""
    return spacy_llm_full_split(text)  # uses bundled full review


# ---------------------------------------------------------------------------
# Text preprocessing (same as production pipeline)
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Same preprocessing as _clean_chunk_text_for_spacy in production."""
    from src.worker.services.sentence_extraction_service import _clean_chunk_text_for_spacy
    return _clean_chunk_text_for_spacy(text)


# ---------------------------------------------------------------------------
# Neo4j text fetcher
# ---------------------------------------------------------------------------
def fetch_texts_from_neo4j(group_id: str) -> list:
    """Fetch original paragraph text (parent_text) from Sentence nodes."""
    from src.core.config import settings
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    )
    texts = []
    with driver.session(database=settings.NEO4J_DATABASE or "neo4j") as session:
        # Get doc titles
        doc_map = {}
        result = session.run(
            "MATCH (d:Document {group_id: $gid}) RETURN d.document_id AS did, d.title AS t",
            gid=group_id,
        )
        for r in result:
            doc_map[r["did"]] = r["t"]
        print(f"  Found {len(doc_map)} documents in group '{group_id}'")

        # Get unique parent_text paragraphs grouped by (parent_text, document_id)
        result = session.run(
            """
            MATCH (sent:Sentence {group_id: $gid})
            WHERE sent.parent_text IS NOT NULL AND sent.source = "paragraph"
            WITH sent.parent_text AS parent_text, sent.document_id AS doc_id,
                 sent.section_path AS section_path, sent.chunk_id AS chunk_id,
                 collect(sent.text) AS sentence_texts
            RETURN parent_text, doc_id, section_path, chunk_id,
                   size(sentence_texts) AS sent_count
            ORDER BY doc_id, section_path
            """,
            gid=group_id,
        )
        for r in result:
            pt = r["parent_text"].strip()
            if pt.startswith("."):
                pt = pt[1:].strip()
            if len(pt) > 50:
                texts.append({
                    "doc_title": doc_map.get(r["doc_id"], r["doc_id"] or "unknown"),
                    "section_path": r["section_path"],
                    "chunk_id": r["chunk_id"] or "",
                    "text": pt,
                    "neo4j_sent_count": r["sent_count"],
                })

    driver.close()
    total_sents = sum(t.get("neo4j_sent_count", 0) for t in texts)
    print(f"  Fetched {len(texts)} paragraphs ({total_sents} Neo4j sentences)")
    return texts


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------
def compare_splitters(texts: list, model: str) -> dict:
    """Run all 4 splitters on each text and compare."""
    os.environ.setdefault("SENTENCE_REVIEW_MODEL", model)
    os.environ.setdefault("SENTENCE_REVIEW_DEPLOYMENT", model)

    results = []
    totals = {"spacy": 0, "spacy_llm": 0, "spacy_llm_full": 0,
              "wtpsplit": 0, "wtpsplit_llm": 0, "wtpsplit_llm_full": 0}
    llm_changes = {"spacy_llm": 0, "spacy_llm_full": 0,
                   "wtpsplit_llm": 0, "wtpsplit_llm_full": 0}
    timings = {"spacy": 0, "spacy_llm": 0, "spacy_llm_full": 0,
               "wtpsplit": 0, "wtpsplit_llm": 0, "wtpsplit_llm_full": 0}

    for i, item in enumerate(texts):
        text = item["text"]
        doc_title = item["doc_title"]

        # 1. spaCy
        t0 = time.time()
        sp = spacy_split(text)
        timings["spacy"] += time.time() - t0

        # 2. wtpsplit
        t0 = time.time()
        wt = wtpsplit_split(text)
        timings["wtpsplit"] += time.time() - t0

        # 3. spaCy + LLM (selective)
        t0 = time.time()
        sp_llm = spacy_llm_split(text)
        timings["spacy_llm"] += time.time() - t0

        # 4. wtpsplit + LLM (selective)
        t0 = time.time()
        wt_llm = wtpsplit_llm_split(text)
        timings["wtpsplit_llm"] += time.time() - t0

        # 5. spaCy + LLM (full — all boundaries)
        t0 = time.time()
        sp_llm_full = spacy_llm_full_split(text)
        timings["spacy_llm_full"] += time.time() - t0

        # 6. wtpsplit + LLM (full — all boundaries)
        t0 = time.time()
        wt_llm_full = wtpsplit_llm_full_split(text)
        timings["wtpsplit_llm_full"] += time.time() - t0

        sp_changed = sp != sp_llm
        wt_changed = wt != wt_llm
        sp_full_changed = sp != sp_llm_full
        wt_full_changed = wt != wt_llm_full
        if sp_changed:
            llm_changes["spacy_llm"] += 1
        if wt_changed:
            llm_changes["wtpsplit_llm"] += 1
        if sp_full_changed:
            llm_changes["spacy_llm_full"] += 1
        if wt_full_changed:
            llm_changes["wtpsplit_llm_full"] += 1

        totals["spacy"] += len(sp)
        totals["spacy_llm"] += len(sp_llm)
        totals["spacy_llm_full"] += len(sp_llm_full)
        totals["wtpsplit"] += len(wt)
        totals["wtpsplit_llm"] += len(wt_llm)
        totals["wtpsplit_llm_full"] += len(wt_llm_full)

        entry = {
            "chunk_id": item["chunk_id"],
            "doc_title": doc_title,
            "text_len": len(text),
            "neo4j_sent_count": item.get("neo4j_sent_count", 0),
            "spacy_count": len(sp),
            "spacy_llm_count": len(sp_llm),
            "spacy_llm_full_count": len(sp_llm_full),
            "wtpsplit_count": len(wt),
            "wtpsplit_llm_count": len(wt_llm),
            "wtpsplit_llm_full_count": len(wt_llm_full),
            "spacy_changed_by_llm": sp_changed,
            "spacy_changed_by_llm_full": sp_full_changed,
            "wtpsplit_changed_by_llm": wt_changed,
            "wtpsplit_changed_by_llm_full": wt_full_changed,
        }

        # Show diffs where full LLM changed something
        if sp_full_changed or wt_full_changed:
            entry["diffs"] = {}
            if sp_full_changed:
                entry["diffs"]["spacy_full"] = {
                    "before": sp,
                    "after": sp_llm_full,
                }
            if wt_full_changed:
                entry["diffs"]["wtpsplit_full"] = {
                    "before": wt,
                    "after": wt_llm_full,
                }

        results.append(entry)
        # Progress
        any_change = sp_full_changed or wt_full_changed
        print(f"  [{i+1}/{len(texts)}] {doc_title[:40]:40s}  "
              f"spaCy:{len(sp):3d}→{len(sp_llm_full):3d}  "
              f"wtp:{len(wt):3d}→{len(wt_llm_full):3d}"
              f"{'  ★' if any_change else ''}")

    return {
        "model": model,
        "group_id": GROUP_ID,
        "num_chunks": len(texts),
        "totals": totals,
        "llm_changes": llm_changes,
        "timings_s": {k: round(v, 2) for k, v in timings.items()},
        "results": results,
    }


# ---------------------------------------------------------------------------
# Pretty print summary
# ---------------------------------------------------------------------------
def print_summary(data: dict):
    t = data["totals"]
    lc = data["llm_changes"]
    tm = data["timings_s"]
    n = data["num_chunks"]

    print("\n" + "=" * 70)
    print(f"SUMMARY: {n} chunks from {data['group_id']} (LLM: {data['model']})")
    print("=" * 70)

    print(f"\n{'Method':<20} {'Sentences':>10} {'Time (s)':>10} {'LLM changes':>12}")
    print("-" * 55)
    neo4j_total = sum(r.get("neo4j_sent_count", 0) for r in data["results"])
    if neo4j_total:
        print(f"{'Neo4j baseline':<20} {neo4j_total:>10} {'—':>10} {'—':>12}")
    print(f"{'spaCy+legal_fix':<20} {t['spacy']:>10} {tm['spacy']:>10.1f} {'—':>12}")
    print(f"{'spaCy+LLM(sel)':<20} {t['spacy_llm']:>10} {tm['spacy_llm']:>10.1f} {lc['spacy_llm']:>12}")
    print(f"{'spaCy+LLM(full)':<20} {t['spacy_llm_full']:>10} {tm['spacy_llm_full']:>10.1f} {lc['spacy_llm_full']:>12}")
    print(f"{'wtpsplit':<20} {t['wtpsplit']:>10} {tm['wtpsplit']:>10.1f} {'—':>12}")
    print(f"{'wtpsplit+LLM(sel)':<20} {t['wtpsplit_llm']:>10} {tm['wtpsplit_llm']:>10.1f} {lc['wtpsplit_llm']:>12}")
    print(f"{'wtpsplit+LLM(full)':<20} {t['wtpsplit_llm_full']:>10} {tm['wtpsplit_llm_full']:>10.1f} {lc['wtpsplit_llm_full']:>12}")

    # Per-document breakdown
    print(f"\n{'Document':<35} {'Neo4j':>5} {'spaCy':>5} {'sp+LLM':>6} {'sp+Full':>7} {'wtp':>4} {'wt+LLM':>6} {'wt+Full':>7}")
    print("-" * 78)
    doc_totals = {}
    for r in data["results"]:
        dt = r["doc_title"]
        if dt not in doc_totals:
            doc_totals[dt] = {"neo4j": 0, "spacy": 0, "spacy_llm": 0, "spacy_llm_full": 0,
                              "wtpsplit": 0, "wtpsplit_llm": 0, "wtpsplit_llm_full": 0}
        doc_totals[dt]["neo4j"] += r.get("neo4j_sent_count", 0)
        doc_totals[dt]["spacy"] += r["spacy_count"]
        doc_totals[dt]["spacy_llm"] += r["spacy_llm_count"]
        doc_totals[dt]["spacy_llm_full"] += r.get("spacy_llm_full_count", r["spacy_llm_count"])
        doc_totals[dt]["wtpsplit"] += r["wtpsplit_count"]
        doc_totals[dt]["wtpsplit_llm"] += r["wtpsplit_llm_count"]
        doc_totals[dt]["wtpsplit_llm_full"] += r.get("wtpsplit_llm_full_count", r["wtpsplit_llm_count"])
    for dt, tots in sorted(doc_totals.items()):
        label = dt[:33]
        print(f"  {label:<33} {tots['neo4j']:>5} {tots['spacy']:>5} {tots['spacy_llm']:>6} "
              f"{tots['spacy_llm_full']:>7} {tots['wtpsplit']:>4} {tots['wtpsplit_llm']:>6} "
              f"{tots['wtpsplit_llm_full']:>7}")

    # Show all diffs
    diffs = [r for r in data["results"] if r.get("diffs")]
    if diffs:
        print(f"\n{'=' * 70}")
        print(f"LLM CHANGES DETAIL ({len(diffs)} chunks modified)")
        print("=" * 70)
        for r in diffs:
            print(f"\n--- {r['doc_title']} / {r['chunk_id']} ---")
            for method, diff in r["diffs"].items():
                print(f"  [{method}]")
                bef = diff["before"]
                aft = diff["after"]
                # Find what changed
                if len(bef) > len(aft):
                    print(f"    MERGED: {len(bef)} → {len(aft)} segments")
                elif len(bef) < len(aft):
                    print(f"    SPLIT: {len(bef)} → {len(aft)} segments")
                else:
                    print(f"    RESHUFFLED: {len(bef)} segments (boundaries moved)")
                # Show before/after for segments that differ
                max_show = max(len(bef), len(aft))
                for j in range(min(max_show, 8)):
                    b = bef[j] if j < len(bef) else "—"
                    a = aft[j] if j < len(aft) else "—"
                    if b != a:
                        if len(b) > 80:
                            b = b[:77] + "..."
                        if len(a) > 80:
                            a = a[:77] + "..."
                        print(f"      before[{j}]: {b}")
                        print(f"       after[{j}]: {a}")
    else:
        print("\n  No LLM changes detected.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="4-way sentence splitting comparison on 5 PDFs")
    parser.add_argument("--model", default="gpt-4.1", help="Azure OpenAI model for LLM review")
    parser.add_argument("--cached", action="store_true", help="Use cached text (skip Neo4j)")
    parser.add_argument("--group-id", default=None, help="Neo4j group_id override")
    args = parser.parse_args()

    global GROUP_ID
    if args.group_id:
        GROUP_ID = args.group_id

    # Fetch or load text
    if args.cached and CACHE_FILE.exists():
        print(f"Loading cached text from {CACHE_FILE}")
        with open(CACHE_FILE) as f:
            texts = json.load(f)
    else:
        print(f"Fetching text from Neo4j (group_id={GROUP_ID})...")
        texts = fetch_texts_from_neo4j(GROUP_ID)
        with open(CACHE_FILE, "w") as f:
            json.dump(texts, f, indent=2)
        print(f"  Cached to {CACHE_FILE}")

    print(f"\nRunning 4-way comparison on {len(texts)} chunks (LLM model: {args.model})...")
    data = compare_splitters(texts, args.model)

    # Save results
    ts = int(time.time())
    outfile = Path(__file__).parent.parent / f"experiment_llm_sentence_review_{ts}.json"
    with open(outfile, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to: {outfile}")

    print_summary(data)


if __name__ == "__main__":
    main()
